import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Kuvera:
    def __init__(self):
        self.fund_schemes = dict()
        self.sub_categories = set()
        self.get_fund_schemes()
        self.get_fund_mapping_per_fund_house()
        self.isin_to_kuvera_code_mapping = dict()

    def get_sub_categories(self):
        return self.sub_categories
    
    def get_known_isin_mapping(self):
        return self.isin_to_kuvera_code_mapping
    
    def get_fund_schemes(self):
        att = 0
        while att < 5:
            try:
                url = "https://api.kuvera.in/mf/api/v4/fund_schemes/list.json"
                att += 1
                print(f'getting funds from {url}')
                page_list_funds = requests.get(url, timeout=15)
                if page_list_funds.status_code == 200:
                    page_list_funds_json = page_list_funds.json()
                    for category,v in page_list_funds_json.items():
                        self.fund_schemes[category] = dict()
                        for sub_category, sub_category_details in v.items():
                            #print('sub category is ', sub_category)
                            self.sub_categories.add(sub_category)
                            self.fund_schemes[category][sub_category] = dict()
                            for fund_house, fund_details in sub_category_details.items():
                                amfi_fund_house = Kuvera.get_amfi_kuvera_fund_house_mapping().get(fund_house)
                                self.fund_schemes[category][sub_category][amfi_fund_house] = dict()
                                for fund in fund_details:
                                    code = fund['c']
                                    self.fund_schemes[category][sub_category][amfi_fund_house][code] = {
                                        'name': fund['n'],
                                        'nav': fund['v']
                                    }
                    break
            except Exception as ex:
                print(f'exception {ex} getting {url} attempt {att}')
    
    def get_fund_info(self, name, isin, amfi_fund_type, amfi_fund_category, fund_house):
        # Not sure how to process non direct plans.
        if not 'direct' in name.lower():
            return None
        if isin in self.isin_to_kuvera_code_mapping:
            return self.isin_to_kuvera_code_mapping[isin]
        fund_type = Kuvera.get_amfi_kuvera_fund_type_mapping().get(amfi_fund_type.replace(' Scheme', '').strip())
        if not fund_type:
            print(f'found no fund type for {amfi_fund_type}')
            return None
        fund_categories = Kuvera.get_amfi_kuvera_fund_category_mapping().get(amfi_fund_category)
        if isinstance(fund_categories, str):
            fund_categories = [fund_categories]
        try:
            # filter by fund_type
            funds_of_type = self.fund_schemes[fund_type]
            funds_of_sub_category = list()
            for sub_category in fund_categories:
                funds_of_sub_category.append(funds_of_type[sub_category])
            fund_house_funds = list()
            for sub_category_funds in funds_of_sub_category:
                for fund_house_k, fund_details in sub_category_funds.items():
                    if fund_house_k == fund_house:
                        fund_house_funds.append(fund_details)
            for fund_details in fund_house_funds:
                for code, details in fund_details.items():
                    scheme_info = Kuvera.get_scheme_info(code)
                    if scheme_info and scheme_info.get('isin', '') != '':
                        self.isin_to_kuvera_code_mapping[scheme_info.get('isin')] = scheme_info
                        if scheme_info.get('isin') == isin:
                            return scheme_info
            for fund_details in self.find_probable_fund_name(name):
                scheme_info = Kuvera.get_scheme_info(fund_details['kuvera_code'])
                if scheme_info and scheme_info.get('isin', '') != '':
                    self.isin_to_kuvera_code_mapping[scheme_info.get('isin')] = scheme_info
                    if scheme_info.get('isin') == isin:
                        return scheme_info
        except Exception as e:
            print(f'exception {e} getting fund info for name {name} isin {isin} fund type {fund_type} fund categories {fund_categories} amfi fund category {amfi_fund_category} fund house {fund_house}')
        return None

    @staticmethod
    def get_scheme_info(code):
        try:
            scheme_url = f"https://api.kuvera.in/mf/api/v5/fund_schemes/{code}.json?v=1.230.10"
            response = requests.get(scheme_url, timeout=15)
            if response.status_code == 200:
                j = response.json()
                entry = j[0]
                return {
                    'name': entry['name'],
                    'short_name': entry['short_name'],
                    'fund_category': entry['fund_category'],
                    'fund_type': entry['fund_type'],
                    'fund_house': entry['fund_house'],
                    'isin': entry['ISIN'],
                    'kuvera_code': code
                }
        except Exception as ex:
            print(f'exception {ex} getting {scheme_url}')

    @staticmethod
    def get_amfi_kuvera_fund_type_mapping():
        return {
            'Equity': 'Equity',
            'Debt': 'Debt',
            'Hybrid': 'Hybrid',
            'Other': 'Others',
            'Solution Oriented': 'Solution Oriented',
            'Income': 'Income',
            'ELSS': 'ELSS',
        }
    
    @staticmethod
    def get_amfi_kuvera_fund_category_mapping():
        return {
            'Banking and PSU Fund':'Banking and PSU Fund',
            'Corporate Bond Fund':'Corporate Bond Fund',
            'Credit Risk Fund':'Credit Risk Fund',
            'Dynamic Bond':'Dynamic Bond',
            'Floater Fund':'Floater Fund',
            'Gilt Fund':'Gilt Fund',
            'Gilt Fund with 10 year constant duration':'Gilt Fund with 10 year constant duration',
            'Liquid Fund':'Liquid Fund',
            'Long Duration Fund':'Long Duration Fund',
            'Medium Duration Fund':'Medium Duration Fund',
            'Medium to Long Duration Fund':'Medium to Long Duration Fund',
            'Money Market Fund':'Money Market Fund',
            'Overnight Fund':'Overnight Fund',
            'Short Duration Fund':'Short Duration Fund',
            'Ultra Short Duration Fund':'Ultra Short Duration Fund',
            'Contra Fund':'Contra Fund',
            'Dividend Yield Fund':'Dividend Yield Fund',
            'ELSS': 'ELSS',
            'Flexi Cap Fund':'Flexi Cap Fund',
            'Focused Fund':'Focused Fund',
            'Large & Mid Cap Fund':'Large & Mid Cap fund',
            'Large Cap Fund':'Large Cap Fund',
            'Mid Cap Fund':'Mid Cap Fund',
            'Multi Cap Fund':'Multi Cap Fund',
            'Sectoral/ Thematic':['Sectoral/Thematic','Equity - ESG Fund'],
            'Small Cap Fund':'Small Cap Fund',
            'Value Fund':'Value Fund',
            'Gilt': 'Gilt',
            'Growth': 'Growth',
            'Aggressive Hybrid Fund':'Aggressive Hybrid Fund',
            'Arbitrage Fund':'Arbitrage Fund',
            'Balanced Hybrid Fund':'Balanced Hybrid Fund',
            'Conservative Hybrid Fund':'Conservative Hybrid Fund',
            'Dynamic Asset Allocation or Balanced Advantage':'Dynamic Asset Allocation or Balanced Advantage',
            'Equity Savings':'Equity Savings',
            'Multi Asset Allocation':'Multi Asset Allocation',
            'Income': 'Index Funds - Fixed Income',
            'Money Market': 'Money Market',
            'FoF Domestic':'Fund of Funds',
            'FoF Overseas':['FoF Overseas', 'Other Bond'],
            'Gold ETF':'Gold ETF',
            'Index Funds':'Index Funds',
            'Other  ETFs':'Other  ETFs',
            "Children's Fund":'Childrens Fund',
            'Childrens Fund':'Childrens Fund',
            'Retirement Fund':'Retirement Fund',
            'Low Duration Fund':'Low Duration Fund'
        }
    
    @staticmethod
    def get_amfi_kuvera_fund_house_mapping():
        return {
            'BirlaSunLifeMutualFund_MF':'Aditya Birla Sun Life Mutual Fund',
            'AXISMUTUALFUND_MF':'Axis Mutual Fund',
            'BARODAMUTUALFUND_MF':'Baroda Mutual Fund',
            'BNPPARIBAS_MF':'BNP Paribas Mutual Fund',
            'BANKOFINDIAMUTUALFUND_MF':'BOI AXA Mutual Fund',
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
            'UNIONMUTUALFUND_MF':'Union Mutual Fund',
            'ABAKKUSMUTUALFUND_MF':'Abakkus Mutual Fund',
            'BAJAJ FINSERV_MF':'Bajaj Finserv Mutual Fund',
            'TRUSTMUTUALFUND_MF':'Trust Mutual Fund',
            '360_ONE_MUTUALFUND_MF':'360 ONE Mutual Fund',
            'WHITEOAKCAPITALMUTUALFUND_MF':'WhiteOak Capital Mutual Fund',
            'QUANTMUTUALFUND_MF_SIF':'quant Mutual Fund',
            'INVESCOMUTUALFUND_MF':'Invesco Mutual Fund',
            'BARODABNPPARIBASMUTUALFUND_MF':'Baroda BNP Paribas Mutual Fund',
            'UTIMUTUALFUND_MF':'UTI Mutual Fund',
            'MIRAEASSET':'Mirae Asset Mutual Fund',
            'BANDHANMUTUALFUND_MF':'Bandhan Mutual Fund',
            'BANKOFINDIAMUTUALFUND_MF':'Bank of India Mutual Fund',
            'NAVIMUTUALFUND_MF':'Navi Mutual Fund',
            'NJMUTUALFUND_MF':'NJ Mutual Fund',
            'MAHINDRA MANULIFE MUTUAL FUND_MF':'Mahindra Manulife Mutual Fund',
            'THEWEALTHCOMPANYMUTUALFUND_MF':'The Wealth Company Mutual Fund',
            'UNIFIMUTUALFUND_MF':'Unifi Mutual Fund',
            'GROWWMUTUALFUND_MF':'Groww Mutual Fund',
            'JIOBLACKROCKMUTUALFUND_MF':'Jio BlackRock Mutual Fund',
        }
    
    @staticmethod
    def check_kuvera_entry_complete(details):
        required_fields = ['kuvera_name', 'kuvera_fund_category', 'kuvera_code']
        for field in required_fields:
            if not details.get(field):
                return False
        return True
    
    @staticmethod
    def check_kuvera_skip_entry(details):
        if details.get('isin', '') == '' and details.get('isin2', '') == '':
            return True
        if details.get('amfi_fund_type','') == 'Income' or details.get('end_date', '') != '':
            return True
        return False
    
    @staticmethod
    def find_probable_fund_name(amfi_fund_name):
        url = f'https://api.kuvera.in/insight/api/v1/global_search.json?query={amfi_fund_name.replace(" ", "%20")}&exclude_assets='+'{%22SKIP_ASSETS%22:[%22us_stocks%22]}&v=1.239.11'
        try:
            print(f'getting funds from {url}')
            page_list_funds = requests.get(url, timeout=15)
            if page_list_funds.status_code != 200:
                return []
            page_list_funds_json = page_list_funds.json()
            if page_list_funds_json['status'] != 'success' or len(page_list_funds_json['data']['funds']) == 0:
                return None
            probables = list()
            for fund in page_list_funds_json['data']['funds'].get('mutual_funds', []):
                probables.append({
                    'name': fund['name'],
                    'kuvera_code': fund['unique_fund_code'],
                    'fund_house': fund['amc'],
                    'category': fund['category'],
                    'sub_category': fund['sub_category'],
                    'current_nav': fund['current_nav']
                })
            return probables
        except Exception as e:
            print(f'exception {e} getting probable fund name for {amfi_fund_name} with url {url}')
        return []
    
    def get_fund_mapping_per_fund_house(self):
        fund_houses = self.get_supported_fund_houses()
        for fh in fund_houses:
            for scheme_plan in ['GROWTH', 'DIVIDEND']:
                url = f'https://api.kuvera.in/insight/api/v1/mutual_fund_search.json?query={fh.split(" ")[0]}&limit=1000&sort_by=one_year_return&order_by=desc&scheme_plan={scheme_plan}&v=1.239.11'
                try:
                    print(f'getting funds from {url}')
                    page_list_funds = requests.get(url, timeout=15)
                    if page_list_funds.status_code == 200:
                        page_list_funds_json = page_list_funds.json()
                    for fund_details in page_list_funds_json['data']['funds']:
                        category = fund_details['category']
                        sub_category = fund_details['sub_category']
                        amfi_fund_house = Kuvera.get_amfi_kuvera_fund_house_mapping().get(fund_details['amc'])
                        code = fund_details['unique_fund_code']
                        if not category in self.fund_schemes:
                            self.fund_schemes[category] = dict()
                        self.sub_categories.add(sub_category)
                        if not sub_category in self.fund_schemes[category]:
                            self.fund_schemes[category][sub_category] = dict()
                        self.fund_schemes[category][sub_category][amfi_fund_house] = dict()
                        self.fund_schemes[category][sub_category][amfi_fund_house][code] = {
                                            'name': fund_details['name'],
                                            'nav': fund_details['current_nav']
                                        }
                except Exception as e:
                    print(f'exception {e} getting fund mapping for fund house {fh} with url {url}')
    
    def get_supported_fund_houses(self):
        # Initialize the driver (ensure you have the correct webdriver installed)
        driver = webdriver.Chrome()

        try:
            # Open the page
            driver.get("https://kuvera.in/mutual-funds/all")
            from selenium.webdriver.common.action_chains import ActionChains

            # 1. Find the body to reset the mouse to the top-left corner
            body = driver.find_element(By.TAG_NAME, 'body')

            # 2. Move to (0,0) and then offset to where you want to click (e.g., 100, 100)
            actions = ActionChains(driver)
            actions.move_to_element_with_offset(body, 0, 0)
            actions.move_by_offset(100, 100).click().perform()

            # Wait for the footer links to be present (Mutual Fund Companies section)
            # The links are typically within a section containing 'Mutual Fund Companies' text
            wait = WebDriverWait(driver, 10)
            fund_house_elements = wait.until(EC.presence_of_all_elements_located(
                (By.XPATH, "//div[contains(text(), 'Mutual Fund Companies')]/following-sibling::a | //p[contains(text(), 'Mutual Fund Companies')]/following-sibling::a")
            ))

            # If the footer layout is a flat list of links:
            fund_houses = []
            for element in fund_house_elements:
                name = element.text.strip()
                link = element.get_attribute('href')
                if name:
                    fund_houses.append({"name": name, "link": link})

            # Display Results
            print(f"{'Fund House':<35} | {'URL'}")
            print("-" * 70)
            for fund in fund_houses:
                print(f"{fund['name']:<35} | {fund['link']}")
        except Exception as e:
            print(f'exception {e} getting supported fund houses from kuvera')
        finally:
            driver.quit()
        return ['Axis Mutual Funds',
                'Kotak Mutual Funds',
                'SBI Mutual Funds',
                'ICICI Mutual Funds',
                'Quant Mutual Fund',
                'NJ Mutual Fund',
                'Nippon India Mutual Fund',
                'HDFC',
                'Aditya Birla Sunlife Mutual Fund',
                'LIC',
                'Invesco',
                'Canara Robeco',
                'Motilal Oswal',
                'Mirae Asset',
                'Franklin Templeton',
                'DSP Mutual Fund',
                'PGIM Mutual Fund',
                'Navi Mutual Fund',
                'BOI Mutual Fund',
                'White Oak',
                '360 ONE Mutual Fund',
                'Groww Mutual Fund',
                'Jio BlackRock Mutual Fund',
                'Zerodha Mutual Fund',
                'Bandhan Mutual Fund',
                'Edelweiss Mutual Fund',
                'Union Mutual Fund',
                'Mahindra Manulife Mutual Fund',
                'WhiteOak Capital Mutual Fund'
                ]
'''
name = 'Sundaram Banking & PSU Debt Fund - Direct Quarterly Dividend'
isin = 'INF903J019I1'
amfi_fund_type = 'Debt Scheme'
amfi_fund_category = 'Banking and PSU Fund'
fund_house = 'Sundaram Mutual Fund'
kuvera = Kuvera()
kuvera.get_fund_info(name, isin, amfi_fund_type, amfi_fund_category, fund_house)
'''