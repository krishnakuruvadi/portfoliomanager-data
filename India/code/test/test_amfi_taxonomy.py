import os
import sys
import json
import unittest
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from helpers.amfi_taxonomy import (
    apply_known_amfi_aliases,
    load_known_taxonomy,
    find_unapproved_taxonomy_rows,
)

HEADER = 'code,name,isin,isin2,fund_house,inception_date,end_date,amfi_fund_type,amfi_category,ms_name,ms_category,ms_investment_style,ms_id,kuvera_name,kuvera_fund_category,kuvera_code\n'


class TestApplyKnownAmfiAliases(unittest.TestCase):
    def test_corrects_known_drift(self):
        fund_type, fund_category = apply_known_amfi_aliases('Equity Schemes', 'Sectoral Fund')
        self.assertEqual(fund_type, 'Equity Scheme')
        self.assertEqual(fund_category, 'Sectoral/ Thematic')

    def test_leaves_unknown_pairs_unchanged(self):
        fund_type, fund_category = apply_known_amfi_aliases('Debt Scheme', 'Gilt Fund')
        self.assertEqual(fund_type, 'Debt Scheme')
        self.assertEqual(fund_category, 'Gilt Fund')


class TestLoadKnownTaxonomy(unittest.TestCase):
    def test_returns_nonempty_sets_including_current_values(self):
        known_types, known_categories = load_known_taxonomy()
        self.assertIn('Equity Scheme', known_types)
        self.assertIn('Debt Scheme', known_types)
        self.assertIn('Sectoral/ Thematic', known_categories)
        self.assertGreater(len(known_types), 0)
        self.assertGreater(len(known_categories), 0)


class TestFindUnapprovedTaxonomyRows(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.csv_path = os.path.join(self.temp_dir, 'mf.csv')

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def write_csv(self, *rows):
        with open(self.csv_path, 'w', newline='') as f:
            f.write(HEADER)
            for row in rows:
                f.write(row + '\n')

    def test_approved_values_pass(self):
        self.write_csv(
            '100001,Some Fund - Direct Plan - Growth,INF123456789,,Some Fund House,01-01-2020,,Equity Scheme,Large Cap Fund,,,,,,,'
        )
        self.assertEqual(find_unapproved_taxonomy_rows(self.csv_path), [])

    def test_blank_values_are_allowed(self):
        self.write_csv(
            '100001,Some Fund - Direct Plan - Growth,INF123456789,,Some Fund House,01-01-2020,,,,,,,,,,'
        )
        self.assertEqual(find_unapproved_taxonomy_rows(self.csv_path), [])

    def test_unapproved_fund_type_is_flagged(self):
        self.write_csv(
            '100001,Some Fund - Direct Plan - Growth,INF123456789,,Some Fund House,01-01-2020,,Totally New Type,Large Cap Fund,,,,,,,'
        )
        problems = find_unapproved_taxonomy_rows(self.csv_path)
        self.assertEqual(len(problems), 1)
        self.assertEqual(problems[0], (2, 'amfi_fund_type', 'Totally New Type'))

    def test_unapproved_category_is_flagged(self):
        self.write_csv(
            '100001,Some Fund - Direct Plan - Growth,INF123456789,,Some Fund House,01-01-2020,,Equity Scheme,Totally New Category,,,,,,,'
        )
        problems = find_unapproved_taxonomy_rows(self.csv_path)
        self.assertEqual(len(problems), 1)
        self.assertEqual(problems[0], (2, 'amfi_category', 'Totally New Category'))


if __name__ == '__main__':
    unittest.main()
