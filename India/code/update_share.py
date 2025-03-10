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


def copy_selected_fields(download_dir):
    orig_file_path = os.path.join(str(pathlib.Path(__file__).parent.parent.absolute()), 'nse_bse_eq.json')
    new_file_path = os.path.join(download_dir, 'nse_bse_eq.json')
    # Load the first JSON file into a dictionary
    with open(new_file_path, 'r') as file1:
        dict1 = json.load(file1)

    # Load the second JSON file into a dictionary
    with open(orig_file_path, 'r') as file2:
        dict2 = json.load(file2)

    # Loop through each key in dict1
    for key, value in dict1.items():
        if key in dict2:
            # Check if the 'bse_security_id', 'bse_security_code', and 'nse_symbol' match
            if (dict1[key].get('bse_security_id') == dict2[key].get('bse_security_id') and
                dict1[key].get('bse_security_code') == dict2[key].get('bse_security_code') and
                dict1[key].get('nse_symbol') == dict2[key].get('nse_symbol')):
                
                # Copy 'bse_name', 'status', and 'industry' from dict1 to dict2
                dict2[key]['bse_name'] = value.get('bse_name')
                dict2[key]['status'] = value.get('status')
                dict2[key]['industry'] = value.get('industry')
                if value.get('listing_date','').strip() != '':
                    dict2[key]['listing_date'] = value.get('listing_date')
                if value.get('cap','').strip() != '':
                    dict2[key]['cap'] = value.get('cap')
                if value.get('face_value','').strip() != '':
                    dict2[key]['face_value'] = value.get('face_value')
    # Copy only if NSE info is missing
    for key, value in dict1.items():
        if key in dict2:
            # Check if the 'bse_security_id', 'bse_security_code', and 'nse_symbol' match
            if (dict1[key].get('bse_security_id') == dict2[key].get('bse_security_id') and
                dict1[key].get('bse_security_code') == dict2[key].get('bse_security_code') and
                dict1[key].get('nse_symbol', '') != '' and
                dict2[key].get('nse_symbol', '') == ''):
                dict2[key]['nse_symbol'] = value.get('nse_symbol')
                dict2[key]['listing_date'] = value.get('listing_date')
                dict2[key]['nse_name'] = value.get('nse_name')
                dict2[key]['industry'] = value.get('industry')


    # Write the updated dictionary back to the second JSON file
    with open(orig_file_path, 'w') as file2:
        json.dump(dict2, file2, indent=1)

    print("Selected fields copied successfully.")



if __name__ == "__main__":
    update_nse(download_dir())
    update_bse(download_dir())
    # You could merge whole info or select fields
    # choose this for whole info
    #merge_new_info(download_dir())
    # choose this for select fields
    #copy_selected_fields(download_dir())
    