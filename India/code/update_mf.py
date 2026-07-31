from helpers.mf_entry import get_mf_entries, write_entries, get_path_to_csv
from helpers.mf_amfi import get_all_schemes, check_amfi_entry_complete, get_details_amfi
from helpers.mf_kuvera import Kuvera
from helpers.mf_ms import update_ms_details
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import subprocess
import io
import csv


def review_data_changes(original_data, updated_data, phase):
    """Interactively review per-field changes and new entries before writing."""
    if not isinstance(original_data, dict) or not isinstance(updated_data, dict):
        return updated_data

    reviewed_data = {}
    for code in sorted(set(original_data.keys()) | set(updated_data.keys())):
        original_entry = original_data.get(code, {}) or {}
        updated_entry = updated_data.get(code, {}) or {}

        if code not in original_data:
            print(f'\nNew entry: {code}')
            for field in sorted(updated_entry.keys()):
                value = updated_entry.get(field, '')
                print(f'- {field}: {value}')
            choice = input('Looks good? [Y/n]: ').strip().lower()
            if choice in {'', 'y', 'yes'}:
                reviewed_data[code] = updated_entry
            else:
                print(f'Skipping new entry {code}')
            continue

        if code not in updated_data:
            reviewed_data[code] = original_entry
            continue

        reviewed_entry = dict(original_entry)
        changed_fields = []
        for field in sorted(set(original_entry.keys()) | set(updated_entry.keys())):
            old_value = original_entry.get(field, '')
            new_value = updated_entry.get(field, '')
            if (old_value or '') != (new_value or ''):
                changed_fields.append(field)
                print(f'\nEntry {code}: field {field}')
                print(f'  old: {old_value}')
                print(f'  new: {new_value}')
                choice = input('Accept this change? [Y/n]: ').strip().lower()
                if choice in {'', 'y', 'yes'}:
                    reviewed_entry[field] = new_value
                else:
                    reviewed_entry[field] = old_value
                    print(f'Reverted field {field} for {code}')

        if changed_fields:
            print(f'\nReview summary for entry {code}:')
            for field in changed_fields:
                print(f'- {field}: {reviewed_entry.get(field, "")}')
            entry_choice = input('Does this entry look good overall? [Y/n]: ').strip().lower()
            if entry_choice not in {'', 'y', 'yes'}:
                reviewed_entry = dict(original_entry)
                print(f'Rejected whole entry {code}')

        reviewed_data[code] = reviewed_entry

    if phase:
        write_entries(reviewed_data, phase)
    return reviewed_data


def get_amfi():
    # Step 1: Get the current data from CSV and the latest schemes from AMFI, merge them to add any missing entries, and write back to CSV
    current_data = get_mf_entries()
    amfi_schemes = get_all_schemes()
    needs_write = False
    fund_house_name_changes = {}
    # merge these two datasets to add any missing entries in current_data
    for code, details in amfi_schemes.items():
        if code not in current_data:
            current_data[code] = details
            needs_write = True
        else:
            previous_fund_house = current_data[code].get('fund_house', '')
            for key, value in details.items():
                if key in current_data[code] and current_data[code][key] != value:
                    current_data[code][key] = value
                    needs_write = True
                    if key == 'fund_house' and previous_fund_house and previous_fund_house != value:
                        has_existing_mapping = any(
                            bool(current_data[code].get(field, ''))
                            for field in ['kuvera_name', 'kuvera_fund_category', 'kuvera_code']
                        )
                        if has_existing_mapping:
                            fund_house_name_changes[previous_fund_house] = value
    if needs_write:
        reset_kuvera_helper = Kuvera.__new__(Kuvera)
        reset_kuvera_helper.reset_fund_house_name_change(current_data, fund_house_name_changes)
        current_data = review_data_changes(get_mf_entries(), current_data, 'getting all amfi schemes')
    return current_data

def populate_amfi(current_data):
    # Step 2: Update details from AMFI
    needs_write = False
    incomplete_entries = {code: details for code, details in current_data.items() 
                         if not check_amfi_entry_complete(details)}
    
    # temp get only 10 entries
    #incomplete_entries = dict(list(incomplete_entries.items())[:10])
    def fetch_and_update(code, details):
        amfi_data = get_details_amfi(code)
        if amfi_data:
            try:
                ret = {
                    'name': amfi_data['name'],
                    'inception_date': amfi_data.get('scheme_start_date', ''),
                    'end_date': amfi_data.get('scheme_end_date', ''),
                    'amfi_fund_type': amfi_data['amfi_fund_type'],
                    'amfi_category': amfi_data['amfi_fund_category']
                }
                if not 'open ended' in amfi_data['fund_house'].lower() and amfi_data['fund_house'] != '':
                    ret['fund_house'] = amfi_data['fund_house']
                return code, ret
            except Exception as e:
                print(f'ERROR: exception processing AMFI data for code {code} {amfi_data}: {e}')
                raise e
        return code, None
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_and_update, code, details): code 
                   for code, details in incomplete_entries.items()}
        
        for future in as_completed(futures):
            code, data = future.result()
            if data:
                for key, value in data.items():
                    current_data[code][key] = value
                needs_write = True
    if needs_write:
        current_data = review_data_changes(get_mf_entries(), current_data, 'populating amfi details')
    return current_data

def populate_kuvera(current_data):
    # Step 3: Update details from Kuvera
    needs_write = False
    kuvera = Kuvera()
    incomplete_entries = {code: details for code, details in current_data.items() 
                         if not Kuvera.check_kuvera_entry_complete(details) and not Kuvera.check_kuvera_skip_entry(details)}
    # temp get only 10 entries
    #incomplete_entries = dict(list(incomplete_entries.items())[:2000])
    def fetch_and_update(code, details):
        #print(f'fetching kuvera details for code {code} details {details}')
        isin = details.get('isin', '')
        if isin == '':
            isin = details.get('isin2', '')
        kuvera_data = kuvera.get_fund_info(details['name'],
                                                 isin, 
                                                 details['amfi_fund_type'], 
                                                 details['amfi_category'], 
                                                 details['fund_house'])
        if kuvera_data:
            try:
                return code,{
                    'kuvera_name': kuvera_data['name'],
                    'kuvera_fund_category': kuvera_data['fund_category'],
                    'kuvera_code': kuvera_data['kuvera_code']
                }
            except Exception as e:
                print(f'ERROR: exception processing Kuvera data for code {code} {kuvera_data}: {e}')
                raise e
        elif 'direct' in details['name'].lower():
            print(f'no kuvera data found for name {details["name"]} and isin {isin}')
        return code, None
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_and_update, code, details): code 
                   for code, details in incomplete_entries.items()}
        
        for future in as_completed(futures):
            code, data = future.result()
            if data:
                for key, value in data.items():
                    current_data[code][key] = value
                needs_write = True
    known_mapping = kuvera.get_known_isin_mapping()
    for code, details in current_data.items():
        if Kuvera.check_kuvera_entry_complete(details):
            continue
        isin = details.get('isin', '')
        if isin == '':
            isin = details.get('isin2', '')
        if isin in known_mapping:
            kuvera_data = known_mapping[isin]
            print(f'found known kuvera mapping for code {code} isin {isin} data {kuvera_data}')
            current_data[code]['kuvera_name'] = kuvera_data['name']
            current_data[code]['kuvera_fund_category'] = kuvera_data['fund_category']
            current_data[code]['kuvera_code'] = kuvera_data['kuvera_code']
            needs_write = True

    if needs_write:
        current_data = review_data_changes(get_mf_entries(), current_data, 'populating kuvera details')
    return current_data

def populate_ms(current_data):
    update_ms_details(current_data)
    return current_data


def diff_with_git_head(csv_file=None):
    """Interactively review differences between the current CSV and git HEAD."""
    if not csv_file:
        csv_file = get_path_to_csv()

    if not os.path.exists(csv_file):
        print(f'CSV not found: {csv_file}')
        return

    try:
        repo_root = subprocess.run(['git', 'rev-parse', '--show-toplevel'], check=True, stdout=subprocess.PIPE, text=True).stdout.strip()
    except subprocess.CalledProcessError:
        print('Not a git repository; cannot compare with HEAD')
        return

    rel_csv = os.path.relpath(csv_file, repo_root)
    try:
        subprocess.run(['git', 'ls-files', '--error-unmatch', rel_csv], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print(f'File {rel_csv} is not tracked in git; cannot compare with HEAD')
        return

    try:
        head_out = subprocess.run(['git', 'show', f'HEAD:{rel_csv}'], check=True, stdout=subprocess.PIPE, text=True).stdout
    except subprocess.CalledProcessError:
        print('Unable to read file from HEAD')
        return

    with open(csv_file, 'r', newline='') as work_f:
        work_text = work_f.read()
    head_text = head_out

    head_lines = head_text.splitlines()
    work_lines = work_text.splitlines()

    print(f'Diff for {rel_csv}')
    print('--- HEAD ---')
    print('\n'.join(head_lines[:20]))
    print('--- WORKTREE ---')
    print('\n'.join(work_lines[:20]))

    if len(head_lines) != len(work_lines):
        print(f'Line count changed: {len(head_lines)} -> {len(work_lines)}')

    head_rows = list(csv.reader(io.StringIO(head_text)))
    work_rows = list(csv.reader(io.StringIO(work_text)))
    if not head_rows or not work_rows:
        print('No rows to review')
        return

    head_header = head_rows[0]
    work_header = work_rows[0]
    if head_header != work_header:
        print('Header changed')
        print(f'  HEAD: {head_header}')
        print(f'  WORK: {work_header}')
        choice = input('Keep header change? [Y/n]: ').strip().lower()
        if choice not in {'', 'y', 'yes'}:
            work_rows[0] = head_header
            work_text = '\n'.join([','.join(row) for row in work_rows]) + '\n'

    head_map = {}
    work_map = {}
    for row in head_rows[1:]:
        if not row:
            continue
        code = row[0]
        head_map[code] = row
    for row in work_rows[1:]:
        if not row:
            continue
        code = row[0]
        work_map[code] = row

    all_codes = sorted(set(head_map.keys()) | set(work_map.keys()))
    for code in all_codes:
        head_row = head_map.get(code)
        work_row = work_map.get(code)
        if head_row is None and work_row is not None:
            print(f'\nNew entry {code}:')
            for field, value in zip(work_header, work_row):
                print(f'  {field}: {value}')
            choice = input('Keep this new entry? [Y/n]: ').strip().lower()
            if choice not in {'', 'y', 'yes'}:
                work_rows = [row for row in work_rows if not (row and row[0] == code)]
                continue
        elif head_row is not None and work_row is None:
            print(f'\nDeleted entry {code}')
            choice = input('Restore this deleted entry? [Y/n]: ').strip().lower()
            if choice in {'', 'y', 'yes'}:
                work_rows.append(head_row)
        elif head_row is not None and work_row is not None:
            print(f'\nEntry {code}:')
            for idx, field in enumerate(head_header):
                old_value = head_row[idx] if idx < len(head_row) else ''
                new_value = work_row[idx] if idx < len(work_row) else ''
                if (old_value or '') != (new_value or ''):
                    print(f'  {field}: {old_value} -> {new_value}')
            if any((head_row[idx] if idx < len(head_row) else '') != (work_row[idx] if idx < len(work_row) else '') for idx in range(len(head_header))):
                choice = input('Keep this entry change? [Y/n]: ').strip().lower()
                if choice not in {'', 'y', 'yes'}:
                    work_map[code] = head_row

    final_rows = [head_header]
    for code in sorted(work_map.keys()):
        final_rows.append(work_map[code])

    work_text = '\n'.join([','.join(row) for row in final_rows]) + '\n'
    with open(csv_file, 'w', newline='') as out_f:
        out_f.write(work_text)
    print(f'Wrote reviewed content back to {csv_file}')


def print_summary_of_changes():
    csv_file = get_path_to_csv()
    # Read working copy
    if not os.path.exists(csv_file):
        print(f'Working CSV not found: {csv_file}')
        return

    with open(csv_file, newline='') as f:
        reader = csv.reader(f)
        try:
            work_header = next(reader)
        except StopIteration:
            print('Working CSV is empty')
            return
        work_rows = list(reader)

    # Determine repo root and relative path
    try:
        repo_root = subprocess.run(['git', 'rev-parse', '--show-toplevel'], check=True, stdout=subprocess.PIPE, text=True).stdout.strip()
    except subprocess.CalledProcessError:
        print('Not a git repository; cannot obtain HEAD version for comparison')
        return

    rel_csv = "../mf.csv"

    # Ensure file is tracked
    try:
        subprocess.run(['git', 'ls-files', '--error-unmatch', rel_csv], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print(f'File {rel_csv} is not tracked in git; cannot compare with HEAD')
        return

    # Read HEAD version from git
    try:
        head_out = subprocess.run(['git', 'show', f'HEAD:{rel_csv}'], check=True, stdout=subprocess.PIPE, text=True).stdout
    except subprocess.CalledProcessError:
        print('Unable to read file from HEAD')
        return

    head_f = io.StringIO(head_out)
    head_reader = csv.reader(head_f)
    try:
        head_header = next(head_reader)
    except StopIteration:
        print('HEAD CSV is empty')
        return
    head_rows = list(head_reader)

    # Build dicts keyed by first column (code)
    def build_map(header, rows):
        fields = header[1:]
        m = {}
        for row in rows:
            if not row:
                continue
            key = row[0]
            values = {}
            for i, field in enumerate(fields, start=1):
                val = ''
                if i < len(row):
                    val = row[i]
                values[field] = val
            m[key] = values
        return fields, m

    work_fields, work_map = build_map(work_header, work_rows)
    head_fields, head_map = build_map(head_header, head_rows)

    # Union of all fields
    all_fields = list(dict.fromkeys(head_fields + work_fields))

    work_keys = set(work_map.keys())
    head_keys = set(head_map.keys())

    added = sorted(work_keys - head_keys)
    removed = sorted(head_keys - work_keys)
    common = sorted(work_keys & head_keys)

    field_change_counts = {f: 0 for f in all_fields}
    field_changed_codes = {f: [] for f in all_fields}
    entries_with_changes = []

    for code in common:
        changed = False
        for field in all_fields:
            v_work = work_map.get(code, {}).get(field, '')
            v_head = head_map.get(code, {}).get(field, '')
            if (v_work or '') != (v_head or ''):
                field_change_counts[field] += 1
                field_changed_codes[field].append(code)
                changed = True
        if changed:
            entries_with_changes.append(code)

    # Print summary
    print(f'CSV comparison for {rel_csv}')
    print(f'Added entries: {len(added)}')
    if added:
        print(', '.join(added))
    print(f'Removed entries: {len(removed)}')
    if removed:
        print(', '.join(removed))
    print(f'Entries changed: {len(entries_with_changes)}')

    print('\nPer-field change counts:')
    for field in all_fields:
        print(f'- {field}: {field_change_counts.get(field,0)}')

    # Optionally show sample codes changed per field
    print('\nSample changed codes per field (up to 10 each):')
    for field in all_fields:
        codes = field_changed_codes.get(field, [])[:10]
        if codes:
            print(f'- {field}: {", ".join(codes)}')

if __name__ == "__main__":
    data = get_amfi()
    #data = populate_amfi(data)
    data = populate_kuvera(data)
    #data = populate_ms(data)
    print_summary_of_changes()



'''
Check the diff of contents in mf.csv with git HEAD.  If there are any changes, you will be prompted to review them and accept or reject each change.
(venv) portfoliomanager-data % python
Python 3.12.4 (v3.12.4:8e8a4baf65, Jun  6 2024, 17:33:18)
[Clang 13.0.0 (clang-1300.0.29.30)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> import sys
>>> sys.path.insert(0, 'India/code')
>>> from update_mf import diff_with_git_head
>>> diff_with_git_head()
'''