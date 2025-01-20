import datetime
import requests
from .mf_entry import get_mf_entries, get_new_entry, write_entries
from .mf_amfi import get_schemes

def update_kuvera_mapping():
    data = get_mf_entries()
    start = datetime.datetime.now()
    url = "https://api.kuvera.in/mf/api/v4/fund_schemes/list.json"
    r = requests.get(url, timeout=30)
    status = r.status_code
    if status != 200:
        print(f"An error has occured. [Status code {status} ]")
    else:
        ak_mapping = get_amfi_kuvera_fund_house_mapping()
        a_schemes, _ = get_schemes()
        #print(a_schemes)
        modified = 0
        added = 0
        mod_list = list()

        for fund_type,v in r.json().items():
            #print(fund_type)
            for sub_category, details in v.items():
                #print(sub_category)
                for fund_house, fund_details in details.items():
                    #print(fund_house)
                    for fund in fund_details:
                        name = fund['n']
                        code = fund['c']
                        scheme_url = f"https://api.kuvera.in/mf/api/v5/fund_schemes/{code}.json?v=1.230.10"

                        response = requests.get(scheme_url, timeout=15)
                        if response.status_code != 200:
                            print('failed to get scheme details for {scheme_url}')
                            continue
                        j = response.json()
                        #dt = fund['r'].get('date')
                        print(f'{scheme_url} got {j}')
                        k_isin = j[0]['ISIN']
                        for code,det in a_schemes.items():
                            if k_isin != '' and (det['isin1'] == k_isin or det['isin2'] == k_isin):
                                if code in data:
                                    prev = data[code]
                                    changed = False
                                    if data[code]['kuvera_name'] != j[0]['name']:
                                        data[code]['kuvera_name'] = j[0]['name']
                                        changed = True
                                    if data[code]['kuvera_fund_category'] != j[0]['fund_category']:
                                        data[code]['kuvera_fund_category'] = j[0]['fund_category']
                                        changed = True
                                    if data[code]['kuvera_code'] != j[0]['code']:
                                        data[code]['kuvera_code'] = j[0]['code']
                                        changed = True
                                    if data[code].get('category', '') != j[0]['category']:
                                        data[code]['category'] = j[0]['category']
                                        changed = True
                                    if changed:
                                        modified += 1
                                        print(f'before {prev} after {data[code]}')
                                else:
                                    data[code] = get_new_entry()
                                    data[code]['category'] = j[0]['category']
                                    data[code]['kuvera_name'] = j[0]['name']
                                    data[code]['kuvera_code'] = j[0]['code']
                                    data[code]['kuvera_fund_category'] = j[0]['fund_category']
                                    added += 1
                                break
                        
    print(f'added {added} modified {modified}')

    if added > 0 or modified > 0:
        write_entries(data)

    print(f'finished in {(datetime.datetime.now()-start).total_seconds()} s')

def get_amfi_kuvera_fund_house_mapping():
    return {
        'BirlaSunLifeMutualFund_MF':'Aditya Birla Sun Life Mutual Fund',
        'AXISMUTUALFUND_MF':'Axis Mutual Fund',
        'BARODAMUTUALFUND_MF':'Baroda Mutual Fund',
        'BNPPARIBAS_MF':'BNP Paribas Mutual Fund',
        'BHARTIAXAMUTUALFUND_MF':'BOI AXA Mutual Fund',
        'CANARAROBECOMUTUALFUND_MF':'Canara Robeco Mutual Fund',
        'DSP_MF':'DSP Mutual Fund',
        'EDELWEISSMUTUALFUND_MF':'Edelweiss Mutual Fund',
        'FRANKLINTEMPLETON':'Franklin Templeton Mutual Fund',
        'HDFCMutualFund_MF':'HDFC Mutual Fund',
        'HSBCMUTUALFUND_MF':'HSBC Mutual Fund',
        'ICICIPrudentialMutualFund_MF':'ICICI Prudential Mutual Fund',
        'IDBIMUTUALFUND_MF':'IDBI Mutual Fund',
        'IDFCMUTUALFUND_MF':'IDFC Mutual Fund',
        'JM FINANCIAL MUTUAL FUND_MF':'JM Financial Mutual Fund',
        'KOTAKMAHINDRAMF':'Kotak Mahindra Mutual Fund',
        'LICMUTUALFUND_MF':'LIC Mutual Fund',
        'MOTILALOSWAL_MF':'Motilal Oswal Mutual Fund',
        'NipponIndiaMutualFund_MF':'Nippon India Mutual Fund',
        'PGIMINDIAMUTUALFUND_MF':'PGIM India Mutual Fund',
        'PRINCIPALMUTUALFUND_MF':'Principal Mutual Fund',
        'QUANTMUTUALFUND_MF':'quant Mutual Fund',
        'SBIMutualFund_MF':'SBI Mutual Fund',
        'SUNDARAMMUTUALFUND_MF':'Sundaram Mutual Fund',
        'TATAMutualFund_MF':'Tata Mutual Fund',
        'TAURUSMUTUALFUND_MF':'Taurus Mutual Fund',
        'UNIONMUTUALFUND_MF':'Union Mutual Fund'
    }

