import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers.verify_index_returns import find_unexpected, main


class TestVerifyIndexReturns(unittest.TestCase):
    def test_all_expected(self):
        returns = {'trailing_ret': [{'name': 'A'}], 'as_on': '2026-11-15'}
        self.assertEqual(find_unexpected(returns, ['A', 'B']), {})

    def test_new_index_flagged_per_section(self):
        returns = {'trailing_ret': [{'name': 'A'}, {'name': 'C'}], 'monthly_ret': [{'name': 'C'}]}
        self.assertEqual(find_unexpected(returns, ['A']),
                         {'trailing_ret': ['C'], 'monthly_ret': ['C']})

    def test_main_exit_codes(self):
        d = tempfile.mkdtemp()
        returns = os.path.join(d, 'r.json')
        expected = os.path.join(d, 'e.json')
        json.dump(['A'], open(expected, 'w'))
        json.dump({'trailing_ret': [{'name': 'A'}]}, open(returns, 'w'))
        self.assertEqual(main(returns, expected), 0)
        json.dump({'trailing_ret': [{'name': 'A'}, {'name': 'B'}]}, open(returns, 'w'))
        self.assertEqual(main(returns, expected), 1)

    def test_repo_file_is_clean(self):
        self.assertEqual(main(), 0)


if __name__ == '__main__':
    unittest.main()
