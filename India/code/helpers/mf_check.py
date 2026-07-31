from .mf_entry import get_mf_entries, get_new_entry, write_entries, get_path_to_csv


def update_single_code_in_csv(code, csv_file=None):
    """Fetch AMFI and Kuvera data for a single scheme code and write it into the MF CSV."""
    if not csv_file:
        csv_file = get_path_to_csv()

    data = get_mf_entries(csv_file)
    if str(code) in data:
        entry = data[str(code)]
    else:
        entry = get_new_entry()

    from helpers.mf_amfi import get_details_amfi
    from helpers.mf_kuvera import Kuvera

    amfi_data = get_details_amfi(code)
    if amfi_data:
        entry['name'] = amfi_data.get('name', entry.get('name', ''))
        entry['fund_house'] = amfi_data.get('fund_house', entry.get('fund_house', ''))
        entry['inception_date'] = amfi_data.get('scheme_start_date', entry.get('inception_date', ''))
        entry['end_date'] = amfi_data.get('scheme_end_date', entry.get('end_date', ''))
        entry['amfi_fund_type'] = amfi_data.get('amfi_fund_type', entry.get('amfi_fund_type', ''))
        entry['amfi_category'] = amfi_data.get('amfi_fund_category', entry.get('amfi_category', ''))

    current_entry = data.get(str(code), entry)
    if current_entry.get('isin', '') == '' and current_entry.get('isin2', '') == '':
        current_entry['isin'] = entry.get('isin', '')
        current_entry['isin2'] = entry.get('isin2', '')

    kuvera = Kuvera()
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

    data[str(code)] = entry
    write_entries(data, f'updating code {code}', csv_file)
    return data[str(code)]



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