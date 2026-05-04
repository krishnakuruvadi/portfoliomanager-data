import unittest
import json
import csv
import tempfile
import os
import sys
from pathlib import Path

# Add parent directory to path to import helpers
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers.verify_file_content import verify_json_file, verify_csv_file, main


class TestVerifyJsonFile(unittest.TestCase):
    """Tests for verify_json_file function"""
    
    def setUp(self):
        """Create temporary directory for test files"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_valid_json_file(self):
        """Test verification of a valid JSON file"""
        json_file = os.path.join(self.temp_dir, "test.json")
        with open(json_file, 'w') as f:
            json.dump({"key": "value", "number": 42}, f)
        
        is_valid, message = verify_json_file(json_file)
        self.assertTrue(is_valid)
        self.assertIn("Valid JSON", message)
    
    def test_invalid_json_file(self):
        """Test verification of an invalid JSON file"""
        json_file = os.path.join(self.temp_dir, "invalid.json")
        with open(json_file, 'w') as f:
            f.write("{ invalid json }")
        
        is_valid, message = verify_json_file(json_file)
        self.assertFalse(is_valid)
        self.assertIn("Invalid JSON", message)
    
    def test_nonexistent_json_file(self):
        """Test verification of a non-existent JSON file"""
        json_file = os.path.join(self.temp_dir, "nonexistent.json")
        
        is_valid, message = verify_json_file(json_file)
        self.assertFalse(is_valid)
        self.assertIn("File not found", message)
    
    def test_empty_json_file(self):
        """Test verification of an empty JSON file"""
        json_file = os.path.join(self.temp_dir, "empty.json")
        with open(json_file, 'w') as f:
            f.write("")
        
        is_valid, message = verify_json_file(json_file)
        self.assertFalse(is_valid)
        self.assertIn("Invalid JSON", message)
    
    def test_complex_json_file(self):
        """Test verification of a complex JSON file"""
        json_file = os.path.join(self.temp_dir, "complex.json")
        complex_data = {
            "users": [
                {"id": 1, "name": "Alice", "active": True},
                {"id": 2, "name": "Bob", "active": False}
            ],
            "metadata": {
                "version": "1.0",
                "timestamp": "2026-05-03"
            }
        }
        with open(json_file, 'w') as f:
            json.dump(complex_data, f)
        
        is_valid, message = verify_json_file(json_file)
        self.assertTrue(is_valid)
        self.assertIn("Valid JSON", message)


class TestVerifyCsvFile(unittest.TestCase):
    """Tests for verify_csv_file function"""
    
    def setUp(self):
        """Create temporary directory for test files"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_valid_csv_file(self):
        """Test verification of a valid CSV file"""
        csv_file = os.path.join(self.temp_dir, "test.csv")
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Age", "City"])
            writer.writerow(["Alice", "30", "New York"])
            writer.writerow(["Bob", "25", "Los Angeles"])
        
        is_valid, message = verify_csv_file(csv_file)
        self.assertTrue(is_valid)
        self.assertIn("Valid CSV", message)
        self.assertIn("rows", message)
    
    def test_csv_file_row_count(self):
        """Test that CSV row count is reported correctly"""
        csv_file = os.path.join(self.temp_dir, "count.csv")
        num_rows = 5
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Header1", "Header2"])
            for i in range(num_rows - 1):
                writer.writerow([f"Value{i}", f"Data{i}"])
        
        is_valid, message = verify_csv_file(csv_file)
        self.assertTrue(is_valid)
        self.assertIn(f"{num_rows} rows", message)
    
    def test_empty_csv_file(self):
        """Test verification of an empty CSV file"""
        csv_file = os.path.join(self.temp_dir, "empty.csv")
        with open(csv_file, 'w') as f:
            f.write("")
        
        is_valid, message = verify_csv_file(csv_file)
        self.assertFalse(is_valid)
        self.assertIn("Invalid CSV", message)
    
    def test_nonexistent_csv_file(self):
        """Test verification of a non-existent CSV file"""
        csv_file = os.path.join(self.temp_dir, "nonexistent.csv")
        
        is_valid, message = verify_csv_file(csv_file)
        self.assertFalse(is_valid)
        self.assertIn("File not found", message)
    
    def test_csv_file_with_semicolon_delimiter(self):
        """Test verification of CSV file with semicolon delimiter"""
        csv_file = os.path.join(self.temp_dir, "semicolon.csv")
        with open(csv_file, 'w') as f:
            f.write("Name;Age;City\n")
            f.write("Alice;30;New York\n")
            f.write("Bob;25;Los Angeles\n")
        
        is_valid, message = verify_csv_file(csv_file)
        self.assertTrue(is_valid)
        self.assertIn("Valid CSV", message)


class TestMainFunction(unittest.TestCase):
    """Tests for main function"""
    
    def setUp(self):
        """Create temporary directory for test files"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    def tearDown(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_main_returns_dict(self):
        """Test that main function returns a dictionary"""
        results = main(self.temp_dir)
        self.assertIsInstance(results, dict)
        self.assertIn("json_results", results)
        self.assertIn("csv_results", results)
        self.assertIn("summary", results)
    
    def test_main_summary_structure(self):
        """Test that summary has correct structure"""
        results = main(self.temp_dir)
        summary = results["summary"]
        
        self.assertIn("json", summary)
        self.assertIn("csv", summary)
        self.assertIn("overall", summary)
        
        # Check json summary
        self.assertIn("total", summary["json"])
        self.assertIn("valid", summary["json"])
        self.assertIn("invalid", summary["json"])
        
        # Check csv summary
        self.assertIn("total", summary["csv"])
        self.assertIn("valid", summary["csv"])
        self.assertIn("invalid", summary["csv"])
    
    def test_main_with_test_files(self):
        """Test main function with actual test files"""
        # Create test files
        json_file = os.path.join(self.temp_dir, "test.json")
        with open(json_file, 'w') as f:
            json.dump({"test": "data"}, f)
        
        csv_file = os.path.join(self.temp_dir, "test.csv")
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Col1", "Col2"])
            writer.writerow(["Val1", "Val2"])
        
        results = main(self.temp_dir)
        
        # Verify results
        self.assertEqual(results["summary"]["json"]["total"], 1)
        self.assertEqual(results["summary"]["json"]["valid"], 1)
        self.assertEqual(results["summary"]["csv"]["total"], 1)
        self.assertEqual(results["summary"]["csv"]["valid"], 1)


if __name__ == "__main__":
    unittest.main()
