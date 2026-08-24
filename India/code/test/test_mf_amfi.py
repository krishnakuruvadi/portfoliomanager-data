import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from helpers.mf_amfi import (
    parse_fund_type_info,
    parse_scheme_name_nav_date,
    name_has_new_info,
    _simplify_plan,
    _simplify_idcw_option,
)


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


class TestParseSchemeNameNavDate(unittest.TestCase):
    def test_legacy_six_field_format(self):
        scheme = ['119550', 'INF209K01YN0', '-', 'Aditya Birla Sun Life Banking & PSU Debt Fund - Direct Plan - Growth', '403.6492', '21-Aug-2026']
        name, nav, date = parse_scheme_name_nav_date(scheme)
        self.assertEqual(name, 'Aditya Birla Sun Life Banking & PSU Debt Fund - Direct Plan - Growth')
        self.assertEqual(nav, '403.6492')
        self.assertEqual(date, '21-Aug-2026')

    def test_new_eight_field_format_with_plan_and_option_split_out(self):
        # AMFI started emitting plan/option as separate fields (Aug 2026) instead
        # of baking them into the name; the old fixed-position parse would read
        # "Direct Plan" as nav and "GROWTH" as date. The word "Plan" is dropped
        # from the reconstructed name since it's redundant.
        scheme = ['119550', 'INF209K01YN0', '-', 'Aditya Birla Sun Life Banking & PSU Debt Fund', 'Direct Plan', 'GROWTH', '403.6492', '21-Aug-2026']
        name, nav, date = parse_scheme_name_nav_date(scheme)
        self.assertEqual(name, 'Aditya Birla Sun Life Banking & PSU Debt Fund - Direct - GROWTH')
        self.assertEqual(nav, '403.6492')
        self.assertEqual(date, '21-Aug-2026')

    def test_eight_field_format_with_blank_option(self):
        scheme = ['119550', 'INF209K01YN0', '-', 'Some Fund', 'Direct Plan', '', '403.6492', '21-Aug-2026']
        name, nav, date = parse_scheme_name_nav_date(scheme)
        self.assertEqual(name, 'Some Fund - Direct')
        self.assertEqual(nav, '403.6492')
        self.assertEqual(date, '21-Aug-2026')

    def test_verbose_idcw_option_is_simplified(self):
        scheme = ['110282', 'INF209K01LU2', '-', 'Aditya Birla Sun Life Banking & PSU Debt Fund', 'Regular Plan', 'MONTHLY IDCW Payout', '112.4288', '21-Aug-2026']
        name, nav, date = parse_scheme_name_nav_date(scheme)
        self.assertEqual(name, 'Aditya Birla Sun Life Banking & PSU Debt Fund - Regular - MONTHLY IDCW Payout')


class TestSimplifyPlan(unittest.TestCase):
    def test_drops_word_plan(self):
        self.assertEqual(_simplify_plan('Direct Plan'), 'Direct')
        self.assertEqual(_simplify_plan('Regular Plan'), 'Regular')

    def test_leaves_plan_free_text_untouched(self):
        self.assertEqual(_simplify_plan('Direct'), 'Direct')


class TestSimplifyIdcwOption(unittest.TestCase):
    def test_non_idcw_option_untouched(self):
        self.assertEqual(_simplify_idcw_option('GROWTH'), 'GROWTH')
        self.assertEqual(_simplify_idcw_option('Bonus Option'), 'Bonus Option')
        self.assertEqual(_simplify_idcw_option('Cumulative'), 'Cumulative')

    def test_already_short_idcw_option_untouched(self):
        self.assertEqual(_simplify_idcw_option('Daily IDCW'), 'Daily IDCW')
        self.assertEqual(_simplify_idcw_option('QUARTERLY IDCW Payout'), 'QUARTERLY IDCW Payout')

    def test_bare_expansion_collapses_to_idcw(self):
        self.assertEqual(_simplify_idcw_option('Income Distribution cum Capital Withdrawal'), 'IDCW')
        self.assertEqual(_simplify_idcw_option('IDCW (Income Distribution CUM Capital Withdrawal)'), 'IDCW')

    def test_frequency_and_distribution_type_are_preserved(self):
        # These two differ only by option text and must stay distinguishable -
        # they're different scheme codes with different NAVs.
        self.assertEqual(
            _simplify_idcw_option('Monthly Payout of Income Distribution cum capital withdrawal option'),
            'Monthly Payout IDCW',
        )
        self.assertEqual(
            _simplify_idcw_option('Quarterly Income Distribution Cum Capital Withdrawal'),
            'Quarterly IDCW',
        )

    def test_qualifier_before_idcw_acronym_is_preserved(self):
        self.assertEqual(
            _simplify_idcw_option('Institutional IDCW (Income Distribution CUM Capital Withdrawal)'),
            'Institutional IDCW',
        )


class TestNameHasNewInfo(unittest.TestCase):
    def test_identical_name_has_no_new_info(self):
        self.assertFalse(name_has_new_info('Some Fund - Direct Plan - Growth', 'Some Fund - Direct Plan - Growth'))

    def test_reordered_and_recased_name_has_no_new_info(self):
        # Same words, different case/punctuation.
        self.assertFalse(name_has_new_info('kotak dividend yield fund direct growth', 'Kotak Dividend Yield Fund - Direct - Growth'))

    def test_shorter_reconstructed_name_has_no_new_info(self):
        # AMFI returns blank plan/option for many legacy/closed schemes, which
        # would otherwise silently drop real detail from the stored name.
        old_name = 'Motilal Oswal Ultra Short Term Fund (MOFUSTF) -Direct Plan- Growth'
        new_name = 'Motilal Oswal Ultra Short Term Fund'
        self.assertFalse(name_has_new_info(old_name, new_name))

    def test_name_with_extra_words_has_new_info(self):
        old_name = 'Aditya Birla Sun Life Gold Fund-Growth'
        new_name = 'Aditya Birla Sun Life Gold Fund - Regular Plan - GROWTH'
        self.assertTrue(name_has_new_info(old_name, new_name))
