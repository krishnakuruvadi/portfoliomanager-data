import os
import sys
import unittest
from unittest.mock import patch

# Add parent directory to path to import update_mf
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from update_mf import review_data_changes
from helpers.mf_check import update_single_code_in_csv


class TestReviewDataChanges(unittest.TestCase):
    def test_update_single_code_in_csv_imports(self):
        self.assertTrue(callable(update_single_code_in_csv))

    def test_rejects_single_field_change(self):
        original = {
            '1': {
                'name': 'Old Name',
                'fund_house': 'Old House',
                'kuvera_name': '',
                'kuvera_code': '',
            }
        }
        updated = {
            '1': {
                'name': 'New Name',
                'fund_house': 'Old House',
                'kuvera_name': '',
                'kuvera_code': '',
            }
        }

        with patch('builtins.input', return_value='n'):
            with patch('update_mf.write_entries') as write_mock:
                result = review_data_changes(original, updated, 'test-phase')

        self.assertEqual(result['1']['name'], 'Old Name')
        write_mock.assert_called_once()

    def test_drops_new_entry_when_rejected(self):
        original = {}
        updated = {
            '2': {
                'name': 'New Fund',
                'fund_house': 'New House',
                'kuvera_name': '',
                'kuvera_code': '',
            }
        }

        with patch('builtins.input', return_value='n'):
            with patch('update_mf.write_entries') as write_mock:
                result = review_data_changes(original, updated, 'test-phase')

        self.assertNotIn('2', result)
        write_mock.assert_called_once()
