from mftool import Mftool
import json
import pandas as pd
from .mf_entry import write_entries, get_new_entry, get_mf_entries
from .utils import get_float_or_zero_from_string

def update_amfi_details():
    print('updating amfi details')
    
    mf_schemes, ignored = get_schemes(False)
    data = get_mf_entries()
    added = 0
    modified = 0
    for code, details in mf_schemes.items():
        isin2 = ''
        if details['isin2'] and details['isin2'] != '' and details['isin2'] != '-':
            isin2 = details['isin2']
        if code not in data:
            data[code] = get_new_entry()
            data[code]['name'] = details['name']
            data[code]['isin'] = details['isin1']
            data[code]["isin2"] = isin2
            data[code]['fund_house'] = details['fund_house']            
            added += 1
        else:
            changed = False
            prev = data[code]
            if data[code]['name'] != details['name']:
                data[code]['name'] = details['name']
                changed = True
            if data[code]['isin'] != details['isin1']:
                data[code]['isin'] = details['isin1']
                changed = True
            if data[code]['isin2'] != isin2:
                data[code]['isin2'] = isin2
                changed = True
            if data[code]['fund_house'] != details['fund_house']:
                data[code]['fund_house'] = details['fund_house']
                changed = True
            if changed:
                modified += 1
                print(f'before: {prev} after {data[code]}')
    print(f'added {added} modified {modified} ignored {ignored}')
    if added > 0 or modified > 0:
        write_entries(data)

def get_schemes(as_json=False):
    """
    returns a dictionary with key as scheme code and value as scheme name.
    cache handled internally
    :return: dict / json
    """
    mf = Mftool()
    scheme_info = {}
    url = mf._get_quote_url
    response = mf._session.get(url)
    data = response.text.split("\n")
    fund_house = ""
    ignored = 0
    for scheme_data in data:
        if ";INF" in scheme_data:
            scheme = scheme_data.rstrip().split(";")
            if get_float_or_zero_from_string(scheme[4]) > 0:
                #print(scheme[1],', ',scheme[2])
                scheme_info[scheme[0]] = {'isin1': scheme[1],
                                        'isin2':scheme[2],
                                        'name':scheme[3],
                                        'nav':scheme[4],
                                        'date':scheme[5],
                                        'fund_house':fund_house}
            else:
                print(f'ignoring {scheme[4]} nav fund {scheme[3]}')
                ignored += 1
        elif scheme_data.strip() != "":
            if ';' not in scheme_data:
                fund_house = scheme_data.strip()
            else:
                print(f'ignoring fund with no isin: {scheme_data}')
                ignored += 1

    return render_response(scheme_info, as_json), ignored

def render_response(data, as_json=False, as_Dataframe=False):
    if as_json is True:
        return json.dumps(data)
    # parameter 'as_Dataframe' only works with get_scheme_historical_nav()
    elif as_Dataframe is True:
        df = pd.DataFrame.from_records(data['data'])
        df['dayChange'] = df['nav'].astype(float).diff(periods=-1)
        df = df.set_index('date')
        return df
    else:
        return data

'''
def get_amfi_schemes():
    """
    returns a dictionary with key as scheme code and value as scheme name.
    cache handled internally
    :return: dict / json
    """
    mf = Mftool()
    scheme_info = {}
    url = mf._get_quote_url
    response = mf._session.get(url)
    data = response.text.split("\n")
    fund_house = ""
    for scheme_data in data:
        if ";INF" in scheme_data:
            scheme = scheme_data.rstrip().split(";")
            if get_float_or_zero_from_string(scheme[4]) > 0:
                d = get_date_or_none_from_string(scheme[5], '%d-%b-%Y')
                #print(scheme[1],', ',scheme[2])
                if d:
                    scheme_info[scheme[0]] = {'isin1': scheme[1],
                                            'isin2':scheme[2],
                                            'name':scheme[3],
                                            'nav':get_float_or_zero_from_string(scheme[4]),
                                            'date':d,
                                            'fund_house':fund_house}
            else:
                print(f'ignoring {scheme[4]} nav fund {scheme[3]}')
        elif scheme_data.strip() != "":
            if ';' not in scheme_data:
                fund_house = scheme_data.strip()
    return scheme_info
'''


