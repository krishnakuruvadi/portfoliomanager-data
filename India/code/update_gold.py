
import datetime
import requests
import bs4
import json
import os
from helpers.utils import get_float_or_none_from_string, get_date_or_none_from_string
from dateutil.relativedelta import relativedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service as ChromeService


def get_latest_physical_gold_price():
    url = 'https://www.gadgets360.com/finance/gold-rate-in-india'
    # Initialize the WebDriver
    chrome_options = webdriver.ChromeOptions()
    '''
    # none of the below options help with headless
    #chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False) 
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--remote-debugging-port=9222")
    '''
    driver = webdriver.Chrome(service=ChromeService(), options=chrome_options)
    driver.get(url)
    # Wait for the page to load completely (you can adjust the wait time as needed)
    driver.implicitly_wait(10)  # Wait for up to 10 seconds for elements to be available
    # Find the element containing the gold price (you may need to adjust the selector)
    tables = driver.find_elements(By.TAG_NAME, 'table')
    res = dict()
    for table in tables:
        try:
            # get the heading of the table using thead tag
            thead = table.find_element(By.TAG_NAME, 'thead')
            # search for 'Date' and 'Pure Gold (24K)' in the rows of thead
            if 'Date' in thead.text and 'Pure Gold (24K)' in thead.text and '22K' in thead.text:
                rows = table.find_elements(By.TAG_NAME, 'tr')
                for i, row in enumerate(rows):
                    if i == 0:
                        continue
                    cols = row.find_elements(By.TAG_NAME, 'td')
                    dt = get_date_or_none_from_string(cols[0].text.strip(), "%d %B %Y")
                    val24k = get_float_or_none_from_string(cols[1].text.replace('₹ ', '').replace(',',''))
                    val22k = get_float_or_none_from_string(cols[2].text.replace('₹ ', '').replace(',',''))
                    if dt and val22k and val24k:
                        res[dt] = {"24K": val24k/10, "22K":val22k/10}
        except NoSuchElementException:
            continue
    driver.quit()
    if res:
        return res
    # If the above method fails, fallback to requests and BeautifulSoup
    r = requests.get(url, timeout=15, allow_redirects=True)
    if r.status_code==200:
        # Creating a bs4 object to store the contents of the requested page
        soup = bs4.BeautifulSoup(r.content, 'html.parser')
        h2 = soup.find_all("h2")
        for item in h2:
            if 'Daily Gold Rate In India' in item.text:
                rows = item.parent.find_all('tr')
                for i, row in enumerate(rows):
                    if i == 0:
                        continue
                    cols = row.find_all('td')
                    dt = get_date_or_none_from_string(cols[0].text.strip(), "%d %B %Y")
                    val24k = get_float_or_none_from_string(cols[1].text.replace('₹ ', '').replace(',',''))
                    val22k = get_float_or_none_from_string(cols[2].text.replace('₹ ', '').replace(',',''))
                    if dt and val22k and val24k:
                        res[dt] = {"24K": val24k/10, "22K":val22k/10}
        return res
    else:
        print(f"Page not found {r.status_code} {url}")
    print('failed to get any price for latest physical gold price')
    return res   

def get_last_close_digital_gold_price():
    url = 'https://www.gadgets360.com/finance/digital-gold-price-in-india'
    # Initialize the WebDriver
    chrome_options = webdriver.ChromeOptions()
    #chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(service=ChromeService(), options=chrome_options)
    driver.get(url)
    # Wait for the page to load completely (you can adjust the wait time as needed)
    driver.implicitly_wait(10)  # Wait for up to 10 seconds for elements to be available
    # Find the element containing the gold price (you may need to adjust the selector)
    tables = driver.find_elements(By.TAG_NAME, 'table')
    res = dict()
    for table in tables:
        # get the heading of the table using thead tag
        thead = table.find_element(By.TAG_NAME, 'thead')
        # search for 'Date' and 'Pure Gold (24K)' in the rows of thead
        if 'Date' in thead.text and 'Price' in thead.text and 'Close' in thead.text:
            rows = table.find_elements(By.TAG_NAME, 'tr')
            for i, row in enumerate(rows):
                if i == 0:
                    continue
                cols = row.find_elements(By.TAG_NAME, 'td')
                dt = get_date_or_none_from_string(cols[0].text.strip(), "%d %B %Y")
                val24k = get_float_or_none_from_string(cols[3].text.replace('₹ ', '').replace(',',''))
                if dt and val24k:
                    res[dt] = val24k
    driver.quit()
    if res:
        return res
    r = requests.get(url, timeout=15, allow_redirects=True)
    res = dict()
    if r.status_code==200:
        # Creating a bs4 object to store the contents of the requested page
        soup = bs4.BeautifulSoup(r.content, 'html.parser')
        h2 = soup.find_all("h2")
        for item in h2:
            if 'Digital Gold Price for Last ' in item.text:
                rows = item.parent.find_all('tr')
                for i, row in enumerate(rows):
                    if i == 0:
                        continue
                    cols = row.find_all('td')
                    if len(cols) > 0:
                        dt = get_date_or_none_from_string(cols[0].text.strip(), "%d %B %Y")
                        if dt:
                            val24k = get_float_or_none_from_string(cols[1].text.replace('₹ ', '').replace(',',''))
                            if val24k:
                                res[dt] = val24k
                        else:
                            print(f'failed to convert {cols[0].text.strip()} to date')
        return res
    else:
        print(f"Page not found {r.status_code} {url}")
    print('failed to get any price for latest digital gold price')
    return res

def load_entries_from_file():
    # get current directory of the python file
    script_path = os.path.abspath(__file__)
    script_dir = os.path.dirname(script_path)
    gold_dir = os.path.join(os.path.dirname(script_dir), 'gold')
    if not os.path.exists(gold_dir):
        raise Exception(f"gold directory {gold_dir} does not exist")
    today = datetime.date.today()
    gold_file_path = os.path.join(gold_dir, f'{today.year}.json')
    if not os.path.exists(gold_file_path):
        # create file with content
        data = {
            "date_format": "dd/mm/yyyy",
            "currency": "INR",
            "weight": "gram",
            "prices": {
            }
        }
        with open(gold_file_path, 'w') as f:
            json.dump(data, f, indent=4)
    with open(gold_file_path, 'r') as f:
        data = json.load(f)
    return data, gold_file_path

def write_entries_to_file(data, file_path):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def update_gold_price():
    try:
        data, file_path = load_entries_from_file()
        physical_gold = get_latest_physical_gold_price()
        print(f'physical gold prices fetched {len(physical_gold)} entries')
        digi_gold = get_last_close_digital_gold_price()
        print(f'digital gold prices fetched {len(digi_gold)} entries')
        for k,v in digi_gold.items():
            if k in physical_gold and k.day == 1:
                dt_str = k.strftime("%d/%m/%Y")
                if dt_str not in data["prices"]:
                    data["prices"][dt_str] = dict()
                    data["prices"][dt_str]["24K"] = physical_gold[k]["24K"]
                    data["prices"][dt_str]["22K"] = physical_gold[k]["22K"]
                    data["prices"][dt_str]["digital"] = v

        write_entries_to_file(data, file_path)
        print(f'gold prices updated to file {file_path}')
    except Exception as ex:
        print(f"exception {ex} when getting gold price")

def main():
    """
    The main function of the script.
    Contains the primary logic to be executed.
    """
    update_gold_price()

if __name__ == "__main__":
    # This block is executed only when the script is run directly
    main()
