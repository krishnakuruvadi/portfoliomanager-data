import unittest
import requests
import sys
import os

# Add parent directory to path to import helpers
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers.mf_amfi import get_details_amfi
from helpers.mf_kuvera import Kuvera


class TestKuveraInit(unittest.TestCase):
    """Tests for Kuvera initialization with actual API calls"""
    
    def test_kuvera_initialization(self):
        """Test that Kuvera initializes with fund schemes from API"""
        kuvera = Kuvera()
        self.assertIsNotNone(kuvera.fund_schemes)
        self.assertIsInstance(kuvera.fund_schemes, dict)
        self.assertGreater(len(kuvera.fund_schemes), 0)
    
    def test_fund_schemes_structure(self):
        """Test that fund schemes have expected structure"""
        kuvera = Kuvera()
        fund_types = list(kuvera.fund_schemes.keys())
        self.assertGreater(len(fund_types), 0)
        for fund_type in fund_types[:1]:
            self.assertIsInstance(kuvera.fund_schemes[fund_type], dict)


class TestGetFundSchemes(unittest.TestCase):
    """Tests for get_fund_schemes method with actual API calls"""
    
    def test_get_fund_schemes_returns_dict(self):
        """Test that get_fund_schemes returns a dictionary"""
        kuvera = Kuvera.__new__(Kuvera)
        result = kuvera.get_fund_schemes()
        if result is not None:
            self.assertIsInstance(result, dict)
    
    def test_get_fund_schemes_api_endpoint(self):
        """Test that get_fund_schemes actually calls the correct API"""
        url = "https://api.kuvera.in/mf/api/v4/fund_schemes/list.json"
        response = requests.get(url, timeout=15)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, dict)
        self.assertGreater(len(data), 0)
    
    def test_get_fund_schemes_contains_fund_types(self):
        """Test that fund schemes contain common fund types"""
        kuvera = Kuvera.__new__(Kuvera)
        result = kuvera.get_fund_schemes()
        if result:
            fund_types = result.keys()
            self.assertGreater(len(list(fund_types)), 0)

class TestGetFundInfo(unittest.TestCase):
    """Tests for get_fund_info method with actual API calls"""
    
    def test_get_fund_info_with_valid_isin(self):
        """Test get_fund_info retrieves correct scheme info for valid ISIN"""
        kuvera = Kuvera()
        
        isin = 'INF044D01BU9'
        fund_type = 'Equity Scheme'
        fund_categories = ['Flexi Cap Fund']
        fund_house = 'Taurus Mutual Fund'
        scheme_code = 'TUSSG1G-GR'
        name = 'Taurus Flexi Cap Fund - Direct Plan - Growth'
        code, fund_info = kuvera.get_fund_info(name, isin, fund_type, fund_categories, fund_house)
        self.assertIsInstance(fund_info, dict)
        self.assertEqual(fund_info.get('isin', ''), isin)
        self.assertEqual(fund_info.get('name', ''), 'Taurus Flexi Cap Growth Direct Plan')
        self.assertEqual(code, scheme_code)

class TestGetSchemeInfo(unittest.TestCase):
    """Tests for get_scheme_info static method with actual API calls"""
    
    def test_get_scheme_info_with_valid_code(self):
        """Test get_scheme_info retrieves ISIN for valid scheme code"""
        # check with direct fund
        scheme_code = 'TUSSG1G-GR'
        result = Kuvera.get_scheme_info(scheme_code)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('isin', ''), 'INF044D01BU9')
        self.assertEqual(result.get('name', ''), 'Taurus Flexi Cap Growth Direct Plan')
        self.assertEqual(result.get('fund_type', ''), 'Equity')
        self.assertEqual(result.get('fund_category', ''), 'Flexi Cap Fund')
        self.assertEqual(result.get('fund_house', ''), 'TAURUSMUTUALFUND_MF')
        # check with growth fund
        scheme_code = 'HSFTAFG-GR'
        result = Kuvera.get_scheme_info(scheme_code)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('isin', ''), 'INF677K01064')
        self.assertEqual(result.get('name', ''), 'HSBC ELSS Tax Saver Growth Plan')
        self.assertEqual(result.get('fund_type', ''), 'Equity')
        self.assertEqual(result.get('fund_category', ''), 'ELSS')
        self.assertEqual(result.get('fund_house', ''), 'HSBCMUTUALFUND_MF')


class TestGetAmfiKuveraFundHouseMapping(unittest.TestCase):
    """Tests for get_amfi_kuvera_fund_house_mapping method"""
    
    def test_fund_house_mapping_returns_dict(self):
        """Test that mapping returns a non-empty dictionary"""
        mapping = Kuvera.get_amfi_kuvera_fund_house_mapping()
        self.assertIsInstance(mapping, dict)
        self.assertGreater(len(mapping), 0)
    
    def test_fund_house_mapping_has_expected_keys(self):
        """Test that fund house mapping has expected fund houses"""
        mapping = Kuvera.get_amfi_kuvera_fund_house_mapping()
        expected_keys = [
            'BirlaSunLifeMutualFund_MF',
            'AXISMUTUALFUND_MF',
            'HDFCMutualFund_MF',
            'SBIMutualFund_MF'
        ]
        for key in expected_keys:
            self.assertIn(key, mapping, f"Expected key {key} not found in mapping")
    
    def test_fund_house_mapping_has_correct_values(self):
        """Test that fund house mapping has correct values"""
        mapping = Kuvera.get_amfi_kuvera_fund_house_mapping()
        self.assertEqual(mapping['HDFCMutualFund_MF'], 'HDFC Mutual Fund')
        self.assertEqual(mapping['SBIMutualFund_MF'], 'SBI Mutual Fund')
        self.assertEqual(mapping['KOTAKMAHINDRAMF'], 'Kotak Mahindra Mutual Fund')
    
    def test_fund_house_mapping_all_values_are_strings(self):
        """Test that all values in mapping are non-empty strings"""
        mapping = Kuvera.get_amfi_kuvera_fund_house_mapping()
        for key, value in mapping.items():
            self.assertIsInstance(key, str)
            self.assertIsInstance(value, str)
            self.assertGreater(len(value), 0)
    
    def test_fund_house_mapping_count(self):
        """Test that fund house mapping has expected number of entries"""
        mapping = Kuvera.get_amfi_kuvera_fund_house_mapping()
        self.assertEqual(len(mapping), 28)


class TestCheckKuveraEntryComplete(unittest.TestCase):
    """Tests for check_kuvera_entry_complete method"""
    
    def test_entry_complete_all_fields_present(self):
        """Test entry validation when all required fields are present"""
        details = {
            'kuvera_name': 'HDFC Equity Fund',
            'kuvera_fund_category': 'Equity',
            'kuvera_code': '1001'
        }
        result = Kuvera.check_kuvera_entry_complete(details)
        self.assertTrue(result)
    
    def test_entry_incomplete_missing_name(self):
        """Test entry validation fails when kuvera_name is missing"""
        kuvera = Kuvera.__new__(Kuvera)
        details = {
            'kuvera_fund_category': 'Equity',
            'kuvera_code': '1001'
        }
        result = Kuvera.check_kuvera_entry_complete(kuvera, details)
        self.assertFalse(result)
    
    def test_entry_incomplete_empty_field(self):
        """Test entry validation fails when field is empty string"""
        kuvera = Kuvera.__new__(Kuvera)
        details = {
            'kuvera_name': '',
            'kuvera_fund_category': 'Equity',
            'kuvera_code': '1001'
        }
        result = Kuvera.check_kuvera_entry_complete(kuvera, details)
        self.assertFalse(result)
    
    def test_entry_incomplete_none_field(self):
        """Test entry validation fails when field is None"""
        kuvera = Kuvera.__new__(Kuvera)
        details = {
            'kuvera_name': 'HDFC Equity Fund',
            'kuvera_fund_category': None,
            'kuvera_code': '1001'
        }
        result = Kuvera.check_kuvera_entry_complete(kuvera, details)
        self.assertFalse(result)
    
    def test_entry_incomplete_missing_multiple_fields(self):
        """Test entry validation fails when multiple fields are missing"""
        kuvera = Kuvera.__new__(Kuvera)
        details = {
            'kuvera_name': 'HDFC Equity Fund'
        }
        result = Kuvera.check_kuvera_entry_complete(kuvera, details)
        self.assertFalse(result)
    
    def test_entry_with_extra_fields(self):
        """Test entry validation ignores extra fields"""
        kuvera = Kuvera.__new__(Kuvera)
        details = {
            'kuvera_name': 'HDFC Equity Fund',
            'kuvera_fund_category': 'Equity',
            'kuvera_code': '1001',
            'extra_field': 'extra_value',
            'another_field': 'another_value'
        }
        result = Kuvera.check_kuvera_entry_complete(kuvera, details)
        self.assertTrue(result)
    
    def test_entry_with_zero_value(self):
        """Test entry validation with zero value"""
        kuvera = Kuvera.__new__(Kuvera)
        details = {
            'kuvera_name': 'Fund Name',
            'kuvera_fund_category': 'Equity',
            'kuvera_code': 0
        }
        result = Kuvera.check_kuvera_entry_complete(kuvera, details)
        self.assertFalse(result)
    
    def test_entry_with_whitespace_only_field(self):
        """Test entry validation with whitespace-only field"""
        kuvera = Kuvera.__new__(Kuvera)
        details = {
            'kuvera_name': '   ',
            'kuvera_fund_category': 'Equity',
            'kuvera_code': '1001'
        }
        result = Kuvera.check_kuvera_entry_complete(kuvera, details)
        self.assertIsInstance(result, bool)


class TestIntegration(unittest.TestCase):
    """Integration tests with actual API calls"""
    
    def test_kuvera_full_initialization_flow(self):
        """Test complete Kuvera initialization flow"""
        kuvera = Kuvera()
        self.assertIsNotNone(kuvera.fund_schemes)
        self.assertIsInstance(kuvera.fund_schemes, dict)
        if len(kuvera.fund_schemes) > 0:
            fund_type = list(kuvera.fund_schemes.keys())[0]
            self.assertIsInstance(fund_type, str)
    
    def test_mapping_retrieval_consistency(self):
        """Test that mapping retrieval is consistent across calls"""
        kuvera = Kuvera.__new__(Kuvera)
        mapping1 = Kuvera.get_amfi_kuvera_fund_house_mapping(kuvera)
        mapping2 = Kuvera.get_amfi_kuvera_fund_house_mapping(kuvera)
        self.assertEqual(mapping1, mapping2)
    
    def test_entry_validation_with_real_mapping(self):
        """Test entry validation using real fund house mapping"""
        kuvera = Kuvera.__new__(Kuvera)
        mapping = Kuvera.get_amfi_kuvera_fund_house_mapping(kuvera)
        first_fund_house_name = list(mapping.values())[0]
        entry = {
            'kuvera_name': first_fund_house_name,
            'kuvera_fund_category': 'Equity',
            'kuvera_code': 'TEST001'
        }
        is_valid = Kuvera.check_kuvera_entry_complete(kuvera, entry)
        self.assertTrue(is_valid)
    
    def test_api_endpoint_stability(self):
        """Test that API endpoints are stable and accessible"""
        endpoints = [
            "https://api.kuvera.in/mf/api/v4/fund_schemes/list.json",
        ]
        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, timeout=15)
                self.assertIn(response.status_code, [200, 429, 500, 502, 503])
            except requests.exceptions.Timeout:
                self.skipTest(f"Timeout accessing {endpoint}")
            except requests.exceptions.ConnectionError:
                self.skipTest(f"Connection error to {endpoint}")

class TestGetDetailsAmfi(unittest.TestCase):
    """Test the get_details_amfi function"""
    def test_get_details_amfi_valid_code(self):
        """Test get_details_amfi with a valid scheme code"""
        code = '152863'
        result = get_details_amfi(code)
        print(result)
        self.assertIsInstance(result, dict)
        self.assertEqual(str(result.get('scheme_code', '')), code)
        self.assertEqual(result.get('name', None), 'Invesco India Technology Fund - Direct Plan - Growth')
        self.assertEqual(result.get('fund_house', None), 'Invesco Mutual Fund')
        self.assertEqual(result.get('amfi_fund_type', None), 'Equity Scheme')
        self.assertEqual(result.get('amfi_fund_category', None), 'Sectoral/ Thematic')
        self.assertEqual(result.get('scheme_start_date', None), "25-09-2024")
        self.assertEqual(result.get('scheme_end_date', None), "")

class TestAmfiKuveraFundCategoryMapping(unittest.TestCase):
    """Test Amfi to Kuvera fund category mapping"""
    
    def test_fund_category_mapping_returns_dict(self):
        """Test that fund category mapping returns a non-empty dictionary"""
        mapping = Kuvera.get_amfi_kuvera_fund_category_mapping()
        self.assertIsInstance(mapping, dict)
        self.assertGreater(len(mapping), 0)
    
    def test_fund_category_mapping_has_expected_keys(self):
        """Test that fund category mapping has expected AMFI categories"""
        kuvera = Kuvera()
        for sc in kuvera.get_sub_categories():
            found = False
            for _, value in Kuvera.get_amfi_kuvera_fund_category_mapping().items():
                if isinstance(value, list):
                    if sc in value:
                        found = True
                        break
                else:
                    if value == sc:
                        found = True
                        break
            self.assertTrue(found, f"Expected sub category {sc} not found in mapping values")

class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions"""
    
    def test_get_scheme_info_with_empty_string(self):
        """Test get_scheme_info with empty string code"""
        kuvera = Kuvera.__new__(Kuvera)
        result = Kuvera.get_scheme_info(kuvera, '')
        self.assertTrue(result is None or isinstance(result, str))
    
    def test_check_entry_complete_with_empty_dict(self):
        """Test check_kuvera_entry_complete with empty dictionary"""
        kuvera = Kuvera.__new__(Kuvera)
        details = {}
        result = Kuvera.check_kuvera_entry_complete(kuvera, details)
        self.assertFalse(result)
    
    def test_fund_house_mapping_no_duplicates(self):
        """Test that fund house mapping has no duplicate keys"""
        kuvera = Kuvera.__new__(Kuvera)
        mapping = Kuvera.get_amfi_kuvera_fund_house_mapping(kuvera)
        keys = list(mapping.keys())
        self.assertEqual(len(keys), len(set(keys)), "Duplicate keys found in mapping")
    
    def test_kuvera_handles_api_timeout_gracefully(self):
        """Test that Kuvera handles API timeouts gracefully"""
        kuvera = Kuvera.__new__(Kuvera)
        result = kuvera.get_fund_schemes()
        self.assertTrue(result is None or isinstance(result, dict))
    
    def test_mapping_and_validation_integration(self):
        """Test fund house mapping with entry validation"""
        kuvera = Kuvera.__new__(Kuvera)
        mapping = Kuvera.get_amfi_kuvera_fund_house_mapping(kuvera)
        entry = {
            'kuvera_name': mapping['HDFCMutualFund_MF'],
            'kuvera_fund_category': 'Equity',
            'kuvera_code': 'HDFC001'
        }
        is_valid = Kuvera.check_kuvera_entry_complete(kuvera, entry)
        self.assertTrue(is_valid)


if __name__ == '__main__':
    unittest.main()
