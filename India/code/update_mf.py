from helpers.mf_entry import get_mf_entries, write_entries, get_path_to_csv
from helpers.mf_amfi import get_all_schemes, check_amfi_entry_complete, get_details_amfi
from helpers.mf_kuvera import Kuvera
from helpers.mf_ms import update_ms_details
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import subprocess
import io
import csv


def get_amfi():
    # Step 1: Get the current data from CSV and the latest schemes from AMFI, merge them to add any missing entries, and write back to CSV
    current_data = get_mf_entries()
    amfi_schemes = get_all_schemes()
    needs_write = False
    # merge these two datasets to add any missing entries in current_data
    for code, details in amfi_schemes.items():
        if code not in current_data:
            current_data[code] = details
            needs_write = True
        else:
            for key, value in details.items():
                if key in current_data[code] and current_data[code][key] != value:
                    current_data[code][key] = value
                    needs_write = True
    if needs_write:
        write_entries(current_data, 'getting all amfi schemes')
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
                return code, {
                    'name': amfi_data['name'],
                    'fund_house': amfi_data['fund_house'],
                    'inception_date': amfi_data.get('scheme_start_date', ''),
                    'end_date': amfi_data.get('scheme_end_date', ''),
                    'amfi_fund_type': amfi_data['amfi_fund_type'],
                    'amfi_category': amfi_data['amfi_fund_category']
                }
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
        write_entries(current_data, 'populating amfi details')
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
        write_entries(current_data, 'populating kuvera details')
    return current_data

def populate_ms(current_data):
    update_ms_details(current_data)
    return current_data


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
    data = populate_amfi(data)
    data = populate_kuvera(data)
    #data = populate_ms(data)
    print_summary_of_changes()
