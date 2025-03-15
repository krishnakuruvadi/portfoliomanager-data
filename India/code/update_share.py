import os
import pathlib
import json
from helpers.stock_nse import update_nse
from helpers.stock_bse import update_bse
from datetime import datetime
from rich.console import Console
from rich.table import Table

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
        # we most likely want etf to be tracked here
        #if isin.startswith("INF"):
        #    print(f'ignoring isin {isin} because its a ETF or MF')
        #    continue
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
    merged_file_path = os.path.join(str(pathlib.Path(__file__).parent.parent.absolute()), 'modified_nse_bse_eq.json')

    # Write the updated JSON back to the output file while maintaining order
    with open(merged_file_path, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, indent=1, ensure_ascii=False)

    print(f"Updated JSON has been saved to {merged_file_path}")


def copy_selected_fields():
    orig_file_path = os.path.join(str(pathlib.Path(__file__).parent.parent.absolute()), 'nse_bse_eq.json')
    new_file_path = os.path.join(str(pathlib.Path(__file__).parent.parent.absolute()), 'modified_nse_bse_eq.json')
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
            if (dict1[key].get('bse_security_id') != '' and
                dict1[key].get('bse_security_id') == dict2[key].get('bse_security_id') and
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
    # Copy NSE
    for key, value in dict1.items():
        if key in dict2:
            # Check if the 'bse_security_id', 'bse_security_code', and 'nse_symbol' match
            if (dict1[key].get('bse_security_id') == dict2[key].get('bse_security_id') and
                dict1[key].get('bse_security_code') == dict2[key].get('bse_security_code')):
                # if nse info is missing or if nse symbol is same while info needs updates
                if (dict1[key].get('nse_symbol', '') != '' and
                    dict2[key].get('nse_symbol', '') == ''):
                        dict2[key]['nse_symbol'] = value.get('nse_symbol')
                        dict2[key]['listing_date'] = value.get('listing_date')
                        dict2[key]['nse_name'] = value.get('nse_name')
                        dict2[key]['industry'] = value.get('industry')
                elif (dict1[key].get('nse_symbol', '') != '' and
                    dict2[key].get('nse_symbol', '') == dict1[key].get('nse_symbol')):
                    dict2[key]['listing_date'] = value.get('listing_date')
                    dict2[key]['nse_name'] = value.get('nse_name')
                    dict2[key]['industry'] = value.get('industry')
    # Copy BSE
    for key, value in dict1.items():
        if key in dict2:
            # Check if the 'nse_symbol', 'bse_security_code', and 'nse_symbol' match
            if (dict1[key].get('nse_symbol', '') != '' and
                dict1[key].get('nse_symbol') == dict2[key].get('nse_symbol') and
                dict2[key].get('bse_security_code') == '' and
                dict2[key].get('bse_security_id') == '' and
                dict2[key].get('nse_symbol') == dict1[key].get('bse_security_id')):
                # if bse info is missing while nse symbol matches and is same as new bse security id
                    print(f'right here for isin {key}')
                    print(f'before {dict2[key]}')
                    dict2[key]['bse_security_code'] = value.get('bse_security_code')
                    dict2[key]['bse_security_id'] = value.get('bse_security_id')
                    dict2[key]['bse_name'] = value.get('bse_name')
                    dict2[key]['status'] = value.get('status')
                    print(f'after {dict2[key]}')
    # Write the updated dictionary back to the second JSON file
    with open(orig_file_path, 'w') as file2:
        json.dump(dict2, file2, indent=1)

    print(f"Selected fields copied successfully and written to {orig_file_path}.")

def interactive_mapping():
    orig_file_path = os.path.join(str(pathlib.Path(__file__).parent.parent.absolute()), 'nse_bse_eq.json')
    new_file_path = os.path.join(str(pathlib.Path(__file__).parent.parent.absolute()), 'modified_nse_bse_eq.json')
    # Load the first JSON file into a dictionary
    with open(new_file_path, 'r') as file1:
        new_data = json.load(file1)

    # Load the second JSON file into a dictionary
    with open(orig_file_path, 'r') as file2:
        orig_data = json.load(file2)

    merged_data = dict()
    result = -1
    updated_isins = list()
    # Loop through each key in dict1
    for o_key, o_value in orig_data.items():
        if o_key in updated_isins:
            continue
        if result != 2 and o_key not in new_data:
            unhandled = True
            for nk, nv in new_data.items():
                # Check if the 'bse_security_id', 'bse_security_code', or 'nse_symbol' match
                if ((o_value.get('bse_security_id', '') != '' and
                    o_value.get('bse_security_id') == nv.get('bse_security_id', '')) or
                    (o_value.get('bse_security_code', '') != '' and
                    o_value.get('bse_security_code') == nv.get('bse_security_code', '')) or
                    (o_value.get('nse_symbol', '') != '' and
                    o_value.get('nse_symbol') == nv.get('nse_symbol', ''))):
                    
                    accept_data = print_as_table(nk, nv, o_key, o_value)
                    result = ask_yes_no("Do you want to merge?")
                    if result == 0:
                        merged_data[nk] = accept_data
                        updated_isins.append(nk)
                    else:
                        merged_data[o_key] = o_value
                    unhandled = False
            if unhandled:
                merged_data[o_key] = o_value
        else:
            merged_data[o_key] = o_value
    
    # Write the updated dictionary back to the second JSON file
    with open(orig_file_path, 'w') as file2:
        json.dump(merged_data, file2, indent=1)

    print(f"Merged approved data successfully and written to {orig_file_path}.")

def add_new_data():
    orig_file_path = os.path.join(str(pathlib.Path(__file__).parent.parent.absolute()), 'nse_bse_eq.json')
    new_file_path = os.path.join(str(pathlib.Path(__file__).parent.parent.absolute()), 'modified_nse_bse_eq.json')
    # Load the first JSON file into a dictionary
    with open(new_file_path, 'r') as file1:
        new_data = json.load(file1)

    # Load the second JSON file into a dictionary
    with open(orig_file_path, 'r') as file2:
        orig_data = json.load(file2)
    for nk, nv in new_data.items():
        if nk not in orig_data:
            accept_data = print_as_table(nk, nv, "", dict())
            result = ask_yes_no("Do you want to add?")
            if result == 0:
                orig_data[nk] = accept_data
            elif result == 2:
                break
            
    # Write the updated dictionary back to the second JSON file
    with open(orig_file_path, 'w') as file2:
        json.dump(orig_data, file2, indent=1)

    print(f"Merged approved data successfully and written to {orig_file_path}.")

def print_as_table(new_isin, new_dict, old_isin, old_dict):
    
    merged_item = dict()
    new_item = Item(new_isin, new_dict)
    old_item = Item(old_isin, old_dict)
    merged_item = Item(new_isin, dict())
    
    # isin
    merged_item.isin = new_item.isin
    # bse_security_code
    if new_item.bse_security_code != '':
        if old_item.bse_security_code != '':
            if new_item.bse_security_code != old_item.bse_security_code:
                if old_item.old_bse_security_code != '':
                    merged_item.old_bse_security_code = old_item.old_bse_security_code + ',' + old_item.bse_security_code
        merged_item.bse_security_code = new_item.bse_security_code
    else:
        merged_item.bse_security_code = new_item.bse_security_code
    # bse_security_id
    if new_item.bse_security_id != '':
        if old_item.bse_security_id != '':
            if new_item.bse_security_id != old_item.bse_security_id:
                if old_item.old_bse_security_id != '':
                    merged_item.old_bse_security_id = old_item.old_bse_security_id + ',' + old_item.bse_security_id
                else:
                    merged_item.old_bse_security_id = old_item.bse_security_id
        merged_item.bse_security_id = new_item.bse_security_id            
    else:
        merged_item.bse_security_id = old_item.bse_security_id
    # bse_name
    merged_item.bse_name = new_item.bse_name if new_item.bse_name != '' else old_item.bse_name
    # status
    merged_item.status = new_item.status if new_item.status != '' else old_item.status
    # face_value
    merged_item.face_value = new_item.face_value if new_item.face_value != '' else old_item.face_value
    # industry
    merged_item.industry = new_item.industry if new_item.industry != '' else old_item.industry
    # old_bse_security_code
    merged_item.old_bse_security_code = merged_item.old_bse_security_code if merged_item.old_bse_security_code != '' else old_item.old_bse_security_code
    # old_bse_security_id
    merged_item.old_bse_security_id = merged_item.old_bse_security_id if merged_item.old_bse_security_id != '' else old_item.old_bse_security_id
    # nse_name
    merged_item.nse_name = new_item.nse_name if new_item.nse_name != '' else old_item.nse_name
    # listing_date
    merged_item.listing_date = find_older_date(new_item.listing_date, old_item.listing_date)
    # old_nse_symbol
    merged_item.old_nse_symbol = merged_item.old_nse_symbol if merged_item.old_nse_symbol != '' else old_item.old_nse_symbol
    # nse_symbol
    if new_item.nse_symbol != '':
        if old_item.nse_symbol != '':
            if new_item.nse_symbol != old_item.nse_symbol:
                if old_item.old_nse_symbol != '':
                    merged_item.old_nse_symbol = old_item.old_nse_symbol + ',' + old_item.nse_symbol
                else:
                    merged_item.old_nse_symbol = old_item.nse_symbol
        merged_item.nse_symbol = new_item.nse_symbol            
    else:
        merged_item.nse_symbol = old_item.nse_symbol
    # mc_code
    merged_item.mc_code = new_item.mc_code if new_item.mc_code != '' else old_item.mc_code
    # cap
    merged_item.cap = new_item.cap if new_item.cap != '' else old_item.cap
    # suspension_date
    merged_item.suspension_date = find_newer_date(new_item.suspension_date, old_item.suspension_date)
    table = InfoTable(old_item, new_item, merged_item)
    table.print_table()
    return merged_item.to_json()

class Item:
    def __init__(self, isin, j_dict):
        self.isin = isin
        self.bse_security_code = j_dict.get('bse_security_code', '')
        self.bse_security_id = j_dict.get('bse_security_id', '')
        self.status = j_dict.get('status', '')
        self.bse_name = j_dict.get('bse_name', '')
        self.face_value = j_dict.get('face_value', '')
        self.industry = j_dict.get('industry', '')
        self.old_bse_security_code = j_dict.get('old_bse_security_code', '')
        self.old_bse_security_id = j_dict.get('old_bse_security_id', '')
        self.nse_name = j_dict.get('nse_name', '')
        self.listing_date = j_dict.get('listing_date', '')
        self.old_nse_symbol = j_dict.get('old_nse_symbol', '')
        self.nse_symbol = j_dict.get('nse_symbol', '')
        self.mc_code = j_dict.get('mc_code', '')
        self.cap = j_dict.get('cap', '')
        self.suspension_date = j_dict.get('suspension_date', '')
    
    def to_json(self):
        return {
            'bse_security_code': self.bse_security_code,
            'bse_security_id': self.bse_security_id,
            'bse_name': self.bse_name,
            'status': self.status,
            'face_value': self.face_value,
            'industry': self.industry,
            'old_bse_security_code': self.old_bse_security_code,
            'old_bse_security_id': self.old_bse_security_id,
            'nse_name': self.nse_name,
            'listing_date': self.listing_date,
            'old_nse_symbol': self.old_nse_symbol,
            'nse_symbol': self.nse_symbol,
            'mc_code': self.mc_code,
            'cap': self.cap,
            'suspension_date': self.suspension_date
        }

class InfoTable:
    def __init__(self, old_item, new_item, merged_item):
        self.merged_item = merged_item
        self.old_item = old_item
        self.new_item = new_item
        self.console = Console()
        self.table = Table(show_header=True, header_style="bold magenta")
        self.table.add_column("", style="dim", width=25)
        self.table.add_column('NEW')
        self.table.add_column('OLD')
        self.table.add_column('MERGED')
        self.attributes = [
            'isin',
            'bse_security_code',
            'bse_security_id',
            'bse_name',
            'status',
            'face_value',
            'industry',
            'old_bse_security_code',
            'old_bse_security_id',
            'nse_name',
            'listing_date',
            'old_nse_symbol',
            'nse_symbol',
            'mc_code',
            'cap',
            'suspension_date'
        ]

    def add_row(self, key, new_value, old_value, merged_value):
        self.table.add_row(key, new_value, old_value, merged_value)

    def add_rows(self):
        for att in self.attributes:
            self.add_row(att, getattr(self.new_item, att), getattr(self.old_item, att), getattr(self.merged_item, att))
    
    def print_table(self):
        self.add_rows()
        self.console.print(self.table)

def find_newer_date(first_dt, second_dt):
    if first_dt == '':
        return second_dt
    if second_dt == '':
        return first_dt
    if first_dt == second_dt:
        return first_dt
    date_format = "%d-%b-%Y"

    # Convert the string to a datetime object
    fd = datetime.strptime(first_dt, date_format)
    sd = datetime.strptime(second_dt, date_format)
    if fd > sd:
        return fd.strftime(date_format)
    return sd.strftime(date_format)

def find_older_date(first_dt, second_dt):
    if first_dt == '':
        return second_dt
    if second_dt == '':
        return first_dt
    if first_dt == second_dt:
        return first_dt
    date_format = "%d-%b-%Y"

    # Convert the string to a datetime object
    fd = datetime.strptime(first_dt, date_format)
    sd = datetime.strptime(second_dt, date_format)
    if fd < sd:
        return fd.strftime(date_format).upper()
    return sd.strftime(date_format).upper()

def ask_yes_no(question):
    # Ask the user for input
    response = input(question + " (y/n/s): ").strip().lower()
    
    # Return True if the response starts with 'y', otherwise False
    if response.startswith('y'):
        return 0
    elif response.startswith('n'):
        return 1
    else:
        return 2

if __name__ == "__main__":
    update_nse(download_dir())
    update_bse(download_dir())
    merge_new_info(download_dir())
    copy_selected_fields()
    interactive_mapping()
    add_new_data()
    