import os
import pathlib
import json
from helpers.stock_nse import update_nse
from helpers.stock_bse import update_bse


def download_dir():
    # ~/Downloads is a valid path on MAC.  Adjust this according to your OS
    dir = os.path.join(os.path.expanduser('~'), 'Downloads')
    return dir

def check_strings(string1, string2):
    if string1.strip() == string2.strip() and string1.strip() != '':
        return True
    return False

def check_matching_symbols(orig_data, new_data):
    for isin, data in orig_data.items():
        if check_strings(data['bse_security_id'], new_data['bse_security_id']):
            return isin, data
        if new_data['bse_security_id'] != '' and new_data['bse_security_id'] in data['old_bse_security_id']:
            return isin, data
        if check_strings(data['nse_symbol'], new_data['nse_symbol']):
            return isin, data
        if new_data['nse_symbol'] != '' and  new_data['nse_symbol'] in data['old_nse_symbol']:
            return isin, data
    return None, None

def merge_new_info(download_dir):
    orig_file_path = os.path.join(str(pathlib.Path(__file__).parent.parent.absolute()), 'nse_bse_eq.json')
    new_file_path = os.path.join(download_dir, 'nse_bse_eq.json')
    # Load the original JSON file
    with open(orig_file_path, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    # Load the JSON file containing the update
    with open(new_file_path, 'r', encoding='utf-8') as f:
        update_data = json.load(f)
    merged_data = dict()
    
    for isin, data in original_data.items():
        if isin in update_data:
            n_data = update_data[isin]
            merged_data[isin] = data
            for key, value in n_data.items():
                if value.strip() != '':
                    merged_data[isin][key] = value
        else:
            matching_isin, matching_data = check_matching_symbols(merged_data, data)
            if matching_isin:
                merged_data[matching_isin] = data
                for key, value in matching_data.items():
                    if value.strip() != '':
                        merged_data[matching_isin][key] = value
            else:
                print(f'found no matching data {isin} {data}')
    
    for isin, data in update_data.items():
        if isin.startswith("INF"):
            #print(f'ignoring isin {isin} because its a ETF or MF')
            continue
        if isin in merged_data:
            for key, value in data.items():
                if value.strip() != '':
                    merged_data[isin][key] = value  # Replace or add the key-value pair
        else:
            matching_isin, matching_data = check_matching_symbols(merged_data, data)
            if not matching_isin:
                merged_data[isin] = data
            else:
                print(f'found matching data {matching_isin} {matching_data} {isin} {data}')
    # Write the updated JSON back to the output file while maintaining order
    with open(orig_file_path, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, indent=1, ensure_ascii=False)

    print(f"Updated JSON has been saved to {orig_file_path}")



if __name__ == "__main__":
    update_nse(download_dir())
    update_bse(download_dir())
    merge_new_info(download_dir())
    