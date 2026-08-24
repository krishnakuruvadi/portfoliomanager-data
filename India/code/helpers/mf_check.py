from .mf_entry import get_mf_entries, get_new_entry, write_entries, get_path_to_csv


def update_kuvera_name_in_csv(kuvera_name, csv_file=None):
    """Given a Kuvera fund name, fill in kuvera_name/kuvera_fund_category/kuvera_code
    on its matching AMFI entry in mf.csv, unless that kuvera_name is already present.

    Matches the Kuvera fund to an existing AMFI row via ISIN, since mf.csv rows are
    keyed by AMFI scheme code, not Kuvera code.
    """
    if not csv_file:
        csv_file = get_path_to_csv()

    from helpers.mf_kuvera import Kuvera

    target_name = (kuvera_name or '').strip()
    if not target_name:
        print('kuvera name must not be empty')
        return None

    data = get_mf_entries(csv_file)

    for code, entry in data.items():
        if (entry.get('kuvera_name') or '').strip().lower() == target_name.lower():
            print(f"kuvera name '{kuvera_name}' is already mapped to code {code} ({entry.get('name')})")
            return entry

    probables = Kuvera.find_probable_fund_name(target_name) or []
    match = next((p for p in probables if p.get('name', '').strip().lower() == target_name.lower()), None)
    if not match:
        if probables:
            print(f"no exact kuvera match for '{kuvera_name}'. Closest candidates:")
            for p in probables[:10]:
                print(f"  - {p.get('name')} ({p.get('kuvera_code')})")
        else:
            print(f"no kuvera fund found matching '{kuvera_name}'")
        return None

    scheme_info = Kuvera.get_scheme_info(match['kuvera_code'])
    if not scheme_info or not scheme_info.get('isin'):
        print(f"could not resolve ISIN for kuvera fund '{match['name']}' ({match['kuvera_code']})")
        return None

    isin = scheme_info['isin']
    target_code = None
    for code, entry in data.items():
        if entry.get('isin') == isin or entry.get('isin2') == isin:
            target_code = code
            break

    if not target_code:
        print(f"no AMFI entry in {csv_file} matches ISIN {isin} for kuvera fund '{match['name']}'. "
              "Run update_mf.py to refresh AMFI data first.")
        return None

    entry = data[target_code]
    entry['kuvera_name'] = scheme_info['name']
    entry['kuvera_fund_category'] = scheme_info['fund_category']
    entry['kuvera_code'] = scheme_info['kuvera_code']
    write_entries(data, f"mapping kuvera name '{kuvera_name}' to code {target_code}", csv_file)
    print(f"updated code {target_code} ({entry.get('name')}) with kuvera_name '{entry['kuvera_name']}'")
    return entry


def update_multiple_entries(csv_file=None):
    # find all entries that have fund_house='Bandhan Mutual Fund' and have 'IDFC' in their name
    if not csv_file:
        csv_file = get_path_to_csv()
    data = get_mf_entries(csv_file)
    codes = list()
    for code, entry in data.items():
        if 'index' in entry.get('name', '').lower() and 'direct' in entry.get('name', '').lower() and entry.get('kuvera_name','') == '':
            print(f'Updating code {code} with name {entry.get("name")}')
            codes.append(code)
        if len(codes) > 50:
            break
    if codes:
        update_single_code_in_csv(codes, csv_file)
    else:
        print('No entries found for Bandhan Mutual Fund with IDFC in kuvera_name')

def update_single_code_in_csv(code, csv_file=None):
    """Fetch AMFI and Kuvera data for one or more scheme codes and write it into the MF CSV."""
    if not csv_file:
        csv_file = get_path_to_csv()

    if isinstance(code, (list, tuple, set)):
        codes = [str(item) for item in code]
    else:
        codes = [str(code)]

    data = get_mf_entries(csv_file)

    from helpers.mf_amfi import get_details_amfi
    from helpers.mf_kuvera import Kuvera

    kuvera = Kuvera()

    for code_value in codes:
        if str(code_value) in data:
            entry = data[str(code_value)]
        else:
            entry = get_new_entry()

        amfi_data = get_details_amfi(code_value)
        if amfi_data:
            entry['name'] = amfi_data.get('name', entry.get('name', ''))
            entry['fund_house'] = amfi_data.get('fund_house', entry.get('fund_house', ''))
            entry['inception_date'] = amfi_data.get('scheme_start_date', entry.get('inception_date', ''))
            entry['end_date'] = amfi_data.get('scheme_end_date', entry.get('end_date', ''))
            entry['amfi_fund_type'] = amfi_data.get('amfi_fund_type', entry.get('amfi_fund_type', ''))
            entry['amfi_category'] = amfi_data.get('amfi_fund_category', entry.get('amfi_category', ''))

        current_entry = data.get(str(code_value), entry)
        if current_entry.get('isin', '') == '' and current_entry.get('isin2', '') == '':
            current_entry['isin'] = entry.get('isin', '')
            current_entry['isin2'] = entry.get('isin2', '')

        if entry.get('isin', '') or entry.get('isin2', ''):
            isin = entry.get('isin', '') or entry.get('isin2', '')
            kuvera_data = kuvera.get_fund_info(
                entry.get('name', ''),
                isin,
                entry.get('amfi_fund_type', ''),
                entry.get('amfi_category', ''),
                entry.get('fund_house', '')
            )
            if kuvera_data:
                entry['kuvera_name'] = kuvera_data.get('name', entry.get('kuvera_name', ''))
                entry['kuvera_fund_category'] = kuvera_data.get('fund_category', entry.get('kuvera_fund_category', ''))
                entry['kuvera_code'] = kuvera_data.get('kuvera_code', entry.get('kuvera_code', ''))

        data[str(code_value)] = entry
        write_entries(data, f'updating code {code_value}', csv_file)

    if len(codes) == 1:
        return data[str(codes[0])]
    return {code_value: data[str(code_value)] for code_value in codes}



'''
Given a scheme code, this function will fetch the AMFI and Kuvera data for that scheme and update the mf.csv file accordingly. 
It first checks if the scheme code already exists in the CSV, and if not, it creates a new entry. 
It then fetches the relevant data from AMFI and Kuvera APIs and updates the entry before writing it back to the CSV file.
(venv) portfoliomanager-data % python
Python 3.12.4 (v3.12.4:8e8a4baf65, Jun  6 2024, 17:33:18) [Clang 13.0.0 (clang-1300.0.29.30)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> import sys
>>> sys.path.insert(0, 'India/code')
>>> from helpers.mf_check import *
>>> update_single_code_in_csv('149835')
'''
