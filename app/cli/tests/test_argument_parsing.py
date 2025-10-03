"""
Comprehensive tests for CLI argument parsing and validation.

These tests verify:
- All command-line argument combinations
- Argument validation and error handling
- Default values and edge cases
- Help text and usage information
"""

import unittest
import tempfile
import os
import sys
import argparse
from unittest.mock import patch, MagicMock
from io import StringIO

# Add the CLI directory to the path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main


class TestArgumentParser(unittest.TestCase):
    """Test argument parsing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.parser = argparse.ArgumentParser(description="DST Calculator CLI - Drug Susceptibility Testing Calculator")
        self.parser.add_argument('--drug-data', type=str, help='Path to input file with drug data (CSV format)')
        self.parser.add_argument('--single-test-input', type=str, help='Path to single test input CSV for one-time automated run')
        self.parser.add_argument('--test-output', type=str, help='Path to test output/error log file')
        self.parser.add_argument('--session-name', type=str, help='Session name for logging (default: interactive prompt)')
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_test_file(self, filename, content="test content"):
        """Helper to create test files."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath
    
    def test_no_arguments(self):
        """Test parsing with no arguments (interactive mode)."""
        args = self.parser.parse_args([])
        
        self.assertIsNone(args.drug_data)
        self.assertIsNone(args.single_test_input)
        self.assertIsNone(args.test_output)
        self.assertIsNone(args.session_name)
    
    def test_drug_data_argument(self):
        """Test --drug-data argument."""
        test_file = self.create_test_file("drugs.csv")
        args = self.parser.parse_args(['--drug-data', test_file])
        
        self.assertEqual(args.drug_data, test_file)
        self.assertIsNone(args.single_test_input)
    
    def test_single_test_input_argument(self):
        """Test --single-test-input argument."""
        test_file = self.create_test_file("test.csv")
        args = self.parser.parse_args(['--single-test-input', test_file])
        
        self.assertEqual(args.single_test_input, test_file)
        self.assertIsNone(args.drug_data)
    
    def test_test_output_argument(self):
        """Test --test-output argument."""
        output_file = os.path.join(self.temp_dir, "output.log")
        args = self.parser.parse_args(['--test-output', output_file])
        
        self.assertEqual(args.test_output, output_file)
    
    def test_session_name_argument(self):
        """Test --session-name argument."""
        args = self.parser.parse_args(['--session-name', 'test_session'])
        
        self.assertEqual(args.session_name, 'test_session')
    
    def test_combined_arguments(self):
        """Test multiple arguments combined."""
        drug_file = self.create_test_file("drugs.csv")
        test_file = self.create_test_file("test.csv")
        output_file = os.path.join(self.temp_dir, "output.log")
        
        args = self.parser.parse_args([
            '--drug-data', drug_file,
            '--single-test-input', test_file,
            '--test-output', output_file,
            '--session-name', 'combined_test'
        ])
        
        self.assertEqual(args.drug_data, drug_file)
        self.assertEqual(args.single_test_input, test_file)
        self.assertEqual(args.test_output, output_file)
        self.assertEqual(args.session_name, 'combined_test')
    
    def test_argument_order_independence(self):
        """Test that argument order doesn't matter."""
        drug_file = self.create_test_file("drugs.csv")
        test_file = self.create_test_file("test.csv")
        
        args1 = self.parser.parse_args(['--drug-data', drug_file, '--single-test-input', test_file])
        args2 = self.parser.parse_args(['--single-test-input', test_file, '--drug-data', drug_file])
        
        self.assertEqual(args1.drug_data, args2.drug_data)
        self.assertEqual(args1.single_test_input, args2.single_test_input)
    
    def test_short_arguments_if_available(self):
        """Test that short argument forms are handled if implemented."""
        # Note: The current parser doesn't define short forms, but this tests the concept
        with self.assertRaises(SystemExit):
            # Should fail since short forms aren't defined
            self.parser.parse_args(['-d', 'test.csv'])
    
    def test_help_argument(self):
        """Test --help argument."""
        with self.assertRaises(SystemExit):
            self.parser.parse_args(['--help'])
    
    def test_unknown_argument(self):
        """Test handling of unknown arguments."""
        with self.assertRaises(SystemExit):
            self.parser.parse_args(['--unknown-arg', 'value'])
    
    def test_argument_without_value(self):
        """Test arguments that require values but don't get them."""
        with self.assertRaises(SystemExit):
            self.parser.parse_args(['--drug-data'])
    
    def test_empty_string_arguments(self):
        """Test arguments with empty string values."""
        args = self.parser.parse_args(['--session-name', ''])
        self.assertEqual(args.session_name, '')
    
    def test_special_characters_in_arguments(self):
        """Test arguments with special characters."""
        special_name = "test-session_123!@#"
        args = self.parser.parse_args(['--session-name', special_name])
        self.assertEqual(args.session_name, special_name)


class TestArgumentValidation(unittest.TestCase):
    """Test validation of parsed arguments."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_test_file(self, filename, content="test content"):
        """Helper to create test files."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath
    
    @patch('main.print_header')
    @patch('main.print_help_text')
    @patch('main.print_success')
    @patch('main.print_step')
    @patch('main.print_error')
    def test_nonexistent_drug_data_file(self, mock_error, mock_step, mock_success, mock_help, mock_header):
        """Test handling of nonexistent drug data file."""
        with patch('sys.argv', ['main.py', '--drug-data', '/nonexistent/file.csv']):
            with patch('main.setup_logger', return_value=MagicMock()):
                with self.assertRaises(SystemExit):
                    main.main()
    
    @patch('main.print_header')
    @patch('main.print_help_text') 
    @patch('main.print_success')
    @patch('main.print_step')
    def test_nonexistent_test_input_file(self, mock_step, mock_success, mock_help, mock_header):
        """Test handling of nonexistent test input file."""
        with patch('sys.argv', ['main.py', '--single-test-input', '/nonexistent/test.csv', '--session-name', 'test']):
            with patch('main.setup_logger', return_value=MagicMock()):
                with patch('main.load_drug_data', return_value=MagicMock()):
                    with self.assertRaises(SystemExit):
                        main.main()
    
    @patch('main.print_header')
    @patch('main.print_help_text')
    @patch('main.print_success')
    @patch('main.print_step')
    @patch('main.print_error')
    def test_valid_drug_data_file(self, mock_error, mock_step, mock_success, mock_help, mock_header):
        """Test handling of valid drug data file."""
        drug_file = self.create_test_file("drugs.csv", "Drug,OrgMolecular_Weight,Diluent,Critical_Concentration\nTest,100.0,Water,1.0")
        
        with patch('sys.argv', ['main.py', '--drug-data', drug_file, '--session-name', 'test']):
            with patch('main.setup_logger', return_value=MagicMock()):
                with patch('main.run_calculation') as mock_calc:
                    with patch('main.pd.read_csv', return_value=MagicMock()):
                        main.main()
                        mock_calc.assert_called_once()
    
    def test_session_name_cleaning(self):
        """Test that session names are properly cleaned."""
        invalid_name = "test<>session|name?"
        cleaned = main.clean_filename(invalid_name)
        
        # Should not contain invalid characters
        self.assertNotIn('<', cleaned)
        self.assertNotIn('>', cleaned)
        self.assertNotIn('|', cleaned)
        self.assertNotIn('?', cleaned)
    
    def test_long_session_name(self):
        """Test handling of very long session names."""
        long_name = "a" * 1000
        cleaned = main.clean_filename(long_name)
        
        # Should still be valid (no length limit in current implementation)
        self.assertEqual(cleaned, long_name)
    
    def test_unicode_session_name(self):
        """Test handling of unicode characters in session names."""
        unicode_name = "test_セッション_名前"
        cleaned = main.clean_filename(unicode_name)
        
        # Unicode should be preserved
        self.assertEqual(cleaned, unicode_name)


class TestMainFunctionArgumentIntegration(unittest.TestCase):
    """Test integration between argument parsing and main function execution."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_test_file(self, filename, content="test content"):
        """Helper to create test files."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath
    
    @patch('main.load_drug_data')
    @patch('main.setup_logger')
    @patch('main.run_calculation')
    @patch('main.print_header')
    @patch('main.print_help_text')
    @patch('main.print_success')
    @patch('main.print_step')
    def test_interactive_mode_default(self, mock_step, mock_success, mock_help, mock_header, 
                                    mock_run_calc, mock_logger, mock_load_data):
        """Test that no arguments defaults to interactive mode."""
        mock_load_data.return_value = MagicMock()
        mock_logger.return_value = MagicMock()
        
        with patch('sys.argv', ['main.py']):
            with patch('builtins.input', return_value='test_session'):
                main.main()
        
        # Should call run_calculation with None test_case (interactive mode)
        mock_run_calc.assert_called_once()
        call_args = mock_run_calc.call_args[0]
        self.assertIsNone(call_args[1])  # test_case should be None
    
    @patch('main.load_drug_data')
    @patch('main.setup_logger')
    @patch('main.run_calculation')
    @patch('main.parse_input_file')
    @patch('main.print_header')
    @patch('main.print_help_text')
    @patch('main.print_success')
    @patch('main.print_step')
    def test_single_test_mode_execution(self, mock_step, mock_success, mock_help, mock_header,
                                       mock_parse, mock_run_calc, mock_logger, mock_load_data):
        """Test execution in single test mode."""
        test_file = self.create_test_file("test.csv", "1;log.txt;1,2,3;n;;;137.5;500;results.txt;50;10;final.txt")
        
        mock_load_data.return_value = MagicMock()
        mock_logger.return_value = MagicMock()
        mock_parse.return_value = [{'id': '1', 'selected_numerals': '1,2,3'}]
        
        with patch('sys.argv', ['main.py', '--single-test-input', test_file, '--session-name', 'test']):
            main.main()
        
        # Should call parse_input_file and run_calculation with test case
        mock_parse.assert_called_once_with(test_file)
        mock_run_calc.assert_called_once()
        call_args = mock_run_calc.call_args[0]
        self.assertIsNotNone(call_args[1])  # test_case should not be None
    
    @patch('main.setup_logger')
    @patch('main.run_calculation')
    @patch('main.pd.read_csv')
    @patch('main.print_header')
    @patch('main.print_help_text')
    @patch('main.print_success')
    @patch('main.print_step')
    def test_custom_drug_data_execution(self, mock_step, mock_success, mock_help, mock_header,
                                       mock_read_csv, mock_run_calc, mock_logger):
        """Test execution with custom drug data file."""
        drug_file = self.create_test_file("drugs.csv", "Drug,OrgMolecular_Weight\nTest,100.0")
        
        mock_logger.return_value = MagicMock()
        mock_read_csv.return_value = MagicMock()
        
        with patch('sys.argv', ['main.py', '--drug-data', drug_file, '--session-name', 'test']):
            main.main()
        
        # Should call pd.read_csv instead of load_drug_data
        mock_read_csv.assert_called_once_with(drug_file)
        mock_run_calc.assert_called_once()
    
    @patch('main.load_drug_data')
    @patch('main.setup_logger')
    @patch('main.run_calculation')
    @patch('main.parse_input_file')
    @patch('main.print_header')
    @patch('main.print_help_text')
    @patch('main.print_success')
    @patch('main.print_step')
    def test_test_output_file_creation(self, mock_step, mock_success, mock_help, mock_header,
                                      mock_parse, mock_run_calc, mock_logger, mock_load_data):
        """Test that test output file is created and used."""
        test_file = self.create_test_file("test.csv", "1;log.txt;1,2,3;n;;;137.5;500;results.txt;50;10;final.txt")
        output_file = os.path.join(self.temp_dir, "test_output.log")
        
        mock_load_data.return_value = MagicMock()
        mock_logger.return_value = MagicMock()
        mock_parse.return_value = [{'id': '1', 'selected_numerals': '1,2,3'}]
        
        with patch('sys.argv', ['main.py', '--single-test-input', test_file, 
                               '--test-output', output_file, '--session-name', 'test']):
            with patch('builtins.open', create=True) as mock_open:
                main.main()
        
        # Should attempt to open the output file for writing
        mock_open.assert_called()
    
    def test_invalid_argument_combination_graceful_handling(self):
        """Test that invalid argument combinations are handled gracefully."""
        # This tests the robustness of argument handling
        with patch('sys.argv', ['main.py', '--invalid-arg']):
            with self.assertRaises(SystemExit):
                # argparse should handle this and exit
                main.main()


class TestArgumentEdgeCases(unittest.TestCase):
    """Test edge cases and unusual argument scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_empty_argv(self):
        """Test handling of empty sys.argv (shouldn't happen but test robustness)."""
        parser = argparse.ArgumentParser()
        parser.add_argument('--test', type=str)
        
        # Empty argv should work (no arguments)
        args = parser.parse_args([])
        self.assertIsNone(args.test)
    
    def test_argument_with_spaces(self):
        """Test arguments containing spaces."""
        parser = argparse.ArgumentParser()
        parser.add_argument('--session-name', type=str)
        
        args = parser.parse_args(['--session-name', 'test session with spaces'])
        self.assertEqual(args.session_name, 'test session with spaces')
    
    def test_argument_with_quotes(self):
        """Test arguments containing quotes."""
        parser = argparse.ArgumentParser()
        parser.add_argument('--session-name', type=str)
        
        args = parser.parse_args(['--session-name', 'test "quoted" session'])
        self.assertEqual(args.session_name, 'test "quoted" session')
    
    def test_very_long_file_paths(self):
        """Test handling of very long file paths."""
        parser = argparse.ArgumentParser()
        parser.add_argument('--drug-data', type=str)
        
        long_path = os.path.join(self.temp_dir, "a" * 200, "very_long_filename.csv")
        args = parser.parse_args(['--drug-data', long_path])
        self.assertEqual(args.drug_data, long_path)
    
    def test_relative_vs_absolute_paths(self):
        """Test that both relative and absolute paths are handled correctly."""
        parser = argparse.ArgumentParser()
        parser.add_argument('--drug-data', type=str)
        
        # Relative path
        args1 = parser.parse_args(['--drug-data', './test.csv'])
        self.assertEqual(args1.drug_data, './test.csv')
        
        # Absolute path
        abs_path = os.path.abspath('./test.csv')
        args2 = parser.parse_args(['--drug-data', abs_path])
        self.assertEqual(args2.drug_data, abs_path)
    
    def test_numeric_session_names(self):
        """Test session names that are purely numeric."""
        cleaned = main.clean_filename("12345")
        self.assertEqual(cleaned, "12345")
    
    def test_mixed_alphanumeric_session_names(self):
        """Test session names with mixed alphanumeric characters."""
        cleaned = main.clean_filename("test123session456")
        self.assertEqual(cleaned, "test123session456")


if __name__ == '__main__':
    unittest.main()
