import unittest
import pandas as pd
import io
import sys
from unittest.mock import patch, MagicMock, mock_open
import logging
import tempfile
import os
import supp_calc


class TestSuppCalc(unittest.TestCase):
    """Test cases for supp_calc module functions."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create sample DataFrame for testing
        self.sample_df = pd.DataFrame({
            'Drug': ['Amikacin (AMK)', 'Bedaquiline (BDQ)', 'Clofazimine (CFZ)'],
            'OrgMol_W(g/mol)': [585.6, 555.5, 473.39],
            'Diluent': ['Water', 'DMSO', 'DMSO'],
            'Crit_Conc(mg/ml)': [1.0, 1.0, 1.0]
        })
        
        # Create a more complete sample DataFrame for advanced tests
        self.complete_df = pd.DataFrame({
            'Drug': ['Drug1', 'Drug2'],
            'OrgMol_W(g/mol)': [100.0, 200.0],
            'PurMol_W(g/mol)': [105.0, 195.0],
            'Crit_Conc(mg/ml)': [1.0, 2.0],
            'St_Vol(ml)': [10.0, 15.0],
            'Est_DrugW(mg)': [8.4, 12.6],
            'Act_DrugW(mg)': [8.2, 12.8],
            'Vol_Dil(ml)': [10.2, 14.8],
            'Conc_st_dil(ug/ml)': [800.0, 865.0],
            'Total Mgit tubes': [5.0, 3.0]
        })

    def test_print_and_log_tabulate(self):
        """Test print_and_log_tabulate function."""
        # Capture stdout
        captured_output = io.StringIO()
        
        # Mock logger
        with patch('lib.supp_calc.logger') as mock_logger:
            with patch('sys.stdout', captured_output):
                supp_calc.print_and_log_tabulate(self.sample_df, headers='keys', tablefmt='grid')
        
        # Check that print was called (output captured)
        output = captured_output.getvalue()
        self.assertIn('Amikacin', output)
        self.assertIn('Drug', output)
        
        # Check that logger.info was called
        mock_logger.info.assert_called_once()

    def test_print_table(self):
        """Test print_table function."""
        captured_output = io.StringIO()
        
        with patch('sys.stdout', captured_output):
            supp_calc.print_table(self.sample_df, headers='keys', tablefmt='grid')
        
        output = captured_output.getvalue()
        self.assertIn('Amikacin', output)
        self.assertIn('Drug', output)

    def test_select_drugs_with_valid_input_file(self):
        """Test select_drugs function with valid input file selection."""
        # Test with comma-separated selection
        result = supp_calc.select_drugs(self.sample_df, input_file="1,2")
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        self.assertIn('Amikacin (AMK)', result['Drug'].values)
        self.assertIn('Bedaquiline (BDQ)', result['Drug'].values)

    def test_select_drugs_with_space_separated_input(self):
        """Test select_drugs function with space-separated selection."""
        result = supp_calc.select_drugs(self.sample_df, input_file="1 3")
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        self.assertIn('Amikacin (AMK)', result['Drug'].values)
        self.assertIn('Clofazimine (CFZ)', result['Drug'].values)

    def test_select_drugs_with_invalid_numbers(self):
        """Test select_drugs function with invalid numbers."""
        # Mock error log file
        mock_error_log = MagicMock()
        
        result = supp_calc.select_drugs(self.sample_df, input_file="1,5,10", error_log=mock_error_log)
        
        # Should return None for invalid selections in test mode
        self.assertIsNone(result)
        
        # Check that error messages were written to log
        self.assertTrue(mock_error_log.write.called)

    def test_select_drugs_with_no_valid_selections(self):
        """Test select_drugs function with no valid selections."""
        mock_error_log = MagicMock()
        
        result = supp_calc.select_drugs(self.sample_df, input_file="10,20", error_log=mock_error_log)
        
        self.assertIsNone(result)
        self.assertTrue(mock_error_log.write.called)

    def test_select_drugs_interactive_mode(self):
        """Test select_drugs function in interactive mode."""
        with patch('builtins.input') as mock_input:
            # Mock user selecting drugs 1 and 2, then confirming
            mock_input.side_effect = ["1,2", "y"]
            
            with patch('builtins.print'):  # Suppress print statements
                result = supp_calc.select_drugs(self.sample_df)
            
            self.assertIsInstance(result, pd.DataFrame)
            self.assertEqual(len(result), 2)

    def test_select_drugs_interactive_mode_with_retry(self):
        """Test select_drugs function in interactive mode with retry."""
        with patch('builtins.input') as mock_input:
            # Mock user first rejecting, then accepting
            mock_input.side_effect = ["1,2", "n", "2,3", "y"]
            
            with patch('builtins.print'):  # Suppress print statements
                result = supp_calc.select_drugs(self.sample_df)
            
            self.assertIsInstance(result, pd.DataFrame)
            self.assertEqual(len(result), 2)

    def test_custom_critical_values(self):
        """Test custom_critical_values function."""
        test_df = self.sample_df.copy()
        
        with patch('builtins.input') as mock_input:
            # Mock user entering new values for first drug only
            mock_input.side_effect = ["2.5", "", ""]
            
            supp_calc.custom_critical_values(test_df)
        
        # Check that first drug's critical concentration was updated
        self.assertEqual(test_df.iloc[0]['Crit_Conc(mg/ml)'], 2.5)
        # Check that others remained unchanged
        self.assertEqual(test_df.iloc[1]['Crit_Conc(mg/ml)'], 1.0)

    def test_purchased_weights(self):
        """Test purchased_weights function."""
        test_df = self.sample_df.copy()
        
        with patch('builtins.input') as mock_input:
            mock_input.side_effect = ["600.0", "550.0", "480.0"]
            
            with patch('lib.supp_calc.logger'):  # Mock logger
                supp_calc.purchased_weights(test_df)
        
        # Check that purchased weights column was added
        self.assertIn('PurMol_W(g/mol)', test_df.columns)
        self.assertEqual(test_df.iloc[0]['PurMol_W(g/mol)'], 600.0)
        self.assertEqual(test_df.iloc[1]['PurMol_W(g/mol)'], 550.0)
        self.assertEqual(test_df.iloc[2]['PurMol_W(g/mol)'], 480.0)

    def test_purchased_weights_with_invalid_input(self):
        """Test purchased_weights function with invalid input."""
        test_df = self.sample_df.copy()
        
        with patch('builtins.input') as mock_input:
            # Mock invalid input followed by valid input
            mock_input.side_effect = ["invalid", "600.0", "550.0", "480.0"]
            
            with patch('builtins.print'):  # Suppress error messages
                with patch('lib.supp_calc.logger'):  # Mock logger
                    supp_calc.purchased_weights(test_df)
        
        self.assertIn('PurMol_W(g/mol)', test_df.columns)
        self.assertEqual(test_df.iloc[0]['PurMol_W(g/mol)'], 600.0)

    def test_stock_volume(self):
        """Test stock_volume function."""
        test_df = self.sample_df.copy()
        
        with patch('builtins.input') as mock_input:
            mock_input.side_effect = ["10.0", "15.0", "20.0"]
            
            with patch('lib.supp_calc.logger'):  # Mock logger
                supp_calc.stock_volume(test_df)
        
        self.assertIn('St_Vol(ml)', test_df.columns)
        self.assertEqual(test_df.iloc[0]['St_Vol(ml)'], 10.0)
        self.assertEqual(test_df.iloc[1]['St_Vol(ml)'], 15.0)
        self.assertEqual(test_df.iloc[2]['St_Vol(ml)'], 20.0)

    def test_cal_potency(self):
        """Test cal_potency function."""
        test_df = self.complete_df.copy()
        
        with patch('lib.supp_calc.logger'):  # Mock logger
            supp_calc.cal_potency(test_df)
        
        # Check that new columns were added
        self.assertIn('Potency', test_df.columns)
        self.assertIn('Est_DrugW(mg)', test_df.columns)
        
        # Check calculated values (105/100 = 1.05 potency for first drug)
        self.assertAlmostEqual(test_df.iloc[0]['Potency'], 1.05, places=2)

    def test_cal_potency_with_missing_data(self):
        """Test cal_potency function with missing data."""
        test_df = self.sample_df.copy()
        # Missing required columns
        
        with patch('lib.supp_calc.logger'):  # Mock logger
            supp_calc.cal_potency(test_df)
        
        # Should handle missing data gracefully
        self.assertIn('Potency', test_df.columns)
        self.assertIn('Est_DrugW(mg)', test_df.columns)
        
        # Values should be None for missing data
        self.assertIsNone(test_df.iloc[0]['Potency'])

    def test_act_drugweight(self):
        """Test act_drugweight function."""
        test_df = self.sample_df.copy()
        
        with patch('builtins.input') as mock_input:
            mock_input.side_effect = ["8.2", "12.5", "15.1"]
            
            with patch('builtins.print'):  # Suppress print statements
                with patch('lib.supp_calc.logger'):  # Mock logger
                    supp_calc.act_drugweight(test_df)
        
        self.assertIn('Act_DrugW(mg)', test_df.columns)
        self.assertEqual(test_df.iloc[0]['Act_DrugW(mg)'], 8.2)

    def test_cal_stockdil(self):
        """Test cal_stockdil function."""
        test_df = self.complete_df.copy()
        
        supp_calc.cal_stockdil(test_df)
        
        # Check that new columns were added
        self.assertIn('Vol_Dil(ml)', test_df.columns)
        self.assertIn('Conc_st_dil(ug/ml)', test_df.columns)
        
        # Check that values were calculated (not None)
        self.assertIsNotNone(test_df.iloc[0]['Vol_Dil(ml)'])
        self.assertIsNotNone(test_df.iloc[0]['Conc_st_dil(ug/ml)'])

    def test_mgit_tubes(self):
        """Test mgit_tubes function."""
        test_df = self.sample_df.copy()
        
        with patch('builtins.input') as mock_input:
            mock_input.side_effect = ["5", "3", "7"]
            
            with patch('lib.supp_calc.logger'):  # Mock logger
                supp_calc.mgit_tubes(test_df)
        
        self.assertIn('Total Mgit tubes', test_df.columns)
        self.assertEqual(test_df.iloc[0]['Total Mgit tubes'], 5.0)

    def test_cal_mgit_ws(self):
        """Test cal_mgit_ws function."""
        test_df = self.complete_df.copy()
        
        with patch('lib.supp_calc.logger'):  # Mock logger
            supp_calc.cal_mgit_ws(test_df)
        
        # Check that new columns were added
        expected_columns = [
            'WSol_Conc_MGIT(ug/ml)', 
            'WSol_Vol(ml)', 
            'Vol_WSol_ali(ml)',
            'Vol_Dil_Add(ml)', 
            'Vol_St_Left(ml)'
        ]
        
        for col in expected_columns:
            self.assertIn(col, test_df.columns)
        
        # Check that values were calculated
        self.assertIsNotNone(test_df.iloc[0]['WSol_Conc_MGIT(ug/ml)'])

    def test_cal_mgit_ws_with_exception_handling(self):
        """Test cal_mgit_ws function with missing data."""
        test_df = self.sample_df.copy()  # Missing required columns
        
        with patch('lib.supp_calc.logger'):  # Mock logger
            supp_calc.cal_mgit_ws(test_df)
        
        # Should handle exceptions gracefully
        expected_columns = [
            'WSol_Conc_MGIT(ug/ml)', 
            'WSol_Vol(ml)', 
            'Vol_WSol_ali(ml)',
            'Vol_Dil_Add(ml)', 
            'Vol_St_Left(ml)'
        ]
        
        for col in expected_columns:
            self.assertIn(col, test_df.columns)


class TestSuppCalcIntegration(unittest.TestCase):
    """Integration tests for supp_calc module."""

    def test_full_workflow_simulation(self):
        """Test a complete workflow simulation."""
        # Start with basic drug data
        df = pd.DataFrame({
            'Drug': ['Test Drug 1', 'Test Drug 2'],
            'OrgMol_W(g/mol)': [100.0, 200.0],
            'Crit_Conc(mg/ml)': [1.0, 2.0]
        })
        
        # Select drugs (simulate file input)
        selected_df = supp_calc.select_drugs(df, input_file="1,2")
        self.assertEqual(len(selected_df), 2)
        
        # Add purchased weights (simulate user input)
        with patch('builtins.input') as mock_input:
            mock_input.side_effect = ["105.0", "195.0"]
            with patch('lib.supp_calc.logger'):
                supp_calc.purchased_weights(selected_df)
        
        # Add stock volumes
        with patch('builtins.input') as mock_input:
            mock_input.side_effect = ["10.0", "15.0"]
            with patch('lib.supp_calc.logger'):
                supp_calc.stock_volume(selected_df)
        
        # Calculate potency
        with patch('lib.supp_calc.logger'):
            supp_calc.cal_potency(selected_df)
        
        # Add actual drug weights
        with patch('builtins.input') as mock_input:
            mock_input.side_effect = ["8.5", "12.5"]
            with patch('builtins.print'):
                with patch('lib.supp_calc.logger'):
                    supp_calc.act_drugweight(selected_df)
        
        # Calculate stock dilution
        supp_calc.cal_stockdil(selected_df)
        
        # Add MGIT tubes
        with patch('builtins.input') as mock_input:
            mock_input.side_effect = ["5", "3"]
            with patch('lib.supp_calc.logger'):
                supp_calc.mgit_tubes(selected_df)
        
        # Calculate MGIT working solution
        with patch('lib.supp_calc.logger'):
            supp_calc.cal_mgit_ws(selected_df)
        
        # Verify that all expected columns are present
        expected_final_columns = [
            'Drug', 'OrgMol_W(g/mol)', 'Crit_Conc(mg/ml)', 'PurMol_W(g/mol)',
            'St_Vol(ml)', 'Potency', 'Est_DrugW(mg)', 'Act_DrugW(mg)',
            'Vol_Dil(ml)', 'Conc_st_dil(ug/ml)', 'Total Mgit tubes',
            'WSol_Conc_MGIT(ug/ml)', 'WSol_Vol(ml)', 'Vol_WSol_ali(ml)',
            'Vol_Dil_Add(ml)', 'Vol_St_Left(ml)'
        ]
        
        for col in expected_final_columns:
            self.assertIn(col, selected_df.columns, f"Missing column: {col}")
        
        # Verify that calculations produced reasonable results
        self.assertGreater(selected_df.iloc[0]['Potency'], 0)
        self.assertGreater(selected_df.iloc[0]['Est_DrugW(mg)'], 0)


class TestSuppCalcErrorHandling(unittest.TestCase):
    """Test error handling in supp_calc module."""

    def test_functions_with_empty_dataframe(self):
        """Test functions with empty DataFrame."""
        empty_df = pd.DataFrame()
        
        # These functions should handle empty DataFrames gracefully
        with patch('lib.supp_calc.logger'):
            try:
                supp_calc.cal_potency(empty_df)
                supp_calc.cal_stockdil(empty_df)
                supp_calc.cal_mgit_ws(empty_df)
            except Exception as e:
                self.fail(f"Functions should handle empty DataFrame gracefully: {e}")

    def test_functions_with_malformed_data(self):
        """Test functions with malformed data."""
        malformed_df = pd.DataFrame({
            'Drug': ['Test'],
            'BadColumn': ['BadData']
        })
        
        with patch('lib.supp_calc.logger'):
            # These should handle missing columns gracefully
            supp_calc.cal_potency(malformed_df)
            supp_calc.cal_stockdil(malformed_df)
            supp_calc.cal_mgit_ws(malformed_df)
        
        # Check that the functions didn't crash and added expected columns
        expected_columns = ['Potency', 'Est_DrugW(mg)']
        for col in expected_columns:
            self.assertIn(col, malformed_df.columns)


if __name__ == '__main__':
    unittest.main()
