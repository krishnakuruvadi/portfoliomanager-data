import os
import sys
import unittest
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from helpers.mf_entry import get_mf_entries, find_malformed_rows, find_invalid_field_rows

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


class TestFindInvalidFieldRows(unittest.TestCase):
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

    def problem_fields(self):
        return [field for _, field, _ in find_invalid_field_rows(self.csv_path)]

    def test_clean_row_has_no_problems(self):
        self.write_csv(
            '100001,Some Fund - Direct Plan - Growth,INF123456789,,Some Fund House,01-01-2020,,Equity Scheme,Large Cap Fund,,,,,,,'
        )
        self.assertEqual(find_invalid_field_rows(self.csv_path), [])

    def test_dash_isin_placeholder_is_not_flagged(self):
        self.write_csv(
            '100001,Some Fund - Direct Plan - Growth,-,-,Some Fund House,01-01-2020,,Equity Scheme,Large Cap Fund,,,,,,,'
        )
        self.assertEqual(find_invalid_field_rows(self.csv_path), [])

    def test_complete_kuvera_mapping_is_not_flagged(self):
        self.write_csv(
            '100001,Some Fund - Direct Plan - Growth,INF123456789,,Some Fund House,01-01-2020,,Equity Scheme,Large Cap Fund,,,,,Some Fund Growth Direct Plan,Large Cap Fund,SF-GR'
        )
        self.assertEqual(find_invalid_field_rows(self.csv_path), [])

    def test_non_numeric_code_is_flagged(self):
        self.write_csv(
            'ABC123,Some Fund - Direct Plan - Growth,INF123456789,,Some Fund House,01-01-2020,,Equity Scheme,Large Cap Fund,,,,,,,'
        )
        self.assertIn('code', self.problem_fields())

    def test_blank_name_is_flagged(self):
        self.write_csv(
            '100001,,INF123456789,,Some Fund House,01-01-2020,,Equity Scheme,Large Cap Fund,,,,,,,'
        )
        self.assertIn('name', self.problem_fields())

    def test_invalid_isin_format_is_flagged(self):
        self.write_csv(
            '100001,Some Fund - Direct Plan - Growth,NOTANISIN,,Some Fund House,01-01-2020,,Equity Scheme,Large Cap Fund,,,,,,,'
        )
        self.assertIn('isin', self.problem_fields())

    def test_duplicate_isin_and_isin2_is_flagged(self):
        self.write_csv(
            '100001,Some Fund - Direct Plan - Growth,INF123456789,INF123456789,Some Fund House,01-01-2020,,Equity Scheme,Large Cap Fund,,,,,,,'
        )
        self.assertIn('isin2', self.problem_fields())

    def test_invalid_inception_date_is_flagged(self):
        self.write_csv(
            '100001,Some Fund - Direct Plan - Growth,INF123456789,,Some Fund House,31-02-2020,,Equity Scheme,Large Cap Fund,,,,,,,'
        )
        self.assertIn('inception_date', self.problem_fields())

    def test_end_date_before_inception_date_is_flagged(self):
        self.write_csv(
            '100001,Some Fund - Direct Plan - Growth,INF123456789,,Some Fund House,01-01-2020,01-01-2019,Equity Scheme,Large Cap Fund,,,,,,,'
        )
        self.assertIn('end_date', self.problem_fields())

    def test_partial_kuvera_mapping_is_flagged(self):
        self.write_csv(
            '100001,Some Fund - Direct Plan - Growth,INF123456789,,Some Fund House,01-01-2020,,Equity Scheme,Large Cap Fund,,,,,Some Fund Growth Direct Plan,,'
        )
        problems = find_invalid_field_rows(self.csv_path)
        self.assertEqual(len(problems), 1)
        self.assertIn('kuvera', problems[0][1])

    def test_real_mf_csv_has_no_invalid_fields(self):
        from helpers.mf_entry import get_path_to_csv
        problems = find_invalid_field_rows(get_path_to_csv())
        self.assertEqual(problems, [])


if __name__ == '__main__':
    unittest.main()
