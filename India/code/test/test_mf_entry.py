import os
import sys
import unittest
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from helpers.mf_entry import get_mf_entries, find_malformed_rows

HEADER = 'code,name,isin,isin2,fund_house,inception_date,end_date,amfi_fund_type,amfi_category,ms_name,ms_category,ms_investment_style,ms_id,kuvera_name,kuvera_fund_category,kuvera_code\n'


class TestFindMalformedRows(unittest.TestCase):
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

    def test_clean_file_has_no_problems(self):
        self.write_csv(
            '100001,Some Fund - Direct Plan - Growth,INF123456789,,Some Fund House,01-01-2020,,Equity Scheme,Large Cap Fund,,,,,,,'
        )
        self.assertEqual(find_malformed_rows(self.csv_path), [])

    def test_dash_isin_placeholder_is_not_flagged(self):
        self.write_csv(
            '100001,Some Fund - Direct Plan - Growth,-,INF123456789,Some Fund House,01-01-2020,,Equity Scheme,Large Cap Fund,,,,,,,'
        )
        self.assertEqual(find_malformed_rows(self.csv_path), [])

    def test_unquoted_comma_in_name_is_flagged(self):
        self.write_csv(
            '151406,PGIM India Fund - Direct Plan, IDCW Option, IDCW Option,INF663L01X39,PGIM India Mutual Fund,27-02-2023,,Other Scheme,Index Funds,Index Funds,,,,,,'
        )
        problems = find_malformed_rows(self.csv_path)
        self.assertEqual(len(problems), 1)
        self.assertEqual(problems[0][0], 2)

    def test_get_mf_entries_raises_on_malformed_file(self):
        self.write_csv(
            '151406,PGIM India Fund - Direct Plan, IDCW Option, IDCW Option,INF663L01X39,PGIM India Mutual Fund,27-02-2023,,Other Scheme,Index Funds,Index Funds,,,,,,'
        )
        with self.assertRaises(ValueError):
            get_mf_entries(self.csv_path)

    def test_get_mf_entries_succeeds_on_clean_file(self):
        self.write_csv(
            '100001,Some Fund - Direct Plan - Growth,INF123456789,,Some Fund House,01-01-2020,,Equity Scheme,Large Cap Fund,,,,,,,'
        )
        data = get_mf_entries(self.csv_path)
        self.assertIn('100001', data)
        self.assertEqual(data['100001']['isin'], 'INF123456789')


if __name__ == '__main__':
    unittest.main()
