"""
Tests for CLI main functionality.

These tests verify the core CLI functionality including:
- Argument parsing
- File operations
- Input validation
- Error handling
- End-to-end workflows
"""

import unittest
import tempfile
import os
import sys
import io
from unittest.mock import patch, MagicMock, mock_open
import pandas as pd
from pathlib import Path

# Add the CLI directory to the path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main
from main import clean_filename, parse_input_file, setup_logger, run_calculation


class TestCleanFilename(unittest.TestCase):
    """Test filename cleaning functionality."""
    
    def test_clean_filename_basic(self):
        """Test basic filename cleaning."""
        self.assertEqual(clean_filename("test_file"), "test_file")
        self.assertEqual(clean_filename("Test File"), "Test File")
    
    def test_clean_filename_invalid_chars(self):
        """Test cleaning of invalid characters."""
        self.assertEqual(clean_filename("test<>file"), "test_file")
        self.assertEqual(clean_filename("test|file?"), "test_file")
        self.assertEqual(clean_filename("test*file"), "test_file")
    
    def test_clean_filename_multiple_underscores(self):
        """Test consolidation of multiple underscores."""
        self.assertEqual(clean_filename("test___file"), "test_file")
        self.assertEqual(clean_filename("test__<>__file"), "test_file")
    
    def test_clean_filename_edge_cases(self):
        """Test edge cases for filename cleaning."""
        self.assertEqual(clean_filename(""), "untitled")
        self.assertEqual(clean_filename(None), "untitled")
        self.assertEqual(clean_filename("___"), "untitled")
        self.assertEqual(clean_filename("  _test_  "), "test")
    
    def test_clean_filename_with_numbers(self):
        """Test filename cleaning with numbers."""
        self.assertEqual(clean_filename("test123"), "test123")
        self.assertEqual(clean_filename("123test"), "123test")


class TestParseInputFile(unittest.TestCase):
    """Test input file parsing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_test_file(self, content, filename="test.csv"):
        """Helper to create test files."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath
    
    def test_parse_input_file_with_header(self):
        """Test parsing file with proper header."""
        content = ";".join(main.EXPECTED_FIELDS) + "\n"
        content += "1;log1.txt;1,2,3;n;;;137.5,150.2,160.8;500.0;results1.txt;50.0;10;final1.txt\n"
        
        filepath = self.create_test_file(content)
        result = parse_input_file(filepath)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], '1')
        self.assertEqual(result[0]['selected_numerals'], '1,2,3')
    
    def test_parse_input_file_without_header(self):
        """Test parsing file without header."""
        content = "1;log1.txt;1,2,3;n;;;137.5,150.2,160.8;500.0;results1.txt;50.0;10;final1.txt\n"
        
        filepath = self.create_test_file(content)
        result = parse_input_file(filepath)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], '1')
        self.assertEqual(result[0]['selected_numerals'], '1,2,3')
    
    def test_parse_input_file_empty_lines(self):
        """Test parsing file with empty lines."""
        content = "1;log1.txt;1,2,3;n;;;137.5,150.2,160.8;500.0;results1.txt;50.0;10;final1.txt\n"
        content += "\n"  # Empty line
        content += ";;;;;;;;;;;;\n"  # Line with just semicolons
        
        filepath = self.create_test_file(content)
        result = parse_input_file(filepath)
        
        self.assertEqual(len(result), 1)  # Should skip empty lines
    
    def test_parse_input_file_nonexistent(self):
        """Test parsing nonexistent file."""
        with self.assertRaises(FileNotFoundError):
            parse_input_file("/nonexistent/file.csv")


class TestSetupLogger(unittest.TestCase):
    """Test logger setup functionality."""
    
    @patch('os.makedirs')
    @patch('logging.FileHandler')
    def test_setup_logger_default(self, mock_file_handler, mock_makedirs):
        """Test logger setup with default session name."""
        mock_handler = MagicMock()
        mock_file_handler.return_value = mock_handler
        
        logger = setup_logger()
        
        self.assertIsNotNone(logger)
        mock_makedirs.assert_called_once()
        mock_file_handler.assert_called_once()
        mock_handler.setLevel.assert_called_once()
    
    @patch('os.makedirs')
    @patch('logging.FileHandler')
    def test_setup_logger_custom_session(self, mock_file_handler, mock_makedirs):
        """Test logger setup with custom session name."""
        mock_handler = MagicMock()
        mock_file_handler.return_value = mock_handler
        
        logger = setup_logger("test_session")
        
        self.assertIsNotNone(logger)
        # Check that the custom session name is used in the file path
        call_args = mock_file_handler.call_args[0][0]
        self.assertIn("test_session", call_args)


class TestMainFunction(unittest.TestCase):
    """Test main function and argument parsing."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('main.load_drug_data')
    @patch('main.setup_logger')
    @patch('main.run_calculation')
    @patch('builtins.input', return_value='test_session')
    @patch('sys.argv', ['main.py'])
    def test_main_interactive_mode(self, mock_input, mock_run_calc, mock_logger, mock_load_data):
        """Test main function in interactive mode."""
        mock_load_data.return_value = pd.DataFrame()
        mock_logger.return_value = MagicMock()
        
        with patch('main.print_header'), patch('main.print_help_text'), \
             patch('main.print_success'), patch('main.print_step'):
            main.main()
        
        mock_load_data.assert_called_once()
        mock_run_calc.assert_called_once()
    
    @patch('main.load_drug_data')
    @patch('main.setup_logger')
    @patch('main.run_calculation')
    @patch('main.parse_input_file')
    def test_main_single_test_mode(self, mock_parse, mock_run_calc, mock_logger, mock_load_data):
        """Test main function with single test input."""
        # Create test input file
        test_file = os.path.join(self.temp_dir, "test.csv")
        with open(test_file, 'w') as f:
            f.write("1;log1.txt;1,2,3;n;;;137.5,150.2,160.8;500.0;results1.txt;50.0;10;final1.txt\n")
        
        mock_load_data.return_value = pd.DataFrame()
        mock_logger.return_value = MagicMock()
        mock_parse.return_value = [{'id': '1', 'selected_numerals': '1,2,3'}]
        
        with patch('sys.argv', ['main.py', '--single-test-input', test_file, '--session-name', 'test']):
            with patch('main.print_header'), patch('main.print_help_text'), \
                 patch('main.print_success'), patch('main.print_step'):
                main.main()
        
        mock_parse.assert_called_once_with(test_file)
        mock_run_calc.assert_called_once()
    
    @patch('main.pd.read_csv')
    @patch('main.setup_logger')
    @patch('main.run_calculation')
    @patch('builtins.input', return_value='test_session')
    def test_main_custom_drug_data(self, mock_input, mock_run_calc, mock_logger, mock_read_csv):
        """Test main function with custom drug data file."""
        drug_file = os.path.join(self.temp_dir, "drugs.csv")
        with open(drug_file, 'w') as f:
            f.write("Drug,OrgMolecular_Weight,Diluent,Critical_Concentration\n")
            f.write("TestDrug,100.0,Water,1.0\n")
        
        mock_read_csv.return_value = pd.DataFrame()
        mock_logger.return_value = MagicMock()
        
        with patch('sys.argv', ['main.py', '--drug-data', drug_file]):
            with patch('main.print_header'), patch('main.print_help_text'), \
                 patch('main.print_success'), patch('main.print_step'):
                main.main()
        
        mock_read_csv.assert_called_once_with(drug_file)
        mock_run_calc.assert_called_once()


class TestRunCalculation(unittest.TestCase):
    """Test the run_calculation function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_df = pd.DataFrame({
            'Drug': ['Drug1', 'Drug2'],
            'OrgMolecular_Weight': [100.0, 200.0],
            'Critical_Concentration': [1.0, 2.0],
            'Diluent': ['Water', 'DMSO'],
            'Est_DrugW(mg)': [45.0, 55.0],
            'Vol_WSol_ali(ml)': [2.5, 3.0],
            'Vol_Dil_Add(ml)': [7.5, 7.0], 
            'Vol_St_Left(ml)': [490.0, 490.0]
        })
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('main.select_drugs')
    @patch('main.purchased_weights')
    @patch('main.stock_volume')
    @patch('main.cal_potency')
    @patch('main.act_drugweight')
    @patch('main.cal_stockdil')
    @patch('main.mgit_tubes')
    @patch('main.cal_mgit_ws')
    @patch('builtins.input')
    def test_run_calculation_interactive(self, mock_input, mock_cal_mgit_ws, mock_mgit_tubes,
                                       mock_cal_stockdil, mock_act_drugweight, mock_cal_potency,
                                       mock_stock_volume, mock_purchased_weights, mock_select_drugs):
        """Test run_calculation in interactive mode."""
        mock_logger = MagicMock()
        mock_select_drugs.return_value = self.sample_df.copy()
        mock_input.side_effect = ['n', 'output_file', 'final_file']  # Responses for interactive prompts
        
        with patch('main.print_step'), patch('main.print_success'), \
             patch('builtins.print'), patch('os.makedirs'), \
             patch('builtins.open', mock_open()):
            run_calculation(self.sample_df, None, None, mock_logger)
        
        # Verify all calculation steps were called
        mock_select_drugs.assert_called_once()
        mock_purchased_weights.assert_called_once()
        mock_stock_volume.assert_called_once()
        mock_cal_potency.assert_called_once()
        mock_act_drugweight.assert_called_once()
        mock_cal_stockdil.assert_called_once()
        mock_mgit_tubes.assert_called_once()
        mock_cal_mgit_ws.assert_called_once()
    
    @patch('main.select_drugs')
    @patch('main.cal_potency')
    @patch('main.cal_stockdil')
    @patch('main.cal_mgit_ws')
    def test_run_calculation_test_mode(self, mock_cal_mgit_ws, mock_cal_stockdil,
                                     mock_cal_potency, mock_select_drugs):
        """Test run_calculation with test case input."""
        mock_logger = MagicMock()
        mock_select_drugs.return_value = self.sample_df.copy()
        
        test_case = {
            'selected_numerals': '1,2',
            'own_cc': 'n',
            'purch_mol_weights': '105.0,210.0',
            'stock_vol': '10.0,15.0',
            'weighed_drug': '8.5,12.5',
            'mgit_tubes': '5,3',
            'final_results_filename': 'test_final.txt'
        }
        
        with patch('main.print_step'), patch('main.print_success'), \
             patch('builtins.print'), patch('os.makedirs'), \
             patch('builtins.open', mock_open()):
            run_calculation(self.sample_df, test_case, None, mock_logger)
        
        # Verify calculation steps were called
        mock_select_drugs.assert_called_once()
        mock_cal_potency.assert_called_once()
        mock_cal_stockdil.assert_called_once()
        mock_cal_mgit_ws.assert_called_once()
    
    @patch('main.select_drugs')
    def test_run_calculation_drug_selection_failure(self, mock_select_drugs):
        """Test run_calculation when drug selection fails."""
        mock_logger = MagicMock()
        mock_select_drugs.return_value = None  # Simulate selection failure
        
        test_case = {'selected_numerals': 'invalid'}
        
        with patch('main.print_step'), patch('builtins.print'):
            run_calculation(self.sample_df, test_case, None, mock_logger)
        
        # Should log error and return early
        mock_logger.error.assert_called()


class TestIntegrationWithLibrary(unittest.TestCase):
    """Test integration between CLI and library functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_df = pd.DataFrame({
            'Drug': ['TestDrug1', 'TestDrug2'],
            'OrgMolecular_Weight': [100.0, 200.0],
            'Critical_Concentration': [1.0, 2.0],
            'Diluent': ['Water', 'DMSO']
        })
    
    def test_library_imports(self):
        """Test that library modules can be imported successfully."""
        # This tests the try-except import structure in main.py
        try:
            import drug_database
            import dst_calc  
            import supp_calc
            self.assertTrue(True)  # If we get here, imports worked
        except ImportError:
            # Fallback imports should work
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lib'))
            import drug_database
            import dst_calc
            import supp_calc
            self.assertTrue(True)
    
    @patch('main.load_drug_data')
    def test_load_drug_data_integration(self, mock_load_data):
        """Test integration with drug database loading."""
        mock_load_data.return_value = self.sample_df
        
        result = main.load_drug_data()
        
        self.assertIsInstance(result, pd.DataFrame)
        mock_load_data.assert_called_once()


class TestErrorHandling(unittest.TestCase):
    """Test error handling in CLI functions."""
    
    def test_main_keyboard_interrupt(self):
        """Test handling of keyboard interrupt."""
        with patch('sys.argv', ['main.py', '--session-name', 'test']):
            with patch('main.setup_logger', side_effect=KeyboardInterrupt):
                with self.assertRaises(SystemExit) as cm:
                    main.main()
                self.assertEqual(cm.exception.code, 0)
    
    def test_main_eof_error(self):
        """Test handling of EOF error."""
        with patch('sys.argv', ['main.py', '--session-name', 'test']):
            with patch('main.setup_logger', side_effect=EOFError):
                with self.assertRaises(SystemExit) as cm:
                    main.main()
                self.assertEqual(cm.exception.code, 0)
    
    def test_main_general_exception(self):
        """Test handling of general exceptions."""
        with patch('sys.argv', ['main.py', '--session-name', 'test']):
            with patch('main.setup_logger', side_effect=Exception("Test error")):
                with self.assertRaises(SystemExit) as cm:
                    main.main()
                self.assertEqual(cm.exception.code, 1)


if __name__ == '__main__':
    unittest.main()
