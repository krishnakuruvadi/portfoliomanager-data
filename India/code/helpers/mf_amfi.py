from mftool import Mftool
import datetime
import requests
from .utils import get_date_or_none_from_string, get_date_or_none_from_string, get_float_or_zero_from_string



def get_all_schemes()->dict:
    try:
        mf = Mftool()
        url = mf._get_quote_url
        response = mf._session.get(url)
        data = response.text.split("\n")
    except Exception as e:
        print(f'ERROR: exception fetching amfi details using Mftool: {e}.  Trying alternate')
        data = get_schemes_alternate()
    scheme_info = {}
    fund_house = ""
    amfi_fund_type = ""
    amfi_fund_category = ""
    ignored_zero_nav = 0
    ignored_no_isin = 0
    count = 0
    month_ago = datetime.datetime.today() - datetime.timedelta(days=30)
    month_ago = month_ago.date()
    for scheme_data in data:
        if ";INF" in scheme_data:
            try:
                scheme = scheme_data.rstrip().split(";")
                if get_float_or_zero_from_string(scheme[4]) > 0:
                    isin = ''
                    if scheme[1] and scheme[1] != '' and scheme[1] != '-':
                        isin = scheme[1]
                    isin2 = ''
                    if scheme[2] and scheme[2] != '' and scheme[2] != '-':
                        isin2 = scheme[2]
                    scheme_info[scheme[0]] = {'isin': isin,
                                            'isin2':isin2,
                                            'name':scheme[3],
                                            'nav':scheme[4],
                                            'date':scheme[5],
                                            'amfi_fund_type':amfi_fund_type,
                                            'amfi_category':amfi_fund_category}
                    if not 'open ended' in fund_house.lower() and fund_house != '':
                        scheme_info[scheme[0]]['fund_house'] = fund_house
                    dt = get_date_or_none_from_string(scheme[5], '%d-%b-%Y')
                    if dt and dt < month_ago:
                        scheme_info[scheme[0]]['end_date'] = dt.strftime('%d-%m-%Y')
                    count += 1
            except Exception as e:
                print(f'ERROR: exception processing scheme data {scheme_data}: {e}')
                
        elif scheme_data.strip() != "":
            if ';' not in scheme_data:
                if '(' in scheme_data and ')' in scheme_data and 'Mutual Fund' not in scheme_data:
                    fund_house = scheme_data.strip()
                    # extract content between parentheses
                    fund_type_info = scheme_data[scheme_data.find("(")+1:scheme_data.find(")")].strip()
                    if '-' in fund_type_info:
                        splits = fund_type_info.split('-')
                        amfi_fund_type = splits[0].strip() if splits else ''
                        amfi_fund_category = splits[1].strip() if len(splits) > 1 else ''
                        if 'hildren' in amfi_fund_category.lower():
                            amfi_fund_category = "Children's Fund"
                    else:
                        amfi_fund_type = fund_type_info.strip()
                else:
                    fund_house = scheme_data.strip()
    print(f'found {count} funds. ignored {ignored_zero_nav} zero nav funds and {ignored_no_isin} no isin funds')

    return scheme_info


def get_schemes_alternate():
    url = "https://portal.amfiindia.com/spages/NAVAll.txt"
    _session = requests.Session()
    _session.verify = False
    response = _session.get(url)
    data = response.text.split("\n")
    return data

def get_details_amfi(code):
        """
        gets the scheme info for a given scheme code
        :param code: scheme code
        :param as_json: default false
        :return: dict or None
        :raises: HTTPError, URLError
        """
        code = str(code)
        scheme_info = {}
        url = f"https://api.mfapi.in/mf/{code}"
        _session = requests.Session()
        _session.verify = False
        response = _session.get(url).json()
        # close the session after use
        _session.close()
        scheme_data = response['meta']
        scheme_info['fund_house'] = scheme_data['fund_house']
        splits = scheme_data['scheme_category'].split('-')
        fund_type = splits[0].strip() if splits else ''
        fund_category = splits[1].strip() if len(splits) > 1 else ''
        scheme_info['amfi_fund_type'] = fund_type
        scheme_info['amfi_fund_category'] = fund_category
        scheme_info['scheme_code'] = scheme_data['scheme_code']
        scheme_info['name'] = scheme_data['scheme_name']
        last_day = response['data'][int(len(response['data']) -1)]
        scheme_info['scheme_start_date'] = last_day['date']
        first_date = get_date_or_none_from_string(response['data'][0]['date'], '%d-%m-%Y')
        month_ago = datetime.datetime.today() - datetime.timedelta(days=30)
        month_ago = month_ago.date()
        if first_date and first_date < month_ago:
            scheme_info['scheme_end_date'] = response['data'][0]['date']
        else:            
            scheme_info['scheme_end_date'] = ''
        return scheme_info


def check_amfi_entry_complete(entry):
    required_fields = ['name', 'fund_house', 'inception_date', 'amfi_fund_type', 'amfi_category']
    for field in required_fields:
        if not entry.get(field):
            #print(f'entry {entry} is missing required field {field}')
            return False
    if entry['isin'] == '' and entry['isin2'] == '':
        return False
    return True
