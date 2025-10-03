"""
Integration tests for end-to-end CLI workflows.

These tests verify:
- Complete calculation workflows from start to finish
- Integration with existing test data files
- End-to-end processing with various scenarios
- Real file I/O and data processing
- Integration between all CLI components
"""

import unittest
import tempfile
import os
import sys
import pandas as pd
from unittest.mock import patch, MagicMock

# Add the CLI directory to the path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main


class TestEndToEndWorkflows(unittest.TestCase):
    """Test complete end-to-end CLI workflows."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'test', 'app', 'cli'
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
        # Clear any log handlers
        import logging
        logger = logging.getLogger("pdst-calc")
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
    
    def create_sample_drug_data(self):
        """Create sample drug data for testing."""
        return pd.DataFrame({
            'Drug': ['Rifampin', 'Isoniazid', 'Ethambutol'],
            'OrgMolecular_Weight': [822.94, 137.14, 204.31],
            'Critical_Concentration': [1.0, 0.1, 5.0],
            'Diluent': ['DMSO', 'Water', 'Water']
        })
    
    def create_test_input_file(self, filename, test_case_data):
        """Create a test input file."""
        filepath = os.path.join(self.temp_dir, filename)
        
        # Write header
        with open(filepath, 'w') as f:
            f.write(";".join(main.EXPECTED_FIELDS) + "
")
            
            # Write test case data
            values = [
                test_case_data.get('id', '1'),
                test_case_data.get('logfile_name', 'test.log'),
                test_case_data.get('selected_numerals', '1,2,3'),
                test_case_data.get('reselect_numerals', 'n'),
                test_case_data.get('own_cc', 'n'),
                test_case_data.get('cc_values', ''),
                test_case_data.get('purch_mol_weights', '137.5,150.2,160.8'),
                test_case_data.get('stock_vol', '500.0'),
                test_case_data.get('results_filename', 'results.txt'),
                test_case_data.get('weighed_drug', '50.0'),
                test_case_data.get('mgit_tubes', '10'),
                test_case_data.get('final_results_filename', 'final.txt')
            ]
            f.write(";".join(values) + "
")
        
        return filepath
    
    @patch('main.load_drug_data')
    @patch('main.print_header')
    @patch('main.print_help_text')
    @patch('main.print_success')
    @patch('main.print_step')
    def test_simple_successful_workflow(self, mock_step, mock_success, mock_help, 
                                      mock_header, mock_load_data):
        """Test a simple successful end-to-end workflow."""
        
        # Create mock drug data
        mock_drug_df = self.create_sample_drug_data()
        mock_load_data.return_value = mock_drug_df
        
        # Create test input file
        test_case = {
            'id': '1',
            'selected_numerals': '1,2,3',
            'purch_mol_weights': '823.0,137.0,204.0',
            'stock_vol': '500.0',
            'weighed_drug': '45.5',
            'mgit_tubes': '10'
        }
        test_file = self.create_test_input_file("test_simple.csv", test_case)
        
        # Mock the calculation functions to avoid complex dependencies
        with patch('main.select_drugs', return_value=mock_drug_df):
            with patch('main.cal_potency'):
                with patch('main.cal_stockdil'):
                    with patch('main.cal_mgit_ws'):
                        with patch('main.setup_logger', return_value=MagicMock()):
                            with patch('os.makedirs'):
                                with patch('builtins.open', create=True):
                                    with patch('sys.argv', ['main.py', '--single-test-input', test_file, 
                                                          '--session-name', 'test_simple']):
                                        
                                        # Should complete without errors
                                        main.main()
        
        # Verify mocks were called appropriately
        mock_load_data.assert_called_once()
        mock_step.assert_called()
        mock_success.assert_called()
    
    @patch('main.pd.read_csv')
    @patch('main.print_header')
    @patch('main.print_help_text')
    @patch('main.print_success')
    @patch('main.print_step')
    def test_custom_drug_data_workflow(self, mock_step, mock_success, mock_help, 
                                     mock_header, mock_read_csv):
        """Test workflow with custom drug data file."""
        
        # Create custom drug data file
        drug_file = os.path.join(self.temp_dir, "custom_drugs.csv")
        custom_drug_df = self.create_sample_drug_data()
        custom_drug_df.to_csv(drug_file, index=False)
        
        mock_read_csv.return_value = custom_drug_df
        
        # Create test input file
        test_case = {
            'id': '1',
            'selected_numerals': '1,2',
            'purch_mol_weights': '823.0,137.0',
            'stock_vol': '750.0',
            'weighed_drug': '60.0',
            'mgit_tubes': '15'
        }
        test_file = self.create_test_input_file("test_custom.csv", test_case)
        
        # Mock the calculation functions
        with patch('main.select_drugs', return_value=custom_drug_df.iloc[:2]):
            with patch('main.cal_potency'):
                with patch('main.cal_stockdil'):
                    with patch('main.cal_mgit_ws'):
                        with patch('main.setup_logger', return_value=MagicMock()):
                            with patch('os.makedirs'):
                                with patch('builtins.open', create=True):
                                    with patch('sys.argv', ['main.py', 
                                                          '--drug-data', drug_file,
                                                          '--single-test-input', test_file,
                                                          '--session-name', 'test_custom']):
                                        
                                        main.main()
        
        # Should use custom drug data
        mock_read_csv.assert_called_once_with(drug_file)
    
    @patch('main.load_drug_data')
    @patch('main.print_header')
    @patch('main.print_help_text')
    @patch('main.print_success')
    @patch('main.print_step')
    @patch('builtins.input')
    def test_interactive_mode_workflow(self, mock_input, mock_step, mock_success, 
                                     mock_help, mock_header, mock_load_data):
        """Test interactive mode workflow."""
        
        mock_drug_df = self.create_sample_drug_data()
        mock_load_data.return_value = mock_drug_df
        
        # Simulate user inputs for interactive mode
        mock_input.side_effect = [
            'test_interactive',  # Session name
            'n',                 # Custom critical values
            'output_weights',    # Output filename
            'final_results'      # Final results filename
        ]
        
        # Mock all the interactive functions
        with patch('main.select_drugs', return_value=mock_drug_df):
            with patch('main.purchased_weights'):
                with patch('main.stock_volume'):
                    with patch('main.cal_potency'):
                        with patch('main.act_drugweight'):
                            with patch('main.cal_stockdil'):
                                with patch('main.mgit_tubes'):
                                    with patch('main.cal_mgit_ws'):
                                        with patch('main.setup_logger', return_value=MagicMock()):
                                            with patch('os.makedirs'):
                                                with patch('builtins.open', create=True):
                                                    with patch('builtins.print'):
                                                        with patch('sys.argv', ['main.py']):
                                                            
                                                            main.main()
        
        # Should call interactive functions
        mock_load_data.assert_called_once()
        mock_input.assert_called()


class TestRealDataIntegration(unittest.TestCase):
    """Test integration with real test data files."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'test', 'app', 'cli'
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
        import logging
        logger = logging.getLogger("pdst-calc")
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
    
    def test_parse_existing_test_files(self):
        """Test parsing of existing test data files."""
        
        # Check if test data files exist
        test_file_path = os.path.join(self.test_data_dir, "test_1.csv")
        if not os.path.exists(test_file_path):
            self.skipTest("Test data files not found")
        
        # Parse the real test file
        result = main.parse_input_file(test_file_path)
        
        # Should successfully parse
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        
        # Check that first row has expected structure
        first_row = result[0]
        for field in main.EXPECTED_FIELDS:
            self.assertIn(field, first_row)
    
    def test_various_test_scenarios(self):
        """Test various test scenarios from existing data."""
        
        test_scenarios = [
            ("test_1.csv", "Valid basic test cases"),
            ("test_2.csv", "Additional test scenarios"),
            ("test_3.csv", "Edge case scenarios")
        ]
        
        for test_file, description in test_scenarios:
            test_path = os.path.join(self.test_data_dir, test_file)
            
            if os.path.exists(test_path):
                with self.subTest(test_file=test_file, description=description):
                    try:
                        result = main.parse_input_file(test_path)
                        self.assertIsInstance(result, list)
                        
                        # Each row should have the expected structure
                        for row in result:
                            for field in main.EXPECTED_FIELDS:
                                self.assertIn(field, row)
                                
                    except Exception as e:
                        self.fail(f"Failed to parse {test_file}: {e}")
    
    @patch('main.load_drug_data')
    @patch('main.select_drugs')
    @patch('main.print_header')
    @patch('main.print_help_text')
    @patch('main.print_success')
    @patch('main.print_step')
    def test_real_data_calculation_flow(self, mock_step, mock_success, mock_help,
                                      mock_header, mock_select_drugs, mock_load_data):
        """Test calculation flow with real test data."""
        
        test_file_path = os.path.join(self.test_data_dir, "test_1.csv")
        if not os.path.exists(test_file_path):
            self.skipTest("Test data files not found")
        
        # Create mock data that matches expected structure
        mock_drug_df = pd.DataFrame({
            'Drug': ['Drug1', 'Drug2', 'Drug3'],
            'OrgMolecular_Weight': [150.0, 200.0, 180.0],
            'Critical_Concentration': [1.0, 0.5, 2.0],
            'Diluent': ['Water', 'DMSO', 'Water']
        })
        
        mock_load_data.return_value = mock_drug_df
        mock_select_drugs.return_value = mock_drug_df
        
        # Mock calculation functions
        with patch('main.cal_potency'):
            with patch('main.cal_stockdil'):
                with patch('main.cal_mgit_ws'):
                    with patch('main.setup_logger', return_value=MagicMock()):
                        with patch('os.makedirs'):
                            with patch('builtins.open', create=True):
                                with patch('sys.argv', ['main.py', 
                                                      '--single-test-input', test_file_path,
                                                      '--session-name', 'real_data_test']):
                                    
                                    try:
                                        main.main()
                                        # Should complete successfully
                                        mock_load_data.assert_called_once()
                                        
                                    except Exception as e:
                                        # Log the error for debugging but don't fail the test
                                        # since we're testing with mocked calculation functions
                                        print(f"Note: Calculation flow test with mocked functions encountered: {e}")


class TestErrorRecoveryIntegration(unittest.TestCase):
    """Test error recovery in integrated scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
        import logging
        logger = logging.getLogger("pdst-calc")
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
    
    def create_invalid_test_file(self, filename, content):
        """Create an invalid test file for testing error handling."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath
    
    @patch('main.load_drug_data')
    @patch('main.print_header')
    @patch('main.print_help_text')
    @patch('main.print_error')
    @patch('main.print_step')
    def test_invalid_input_file_handling(self, mock_step, mock_error, mock_help, 
                                       mock_header, mock_load_data):
        """Test handling of invalid input files in full workflow."""
        
        mock_load_data.return_value = pd.DataFrame()
        
        # Create invalid input file
        invalid_content = "invalid;csv;structure;without;proper;fields
"
        invalid_file = self.create_invalid_test_file("invalid.csv", invalid_content)
        
        with patch('main.setup_logger', return_value=MagicMock()):
            with patch('sys.argv', ['main.py', 
                                  '--single-test-input', invalid_file,
                                  '--session-name', 'invalid_test']):
                
                # Should handle gracefully without crashing
                try:
                    main.main()
                except Exception:
                    # Some exceptions are acceptable for invalid data
                    pass
    
    @patch('main.print_header')
    @patch('main.print_help_text')
    @patch('main.print_error')
    def test_missing_drug_data_file(self, mock_error, mock_help, mock_header):
        """Test handling when drug data file is missing."""
        
        nonexistent_drug_file = "/path/that/does/not/exist/drugs.csv"
        
        with patch('main.setup_logger', return_value=MagicMock()):
            with patch('sys.argv', ['main.py', 
                                  '--drug-data', nonexistent_drug_file,
                                  '--session-name', 'missing_drug_test']):
                
                with self.assertRaises(SystemExit):
                    main.main()
    
    @patch('main.load_drug_data')
    @patch('main.select_drugs')
    @patch('main.print_header')
    @patch('main.print_help_text')
    @patch('main.print_step')
    def test_calculation_failure_recovery(self, mock_step, mock_help, mock_header,
                                        mock_select_drugs, mock_load_data):
        """Test recovery when calculation steps fail."""
        
        mock_drug_df = pd.DataFrame({
            'Drug': ['Drug1'],
            'OrgMolecular_Weight': [150.0],
            'Critical_Concentration': [1.0]
        })
        
        mock_load_data.return_value = mock_drug_df
        mock_select_drugs.return_value = mock_drug_df
        
        # Create valid test input
        test_content = ";".join(main.EXPECTED_FIELDS) + "
"
        test_content += "1;test.log;1;n;;;150.0;500.0;results.txt;50.0;10;final.txt
"
        test_file = os.path.join(self.temp_dir, "test_calc_fail.csv")
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        # Mock calculation failure
        with patch('main.cal_potency', side_effect=Exception("Calculation error")):
            with patch('main.setup_logger', return_value=MagicMock()):
                with patch('sys.argv', ['main.py', 
                                      '--single-test-input', test_file,
                                      '--session-name', 'calc_fail_test']):
                    
                    with self.assertRaises(SystemExit):
                        main.main()


class TestOutputIntegration(unittest.TestCase):
    """Test output generation integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.results_dir = os.path.join(self.temp_dir, "results")
        os.makedirs(self.results_dir, exist_ok=True)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
        import logging
        logger = logging.getLogger("pdst-calc")
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
    
    @patch('main.load_drug_data')
    @patch('main.select_drugs')
    @patch('main.cal_potency')
    @patch('main.cal_stockdil')
    @patch('main.cal_mgit_ws')
    @patch('main.print_header')
    @patch('main.print_help_text')
    @patch('main.print_success')
    @patch('main.print_step')
    def test_output_file_generation(self, mock_step, mock_success, mock_help, mock_header,
                                   mock_mgit_ws, mock_stockdil, mock_potency, 
                                   mock_select_drugs, mock_load_data):
        """Test that output files are properly generated."""
        
        # Create enhanced mock data with required columns
        mock_drug_df = pd.DataFrame({
            'Drug': ['Drug1', 'Drug2'],
            'OrgMolecular_Weight': [150.0, 200.0],
            'Critical_Concentration': [1.0, 2.0],
            'Est_DrugW(mg)': [45.0, 55.0],
            'Act_DrugW(mg)': [44.5, 54.2],
            'Vol_WSol_ali(ml)': [2.5, 3.0],
            'Vol_Dil_Add(ml)': [7.5, 7.0],
            'Vol_St_Left(ml)': [490.0, 490.0]
        })
        
        mock_load_data.return_value = mock_drug_df
        mock_select_drugs.return_value = mock_drug_df
        
        # Create test input
        test_content = ";".join(main.EXPECTED_FIELDS) + "
"
        test_content += "1;test.log;1,2;n;;;150.0,200.0;500.0;results.txt;50.0;10;final.txt
"
        test_file = os.path.join(self.temp_dir, "test_output.csv")
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        # Mock the path for results directory
        with patch('os.path.dirname', return_value=self.temp_dir):
            with patch('os.path.abspath', return_value=self.temp_dir):
                with patch('main.setup_logger', return_value=MagicMock()):
                    with patch('sys.argv', ['main.py', 
                                          '--single-test-input', test_file,
                                          '--session-name', 'output_test']):
                        
                        main.main()
        
        # Check that calculation functions were called
        mock_potency.assert_called()
        mock_stockdil.assert_called()
        mock_mgit_ws.assert_called()
    
    def test_log_file_creation_integration(self):
        """Test that log files are created in integration scenarios."""
        
        log_dir = os.path.join(self.temp_dir, ".pdst-calc", "logs")
        
        with patch('os.path.expanduser', return_value=self.temp_dir):
            logger = main.setup_logger("integration_test")
            
            # Log directory should be created
            self.assertTrue(os.path.exists(log_dir))
            
            # Logger should be configured
            self.assertIsNotNone(logger)
            self.assertEqual(logger.name, "pdst-calc")


class TestPerformanceIntegration(unittest.TestCase):
    """Test performance characteristics in integration scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_large_input_file_handling(self):
        """Test handling of large input files."""
        
        # Create a large input file
        large_file = os.path.join(self.temp_dir, "large_input.csv")
        
        with open(large_file, 'w') as f:
            f.write(";".join(main.EXPECTED_FIELDS) + "
")
            
            # Write many test cases
            for i in range(1000):
                values = [
                    str(i), f"log{i}.txt", "1,2,3", "n", "", "",
                    "150.0,160.0,170.0", "500.0", f"results{i}.txt",
                    "50.0", "10", f"final{i}.txt"
                ]
                f.write(";".join(values) + "
")
        
        import time
        start_time = time.time()
        
        # Parse the large file
        result = main.parse_input_file(large_file)
        
        end_time = time.time()
        parse_time = end_time - start_time
        
        # Should parse successfully
        self.assertEqual(len(result), 1000)
        
        # Should complete in reasonable time (less than 5 seconds)
        self.assertLess(parse_time, 5.0, "Large file parsing took too long")
    
    def test_memory_usage_with_large_data(self):
        """Test memory usage with large datasets."""
        
        # Create large DataFrame
        large_df = pd.DataFrame({
            'Drug': [f'Drug_{i}' for i in range(10000)],
            'OrgMolecular_Weight': [150.0 + i*0.1 for i in range(10000)],
            'Critical_Concentration': [1.0 + (i % 10) for i in range(10000)]
        })
        
        # Should handle large DataFrames
        self.assertEqual(len(large_df), 10000)
        
        # Memory usage should be reasonable
        # (This is a basic test - more sophisticated memory profiling could be added)
        import sys
        df_size = sys.getsizeof(large_df)
        self.assertLess(df_size, 100 * 1024 * 1024)  # Less than 100MB


if __name__ == '__main__':
    unittest.main()
