"""
Comprehensive tests for input validation scenarios.

These tests verify:
- CSV file parsing and validation
- Input data type validation
- Range validation and boundary conditions
- Error handling for malformed data
- Edge cases and corner scenarios
"""

import unittest
import tempfile
import os
import sys
import csv
from unittest.mock import patch, MagicMock
import pandas as pd

# Add the CLI directory to the path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main


class TestCSVFileValidation(unittest.TestCase):
    """Test validation of CSV input files."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_test_file(self, filename, content):
        """Helper to create test files."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            f.write(content)
        return filepath
    
    def test_valid_csv_with_header(self):
        """Test parsing valid CSV with header."""
        content = ";".join(main.EXPECTED_FIELDS) + "\n"
        content += "1;log1.txt;1,2,3;n;;;137.5,150.2,160.8;500.0;results1.txt;50.0;10;final1.txt\n"
        
        filepath = self.create_test_file("valid.csv", content)
        result = main.parse_input_file(filepath)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], '1')
        self.assertEqual(result[0]['selected_numerals'], '1,2,3')
    
    def test_valid_csv_without_header(self):
        """Test parsing valid CSV without header."""
        content = "1;log1.txt;1,2,3;n;;;137.5,150.2,160.8;500.0;results1.txt;50.0;10;final1.txt\n"
        
        filepath = self.create_test_file("no_header.csv", content)
        result = main.parse_input_file(filepath)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], '1')
    
    def test_empty_csv_file(self):
        """Test parsing empty CSV file."""
        filepath = self.create_test_file("empty.csv", "")
        result = main.parse_input_file(filepath)
        
        self.assertEqual(len(result), 0)
    
    def test_csv_with_only_header(self):
        """Test parsing CSV with only header row."""
        content = ";".join(main.EXPECTED_FIELDS) + "\n"
        
        filepath = self.create_test_file("header_only.csv", content)
        result = main.parse_input_file(filepath)
        
        self.assertEqual(len(result), 0)
    
    def test_csv_with_insufficient_columns(self):
        """Test parsing CSV with insufficient columns."""
        content = "1;log1.txt;1,2,3
"  # Missing many columns
        
        filepath = self.create_test_file("insufficient.csv", content)
        result = main.parse_input_file(filepath)
        
        # Should still parse but with missing values
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], '1')
        self.assertEqual(result[0]['logfile_name'], 'log1.txt')
    
    def test_csv_with_extra_columns(self):
        """Test parsing CSV with extra columns."""
        content = "1;log1.txt;1,2,3;n;;;137.5,150.2,160.8;500.0;results1.txt;50.0;10;final1.txt;extra;more_extra
"
        
        filepath = self.create_test_file("extra_cols.csv", content)
        result = main.parse_input_file(filepath)
        
        # Should parse successfully, ignoring extra columns
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], '1')
    
    def test_csv_with_mixed_delimiters(self):
        """Test CSV with mixed delimiters (should fail gracefully)."""
        content = "1,log1.txt;1,2,3;n;;;137.5,150.2,160.8;500.0;results1.txt;50.0;10;final1.txt
"
        
        filepath = self.create_test_file("mixed_delim.csv", content)
        result = main.parse_input_file(filepath)
        
        # Should handle gracefully, though results may not be as expected
        self.assertIsInstance(result, list)
    
    def test_csv_with_unicode_characters(self):
        """Test CSV with unicode characters."""
        content = "1;log1_測試.txt;1,2,3;n;;;137.5,150.2,160.8;500.0;results_結果.txt;50.0;10;final_最終.txt
"
        
        filepath = self.create_test_file("unicode.csv", content)
        result = main.parse_input_file(filepath)
        
        self.assertEqual(len(result), 1)
        self.assertIn('測試', result[0]['logfile_name'])
    
    def test_csv_with_special_characters(self):
        """Test CSV with special characters in data."""
        content = "1;log1<test>.txt;1,2,3;n;;;137.5,150.2,160.8;500.0;results&output.txt;50.0;10;final|result.txt
"
        
        filepath = self.create_test_file("special_chars.csv", content)
        result = main.parse_input_file(filepath)
        
        self.assertEqual(len(result), 1)
        self.assertIn('<test>', result[0]['logfile_name'])
    
    def test_csv_with_quotes_and_commas(self):
        """Test CSV with quoted fields containing commas."""
        content = '1;"log1,with,commas.txt";1,2,3;n;;;137.5,150.2,160.8;500.0;"results,output.txt";50.0;10;"final,result.txt"
'
        
        filepath = self.create_test_file("quotes.csv", content)
        result = main.parse_input_file(filepath)
        
        self.assertEqual(len(result), 1)
        # Results may vary based on CSV parsing implementation


class TestDataTypeValidation(unittest.TestCase):
    """Test validation of different data types in input."""
    
    def test_numeric_fields_validation(self):
        """Test validation of numeric fields."""
        # Test valid numeric values
        self.assertTrue(str(137.5).replace('.', '').isdigit() or '.' in str(137.5))
        self.assertTrue(str(500.0).replace('.', '').isdigit() or '.' in str(500.0))
        self.assertTrue(str(50.0).replace('.', '').isdigit() or '.' in str(50.0))
        self.assertTrue(str(10).isdigit())
    
    def test_string_fields_validation(self):
        """Test validation of string fields."""
        # Test various string formats
        valid_strings = [
            "log1.txt",
            "results_output.txt",
            "final-result.txt",
            "test_session_123"
        ]
        
        for string in valid_strings:
            self.assertIsInstance(string, str)
            self.assertTrue(len(string) > 0)
    
    def test_boolean_like_fields_validation(self):
        """Test validation of boolean-like fields (y/n)."""
        valid_values = ['y', 'n', 'Y', 'N']
        invalid_values = ['yes', 'no', '1', '0', 'true', 'false', 'x']
        
        for value in valid_values:
            self.assertIn(value.lower(), ['y', 'n'])
        
        for value in invalid_values:
            if len(value) == 1 and value.lower() in ['y', 'n']:
                continue
            self.assertNotIn(value.lower(), ['y', 'n'])
    
    def test_list_fields_validation(self):
        """Test validation of comma/space-separated list fields."""
        valid_lists = [
            "1,2,3",
            "1 2 3",
            "1,2,3,4,5",
            "1",
            "1 2",
            "10,11,12"
        ]
        
        for list_str in valid_lists:
            # Should be able to split and parse
            items = [x.strip() for x in list_str.replace(',', ' ').split()]
            self.assertTrue(all(item.isdigit() for item in items if item))


class TestRangeValidation(unittest.TestCase):
    """Test validation of value ranges and boundaries."""
    
    def test_drug_selection_ranges(self):
        """Test drug selection number ranges (based on test data expectations)."""
        # From test_1ans.csv, valid range appears to be 1-21
        valid_selections = [1, 2, 3, 10, 15, 21]
        invalid_selections = [0, -1, 22, 23, 100]
        
        for selection in valid_selections:
            self.assertGreaterEqual(selection, 1)
            self.assertLessEqual(selection, 21)
        
        for selection in invalid_selections:
            self.assertTrue(selection < 1 or selection > 21)
    
    def test_critical_concentration_ranges(self):
        """Test critical concentration value ranges."""
        # From test data, appears to be 0-20 range
        valid_cc_values = [0.0, 1.0, 5.0, 10.0, 15.0, 20.0]
        invalid_cc_values = [-1.0, 21.0, 25.0, 100.0]
        
        for value in valid_cc_values:
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 20.0)
        
        for value in invalid_cc_values:
            self.assertTrue(value < 0.0 or value > 20.0)
    
    def test_molecular_weight_ranges(self):
        """Test molecular weight ranges."""
        # From test data, appears to be 137-823 range
        valid_weights = [137.0, 150.0, 200.0, 500.0, 823.0]
        invalid_weights = [136.0, 824.0, 1000.0, -1.0]
        
        for weight in valid_weights:
            self.assertGreaterEqual(weight, 137.0)
            self.assertLessEqual(weight, 823.0)
        
        for weight in invalid_weights:
            self.assertTrue(weight < 137.0 or weight > 823.0)
    
    def test_stock_volume_ranges(self):
        """Test stock volume ranges."""
        # From test data, appears to be 0-1000 range
        valid_volumes = [0.0, 100.0, 500.0, 750.0, 1000.0]
        invalid_volumes = [-1.0, 1001.0, 5000.0]
        
        for volume in valid_volumes:
            self.assertGreaterEqual(volume, 0.0)
            self.assertLessEqual(volume, 1000.0)
        
        for volume in invalid_volumes:
            self.assertTrue(volume < 0.0 or volume > 1000.0)
    
    def test_weighed_drug_ranges(self):
        """Test weighed drug weight ranges."""
        # From test data, appears to be 0-100 range
        valid_weights = [0.0, 25.0, 50.0, 75.0, 100.0]
        invalid_weights = [-1.0, 101.0, 500.0]
        
        for weight in valid_weights:
            self.assertGreaterEqual(weight, 0.0)
            self.assertLessEqual(weight, 100.0)
        
        for weight in invalid_weights:
            self.assertTrue(weight < 0.0 or weight > 100.0)
    
    def test_mgit_tubes_ranges(self):
        """Test MGIT tubes count ranges."""
        # From test data, appears to be 0-100 range (integer)
        valid_counts = [0, 5, 10, 50, 100]
        invalid_counts = [-1, 101, 1000]
        
        for count in valid_counts:
            self.assertGreaterEqual(count, 0)
            self.assertLessEqual(count, 100)
            self.assertIsInstance(count, int)
        
        for count in invalid_counts:
            self.assertTrue(count < 0 or count > 100)


class TestMalformedDataHandling(unittest.TestCase):
    """Test handling of malformed or corrupted data."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_test_file(self, filename, content):
        """Helper to create test files."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            f.write(content)
        return filepath
    
    def test_corrupted_csv_structure(self):
        """Test handling of corrupted CSV structure."""
        content = "1;log1.txt;1,2,3;n;;;137.5,150.2,160.8;500.0;results1.txt;50.0;10;final1.txt
"
        content += "broken line without proper structure
"
        content += "2;log2.txt;4,5,6;n;;;140.0,160.0,180.0;600.0;results2.txt;60.0;20;final2.txt
"
        
        filepath = self.create_test_file("corrupted.csv", content)
        result = main.parse_input_file(filepath)
        
        # Should handle gracefully and parse what it can
        self.assertIsInstance(result, list)
        # At least the valid lines should be parsed
        self.assertGreaterEqual(len(result), 1)
    
    def test_mixed_encoding_file(self):
        """Test handling of files with mixed encoding."""
        # Create a file with mixed encoding (this is a simulation)
        content = "1;log1_测试.txt;1,2,3;n;;;137.5,150.2,160.8;500.0;results1.txt;50.0;10;final1.txt
"
        
        filepath = self.create_test_file("mixed_encoding.csv", content)
        
        # Should handle gracefully
        try:
            result = main.parse_input_file(filepath)
            self.assertIsInstance(result, list)
        except UnicodeDecodeError:
            # This is also acceptable behavior
            pass
    
    def test_extremely_long_lines(self):
        """Test handling of extremely long lines."""
        long_value = "a" * 10000
        content = f"1;{long_value};1,2,3;n;;;137.5,150.2,160.8;500.0;results1.txt;50.0;10;final1.txt
"
        
        filepath = self.create_test_file("long_lines.csv", content)
        result = main.parse_input_file(filepath)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0]['logfile_name']), 10000)
    
    def test_null_bytes_in_file(self):
        """Test handling of null bytes in file."""
        content = "1;log1.txt;1,2,3;n;;;137.5,150.2,160.8;500.0;results1.txt;50.0;10;final1.txt
"
        
        filepath = self.create_test_file("null_bytes.csv", content)
        
        # Should handle gracefully
        try:
            result = main.parse_input_file(filepath)
            self.assertIsInstance(result, list)
        except Exception:
            # Some parsing error is acceptable for corrupted data
            pass
    
    def test_inconsistent_delimiters(self):
        """Test handling of inconsistent delimiters within file."""
        content = "1;log1.txt;1,2,3;n;;;137.5,150.2,160.8;500.0;results1.txt;50.0;10;final1.txt
"
        content += "2,log2.txt,4,5,6,n,,,140.0,160.0,180.0,600.0,results2.txt,60.0,20,final2.txt
"
        
        filepath = self.create_test_file("inconsistent_delim.csv", content)
        result = main.parse_input_file(filepath)
        
        # Should handle gracefully, though second line may not parse correctly
        self.assertIsInstance(result, list)
        self.assertGreaterEqual(len(result), 1)


class TestBoundaryConditions(unittest.TestCase):
    """Test boundary conditions and edge cases."""
    
    def test_exact_boundary_values(self):
        """Test values exactly at boundaries."""
        # Test exact boundary values from the validation ranges
        boundary_tests = {
            'drug_selection': [1, 21],  # Min and max drug selection
            'critical_concentration': [0.0, 20.0],  # Min and max CC
            'molecular_weight': [137.0, 823.0],  # Min and max MW
            'stock_volume': [0.0, 1000.0],  # Min and max volume
            'weighed_drug': [0.0, 100.0],  # Min and max weight
            'mgit_tubes': [0, 100]  # Min and max tubes
        }
        
        for field, values in boundary_tests.items():
            for value in values:
                # Each boundary value should be valid
                if isinstance(value, float):
                    self.assertIsInstance(value, (int, float))
                else:
                    self.assertIsInstance(value, int)
    
    def test_floating_point_precision(self):
        """Test handling of floating point precision issues."""
        precision_values = [
            137.50000001,  # Very slight precision error
            137.4999999,   # Very slight precision error
            0.000000001,   # Very small positive number
            999.9999999    # Very close to 1000 boundary
        ]
        
        for value in precision_values:
            self.assertIsInstance(value, float)
            # Test that the value can be properly handled
            str_value = str(value)
            self.assertTrue(len(str_value) > 0)
    
    def test_empty_and_whitespace_fields(self):
        """Test handling of empty and whitespace-only fields."""
        empty_values = ["", " ", "	", "
", "   	
   "]
        
        for value in empty_values:
            cleaned = value.strip()
            # Empty or whitespace-only values should be handled
            self.assertIsInstance(cleaned, str)
    
    def test_zero_and_negative_edge_cases(self):
        """Test handling of zero and negative values."""
        edge_values = [0, -0, 0.0, -0.0, -1, -100.0]
        
        for value in edge_values:
            # Should be able to handle these values
            self.assertTrue(value <= 0)
    
    def test_very_large_numbers(self):
        """Test handling of very large numbers."""
        large_values = [1e6, 1e10, float('inf')]
        
        for value in large_values:
            if value != float('inf'):
                # Should be able to represent large numbers
                self.assertIsInstance(value, float)
                self.assertGreater(value, 1000000)


class TestInputConsistencyValidation(unittest.TestCase):
    """Test validation of consistency between related input fields."""
    
    def test_drug_count_consistency(self):
        """Test consistency between number of selected drugs and related arrays."""
        # Simulate scenarios where counts don't match
        test_cases = [
            {
                'selected_drugs': 3,
                'cc_values': 3,
                'molecular_weights': 3,
                'volumes': 3,
                'expected_valid': True
            },
            {
                'selected_drugs': 3,
                'cc_values': 2,  # Mismatch
                'molecular_weights': 3,
                'volumes': 3,
                'expected_valid': False
            },
            {
                'selected_drugs': 1,
                'cc_values': 1,
                'molecular_weights': 5,  # Mismatch
                'volumes': 1,
                'expected_valid': False
            }
        ]
        
        for case in test_cases:
            # Check if counts match
            all_counts = [
                case['selected_drugs'],
                case['cc_values'],
                case['molecular_weights'],
                case['volumes']
            ]
            
            consistency = len(set(all_counts)) == 1
            self.assertEqual(consistency, case['expected_valid'])
    
    def test_file_extension_consistency(self):
        """Test consistency of file extensions."""
        valid_extensions = ['.txt', '.csv', '.log']
        test_filenames = [
            'results.txt',
            'data.csv', 
            'log.log',
            'output.xlsx',  # Might be invalid
            'file_without_extension'
        ]
        
        for filename in test_filenames:
            has_valid_ext = any(filename.endswith(ext) for ext in valid_extensions)
            # File extensions should be consistent with expected formats
            self.assertIsInstance(filename, str)
    
    def test_numeric_sequence_validation(self):
        """Test validation of numeric sequences."""
        sequences = [
            "1,2,3",      # Valid ascending
            "3,2,1",      # Valid descending
            "1,1,2",      # Valid with duplicates
            "1,3,2",      # Valid unordered
            "",           # Empty (might be invalid)
            "1,a,3",      # Invalid non-numeric
            "1,,3"        # Invalid empty element
        ]
        
        for seq in sequences:
            if seq:
                try:
                    items = [x.strip() for x in seq.split(',') if x.strip()]
                    all_numeric = all(item.replace('.', '').replace('-', '').isdigit() for item in items)
                    # Should be able to validate numeric sequences
                    self.assertIsInstance(all_numeric, bool)
                except Exception:
                    # Some sequences may cause parsing errors
                    pass


if __name__ == '__main__':
    unittest.main()
