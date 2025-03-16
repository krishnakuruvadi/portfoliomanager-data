from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import json
import os
import time
from .utils import get_files_in_dir, get_new_files_added

bse_url = 'https://www.bseindia.com/corporates/List_Scrips.aspx'


def pull_bse(download_dir):
    existing_files = get_files_in_dir(download_dir)

    chrome_options = webdriver.ChromeOptions()
    prefs = {'download.default_directory' : download_dir}
    chrome_options.add_experimental_option('prefs', prefs)
    #chrome_options.add_argument("--headless")
    service = Service()

    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(bse_url)
    timeout = 10
    try:
        time.sleep(3)
        WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.ID, "ddlsegment")))
        print('select element located')
        time.sleep(3)
        driver.find_element("xpath", "//select[@id='ddlsegment']/option[text()='Equity T+1']").click()
        print('select element clicked')
        time.sleep(3)
        driver.find_element("xpath", "//input[@id='btnSubmit']").click()
        print('submit element clicked')
        time.sleep(3)
        dload = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.ID,'lnkDownload')))
        print('download element located')
        time.sleep(3)
        dload.click()
        print('download element clicked')
        time.sleep(3)
        dload_file_name = None
        for _ in range(5):
            time.sleep(5)
            new_file_list = get_new_files_added(download_dir, existing_files)        
            if len(new_file_list) == 1:
                dload_file_name = new_file_list[0]
                break
            elif len(new_file_list) > 1:
                description = ''
                for fil in new_file_list:
                    description = description + fil
                
                summary='Failure to get bse equity list.  More than one file found;' + description
                print(summary)
                exit(1)
        if dload_file_name:
            os.rename(dload_file_name, bse_eq_file_path(download_dir))

    except Exception as ex:
        print('Exception during pulling from bse', ex)
    driver.close()
    driver.quit()

def bse_eq_file_path(download_dir):
    full_file_path = os.path.join(download_dir, 'bse_eq.csv')
    return full_file_path

def is_bse_eq_file_exists(download_dir):
    full_file_path = bse_eq_file_path(download_dir)
    if os.path.exists(full_file_path):
        return True
    return False

def add_or_append(inp, new_str):
    if not inp or inp == '':
        return new_str
    l = inp.split(';')
    if new_str in l:
        return inp
    return inp + ';' + new_str

def clean(d):
    res = dict()
    for k,v in d.items():
        res[k.strip()] = v
    return res

def nse_bse_eq_file_path(download_dir):
    full_file_path = os.path.join(download_dir, 'nse_bse_eq.json')
    return full_file_path

def is_nse_bse_eq_file_exists(download_dir):
    full_file_path = nse_bse_eq_file_path(download_dir)
    if os.path.exists(full_file_path):
        return True
    return False

def update_bse(download_dir, delete_downloaded_files, delete_processed_files):
    print(f'download directory {download_dir}')
    b_path = bse_eq_file_path(download_dir)
    n_b_path = nse_bse_eq_file_path(download_dir)

    if os.path.exists(b_path):
        print(f'Removing {b_path}')
        os.remove(b_path)
    pull_bse(download_dir)
    print(f'Downloaded BSE data to {b_path}')
    stocks = dict()

    if is_nse_bse_eq_file_exists(download_dir):
        with open(n_b_path) as f:
            stocks = json.load(f)
    
    with open(b_path, mode='r', encoding='utf-8-sig') as bse_csv_file:
        csv_reader = csv.DictReader(bse_csv_file)
        for temp in csv_reader:
            #print(row)
            row = clean(temp)
            isin = row['ISIN No'].strip()
            if isin == '' or isin == 'NA' or not isin.startswith('IN'):
                print(f'ignoring isin {isin}')
                continue
            if not isin in stocks:
                # dont track rights entitled shares
                if '-RE' in row['Security Id']:
                    continue
                stocks[isin] = {
                                'bse_security_code':row['Security Code'], 
                                'bse_security_id':row['Security Id'], 
                                'bse_name': row['Security Name'], 
                                'status':row['Status'], 
                                'face_value':row['Face Value'], 
                                'industry':row['Industry'],
                                'old_bse_security_code':'',
                                'old_bse_security_id':'',
                                'nse_name':'',
                                'listing_date':'',
                                'old_nse_symbol':'',
                                'nse_symbol':'',
                                'mc_code':'',
                                'cap':'',
                                'suspension_date':''
                                }
            else:
                if row['Security Code'] != stocks[isin]['bse_security_code']:
                    if stocks[isin]['bse_security_code'] != '':
                        stocks[isin]['old_bse_security_code'] = add_or_append(stocks[isin].get('old_bse_security_code', None), row['Security Code'])
                    stocks[isin]['bse_security_code'] = row['Security Code']
                if row['Security Id'] != stocks[isin]['bse_security_id']:
                    if stocks[isin]['bse_security_id'] != '':
                        stocks[isin]['old_bse_security_id'] = add_or_append(stocks[isin].get('old_bse_security_id', None), row['Security Id'])
                    stocks[isin]['bse_security_id'] = row['Security Id']
                stocks[isin]['status'] = row['Status']
                stocks[isin]['face_value'] = row['Face Value']
                stocks[isin]['industry'] = row['Industry']
                stocks[isin]['bse_name'] = row['Security Name']

    
    with open(n_b_path, 'w') as json_file:
        json.dump(stocks, json_file, indent=1)
    if delete_downloaded_files:
        os.remove(b_path)
    