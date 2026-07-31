import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from helpers.mf_amfi import parse_fund_type_info


class TestParseFundTypeInfo(unittest.TestCase):
    def test_extracts_nested_parenthetical_fund_type_and_category(self):
        fund_house, amfi_fund_type, amfi_fund_category = parse_fund_type_info(
            'Open Ended Schemes(Exchange Traded Funds (ETFs) - Equity ETF)'
        )

        self.assertEqual(fund_house, 'Open Ended Schemes')
        self.assertEqual(amfi_fund_type, 'Exchange Traded Funds (ETFs)')
        self.assertEqual(amfi_fund_category, 'Equity ETF')

    def test_handles_simple_parenthetical_without_hyphen(self):
        fund_house, amfi_fund_type, amfi_fund_category = parse_fund_type_info(
            'Open Ended Schemes(Equity Scheme)'
        )

        self.assertEqual(fund_house, 'Open Ended Schemes')
        self.assertEqual(amfi_fund_type, 'Equity Scheme')
        self.assertEqual(amfi_fund_category, '')

    def test_extracts_type_and_category_for_equity_value_fund(self):
        fund_house, amfi_fund_type, amfi_fund_category = parse_fund_type_info(
            'Open Ended Schemes(Equity Schemes - Value Fund)'
        )

        self.assertEqual(fund_house, 'Open Ended Schemes')
        self.assertEqual(amfi_fund_type, 'Equity Schemes')
        self.assertEqual(amfi_fund_category, 'Value Fund')
