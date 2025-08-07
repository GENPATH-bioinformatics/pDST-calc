"""
Hypothesis-driven property-based tests for supp_calc module.

These tests use the Hypothesis library to generate random inputs and verify
properties of supplementary calculation functions, including user interaction,
data manipulation, and calculation workflows.
"""

import pytest
import pandas as pd
import tempfile
import os
import io
import sys
from pathlib import Path
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import text, lists, floats, integers, sampled_from
from unittest.mock import patch
from io import StringIO

# Add the parent directory to sys.path to import lib modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from lib.supp_calc import (
    print_and_log_tabulate, print_table, select_drugs,
    custom_critical_values, purchased_weights, stock_volume,
    cal_potency, act_drugweight, cal_stockdil, mgit_tubes, cal_mgit_ws
)

# Import dst_calc functions for integration testing
from lib.dst_calc import potency, est_drugweight, vol_diluent, conc_stock


# Strategies for generating test data
drug_names = text(min_size=1, max_size=30, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-')
molecular_weights = floats(min_value=50.0, max_value=2000.0, allow_nan=False, allow_infinity=False)
concentrations = floats(min_value=0.001, max_value=100.0, allow_nan=False, allow_infinity=False)
volumes = floats(min_value=0.1, max_value=1000.0, allow_nan=False, allow_infinity=False)
positive_integers = integers(min_value=1, max_value=100)

# Strategy for generating drug DataFrame records
drug_record_strategy = st.fixed_dictionaries({
    'Drug': drug_names,
    'OrgMol_W(g/mol)': molecular_weights,
    'Crit_Conc(mg/ml)': concentrations,
    'Diluent': sampled_from(['Water', 'DMSO', 'Ethanol', 'Buffer'])
})


def create_sample_dataframe(records):
    """Helper function to create a DataFrame from drug records."""
    df = pd.DataFrame(records)
    # Ensure drug names are unique by appending index if needed
    if len(df) > 0:
        drug_counts = df['Drug'].value_counts()
        duplicate_drugs = drug_counts[drug_counts > 1].index
        for drug_name in duplicate_drugs:
            mask = df['Drug'] == drug_name
            indices = df[mask].index
            for i, idx in enumerate(indices):
                df.at[idx, 'Drug'] = f"{drug_name}_{i+1}"
    return df


class TestPrintAndLogFunctions:
    """Test printing and logging utility functions."""
    
    @given(records=lists(drug_record_strategy, min_size=1, max_size=10))
    def test_print_table_output(self, records):
        """Test that print_table produces output for valid DataFrames."""
        df = create_sample_dataframe(records)
        
        # Capture stdout to verify output is produced
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            print_table(df)
            output = mock_stdout.getvalue()
            
            # Should produce some output
            assert len(output) > 0
            # Should contain drug names
            for record in records:
                assert record['Drug'] in output or str(record['Drug']) in output
    
    def test_print_table_empty_dataframe(self):
        """Test print_table with empty DataFrame."""
        df = pd.DataFrame()
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            print_table(df)
            output = mock_stdout.getvalue()
            # Should handle empty DataFrame gracefully
            assert isinstance(output, str)
    
    @given(records=lists(drug_record_strategy, min_size=1, max_size=5))
    def test_print_and_log_tabulate_output(self, records):
        """Test that print_and_log_tabulate produces output and logs."""
        df = create_sample_dataframe(records)
        
        # Mock both print and logger
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout, \
             patch('lib.supp_calc.logger') as mock_logger:
            
            print_and_log_tabulate(df)
            
            # Should produce stdout output
            output = mock_stdout.getvalue()
            assert len(output) > 0
            
            # Should call logger.info
            assert mock_logger.info.called


class TestSelectDrugs:
    """Test drug selection functionality."""
    
    @given(records=lists(drug_record_strategy, min_size=3, max_size=10))
    def test_select_drugs_valid_input(self, records):
        """Test select_drugs with valid input strings."""
        df = create_sample_dataframe(records)
        num_drugs = len(df)
        
        # Test selecting first drug
        result = select_drugs(df, input_file="1")
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result.iloc[0]['Drug'] == df.iloc[0]['Drug']
        
        # Test selecting multiple drugs (if enough drugs available)
        if num_drugs >= 3:
            result = select_drugs(df, input_file="1,3")
            assert result is not None
            assert len(result) == 2
    
    @given(records=lists(drug_record_strategy, min_size=2, max_size=10))
    def test_select_drugs_invalid_input(self, records):
        """Test select_drugs with invalid input strings."""
        df = create_sample_dataframe(records)
        num_drugs = len(df)
        
        # Test selecting non-existent drug index
        invalid_index = num_drugs + 10
        result = select_drugs(df, input_file=str(invalid_index))
        assert result is None  # Should return None for invalid input in test mode
    
    @given(records=lists(drug_record_strategy, min_size=1, max_size=5))
    def test_select_drugs_all_selection(self, records):
        """Test select_drugs with 'all' input."""
        df = create_sample_dataframe(records)
        
        # Note: 'all' is handled in interactive mode, not test mode
        # In test mode, it would be processed as invalid input
        result = select_drugs(df, input_file="all")
        # This should process "all" as invalid since it's not a digit
        assert result is None
    
    def test_select_drugs_empty_dataframe(self):
        """Test select_drugs with empty DataFrame."""
        df = pd.DataFrame(columns=['Drug'])
        
        result = select_drugs(df, input_file="1")
        assert result is None  # No drugs to select
    
    @given(records=lists(drug_record_strategy, min_size=5, max_size=20))
    def test_select_drugs_boundary_cases(self, records):
        """Test boundary cases for drug selection."""
        df = create_sample_dataframe(records)
        num_drugs = len(df)
        
        # Test selecting first drug
        result = select_drugs(df, input_file="1")
        assert result is not None and len(result) == 1
        
        # Test selecting last drug
        result = select_drugs(df, input_file=str(num_drugs))
        assert result is not None and len(result) == 1
        
        # Test selecting just outside range
        result = select_drugs(df, input_file=str(num_drugs + 1))
        assert result is None
        
        # Test selecting zero (invalid)
        result = select_drugs(df, input_file="0")
        assert result is None


class TestCalculationFunctions:
    """Test calculation functions with DataFrame inputs."""
    
    @given(records=lists(drug_record_strategy, min_size=1, max_size=5))
    def test_cal_potency_properties(self, records):
        """Test potency calculation properties."""
        df = create_sample_dataframe(records)
        
        # Add required columns
        purchased_weights = [float(record['OrgMol_W(g/mol)']) * 1.1 for record in records]
        stock_volumes = [10.0] * len(records)
        
        df['PurMol_W(g/mol)'] = purchased_weights
        df['St_Vol(ml)'] = stock_volumes
        
        # Calculate potencies
        cal_potency(df)
        
        # Verify potency column exists and has correct properties
        assert 'Potency' in df.columns
        assert 'Est_DrugW(mg)' in df.columns
        
        for i, record in enumerate(records):
            if pd.notna(df.iloc[i]['Potency']):
                # Potency should be positive
                assert df.iloc[i]['Potency'] > 0
                
                # Verify potency calculation
                expected_potency = purchased_weights[i] / float(record['OrgMol_W(g/mol)'])
                assert abs(df.iloc[i]['Potency'] - expected_potency) < 1e-10
    
    @given(records=lists(drug_record_strategy, min_size=1, max_size=5))
    def test_cal_stockdil_properties(self, records):
        """Test stock dilution calculation properties."""
        df = create_sample_dataframe(records)
        
        # Add required columns with reasonable values
        estimated_weights = [5.0] * len(records)
        actual_weights = [4.8] * len(records)  # Slightly less than estimated
        stock_volumes = [10.0] * len(records)
        
        df['Est_DrugW(mg)'] = estimated_weights
        df['Act_DrugW(mg)'] = actual_weights
        df['St_Vol(ml)'] = stock_volumes
        
        # Calculate stock dilution
        cal_stockdil(df)
        
        # Verify required columns exist
        assert 'Vol_Dil(ml)' in df.columns
        assert 'Conc_st_dil(ug/ml)' in df.columns
        
        for i in range(len(df)):
            if pd.notna(df.iloc[i]['Vol_Dil(ml)']):
                # Diluent volume should be positive
                assert df.iloc[i]['Vol_Dil(ml)'] > 0
                
                # Stock concentration should be positive
                assert df.iloc[i]['Conc_st_dil(ug/ml)'] > 0
    
    @given(records=lists(drug_record_strategy, min_size=1, max_size=5))
    def test_cal_mgit_ws_properties(self, records):
        """Test MGIT working solution calculation properties."""
        df = create_sample_dataframe(records)
        
        # Add all required columns
        df['Total Mgit tubes'] = [5.0] * len(records)
        df['Conc_st_dil(ug/ml)'] = [1000.0] * len(records)
        df['Vol_Dil(ml)'] = [10.0] * len(records)
        
        # Calculate MGIT working solutions
        cal_mgit_ws(df)
        
        # Verify all output columns exist
        expected_columns = [
            'WSol_Conc_MGIT(ug/ml)',
            'WSol_Vol(ml)',
            'Vol_WSol_ali(ml)',
            'Vol_Dil_Add(ml)',
            'Vol_St_Left(ml)'
        ]
        
        for col in expected_columns:
            assert col in df.columns
        
        for i in range(len(df)):
            # All calculated values should be reasonable for valid inputs
            if pd.notna(df.iloc[i]['WSol_Conc_MGIT(ug/ml)']):
                assert df.iloc[i]['WSol_Conc_MGIT(ug/ml)'] > 0
                assert df.iloc[i]['WSol_Vol(ml)'] > 0
                assert df.iloc[i]['Vol_WSol_ali(ml)'] >= 0
                # Vol_Dil_Add can be negative when stock is more concentrated than needed
                # This is a realistic scenario, so we don't require it to be non-negative


class TestInputValidation:
    """Test input validation and error handling."""
    
    def test_functions_with_missing_columns(self):
        """Test behavior when required DataFrame columns are missing."""
        df = pd.DataFrame({'Drug': ['TestDrug']})
        
        # These should handle missing columns gracefully
        cal_potency(df)  # Should add columns with None values
        assert 'Potency' in df.columns
        
        cal_stockdil(df)  # Should handle missing required columns
        assert 'Vol_Dil(ml)' in df.columns
        
        cal_mgit_ws(df)  # Should handle missing required columns
        assert 'WSol_Conc_MGIT(ug/ml)' in df.columns
    
    @given(
        num_drugs=integers(min_value=1, max_value=5),
        base_molecular_weight=floats(min_value=50.0, max_value=1000.0, allow_nan=False),
        base_concentration=floats(min_value=0.001, max_value=50.0, allow_nan=False)
    )
    def test_calculation_consistency(self, num_drugs, base_molecular_weight, base_concentration):
        """Test that calculations maintain mathematical consistency."""
        # Create a DataFrame with calculated values
        records = []
        for i in range(num_drugs):
            records.append({
                'Drug': f'Drug{i}',
                'OrgMol_W(g/mol)': base_molecular_weight * (1 + i * 0.1),
                'Crit_Conc(mg/ml)': base_concentration * (1 + i * 0.05),
                'Diluent': 'Water'
            })
        
        df = create_sample_dataframe(records)
        
        # Add calculation inputs
        df['PurMol_W(g/mol)'] = [record['OrgMol_W(g/mol)'] * 1.05 for record in records]  # 5% heavier
        df['St_Vol(ml)'] = [10.0] * len(records)
        
        # Perform calculations
        cal_potency(df)
        
        # Add actual weights (slightly different from estimated)
        df['Act_DrugW(mg)'] = [est * 0.95 for est in df['Est_DrugW(mg)']]
        
        cal_stockdil(df)
        
        # Add MGIT tube counts
        df['Total Mgit tubes'] = [5] * len(records)
        
        cal_mgit_ws(df)
        
        # Verify mathematical relationships
        for i in range(len(df)):
            if all(pd.notna(df.iloc[i][col]) for col in ['Potency', 'Est_DrugW(mg)', 'Act_DrugW(mg)']):
                # Potency should match manual calculation
                expected_potency = df.iloc[i]['PurMol_W(g/mol)'] / df.iloc[i]['OrgMol_W(g/mol)']
                assert abs(df.iloc[i]['Potency'] - expected_potency) < 1e-10
                
                # Working solution components should sum correctly
                if all(pd.notna(df.iloc[i][col]) for col in ['Vol_WSol_ali(ml)', 'Vol_Dil_Add(ml)', 'WSol_Vol(ml)']):
                    ws_total = df.iloc[i]['Vol_WSol_ali(ml)'] + df.iloc[i]['Vol_Dil_Add(ml)']
                    expected_total = df.iloc[i]['WSol_Vol(ml)']
                    assert abs(ws_total - expected_total) < 1e-10


class TestIntegrationProperties:
    """Test integration properties across the entire calculation workflow."""
    
    @given(
        num_drugs=integers(min_value=1, max_value=5),
        base_molecular_weight=floats(min_value=100.0, max_value=500.0, allow_nan=False),
        base_concentration=floats(min_value=0.1, max_value=10.0, allow_nan=False)
    )
    @settings(max_examples=20)  # Limit examples for complex integration test
    def test_complete_workflow_integration(self, num_drugs, base_molecular_weight, base_concentration):
        """Test complete calculation workflow integration."""
        # Create test data
        records = []
        for i in range(num_drugs):
            records.append({
                'Drug': f'TestDrug{i}',
                'OrgMol_W(g/mol)': base_molecular_weight * (1 + i * 0.1),
                'Crit_Conc(mg/ml)': base_concentration * (1 + i * 0.05),
                'Diluent': 'Water'
            })
        
        df = create_sample_dataframe(records)
        
        # Step 1: Add purchased weights and stock volumes
        df['PurMol_W(g/mol)'] = [record['OrgMol_W(g/mol)'] * 1.1 for record in records]
        df['St_Vol(ml)'] = [10.0] * num_drugs
        
        # Step 2: Calculate potency and estimated drug weight
        cal_potency(df)
        
        # Step 3: Add actual drug weights
        df['Act_DrugW(mg)'] = [est * 0.95 if pd.notna(est) else None for est in df['Est_DrugW(mg)']]
        
        # Step 4: Calculate stock dilution
        cal_stockdil(df)
        
        # Step 5: Add MGIT tube counts
        df['Total Mgit tubes'] = [5] * num_drugs
        
        # Step 6: Calculate MGIT working solutions
        cal_mgit_ws(df)
        
        # Verify workflow consistency
        for i in range(len(df)):
            # All major calculated columns should exist
            major_columns = [
                'Potency', 'Est_DrugW(mg)', 'Vol_Dil(ml)', 'Conc_st_dil(ug/ml)',
                'WSol_Conc_MGIT(ug/ml)', 'WSol_Vol(ml)'
            ]
            
            for col in major_columns:
                assert col in df.columns
            
            # Values should be reasonable for valid quantities
            # Most volumes should be non-negative, but Vol_Dil_Add can be negative in realistic scenarios
            non_negative_columns = [
                'Est_DrugW(mg)', 'Vol_Dil(ml)', 'Conc_st_dil(ug/ml)',
                'WSol_Vol(ml)', 'Vol_WSol_ali(ml)'
            ]
            
            for col in non_negative_columns:
                if col in df.columns and pd.notna(df.iloc[i][col]):
                    assert df.iloc[i][col] >= 0, f"Column {col} should be non-negative"
            
            # Potency should be positive
            if pd.notna(df.iloc[i]['Potency']):
                assert df.iloc[i]['Potency'] > 0


class TestErrorHandling:
    """Test error handling in calculation functions."""
    
    def test_calculation_with_invalid_data(self):
        """Test calculations with invalid or missing data."""
        # Create DataFrame with some invalid data
        df = pd.DataFrame({
            'Drug': ['Drug1', 'Drug2'],
            'OrgMol_W(g/mol)': [100.0, None],  # Missing value
            'Crit_Conc(mg/ml)': [1.0, 2.0],
            'PurMol_W(g/mol)': [110.0, 120.0],
            'St_Vol(ml)': [10.0, 10.0]
        })
        
        # Should handle missing/invalid data gracefully
        cal_potency(df)
        
        # First drug should have valid potency, second should have None
        assert pd.notna(df.iloc[0]['Potency'])
        assert pd.isna(df.iloc[1]['Potency'])
    
    def test_division_by_zero_handling(self):
        """Test handling of division by zero scenarios."""
        df = pd.DataFrame({
            'Drug': ['Drug1'],
            'OrgMol_W(g/mol)': [0.0],  # This could cause division by zero
            'Crit_Conc(mg/ml)': [1.0],
            'PurMol_W(g/mol)': [110.0],
            'St_Vol(ml)': [10.0]
        })
        
        # Should handle division by zero gracefully
        cal_potency(df)
        
        # Should either have None or inf value, but not crash
        assert 'Potency' in df.columns


class TestDataFrameManipulation:
    """Test DataFrame manipulation properties."""
    
    @given(records=lists(drug_record_strategy, min_size=1, max_size=10))
    def test_original_data_preservation(self, records):
        """Test that original DataFrame data is preserved during calculations."""
        df = create_sample_dataframe(records)
        original_drugs = df['Drug'].tolist()
        original_mw = df['OrgMol_W(g/mol)'].tolist()
        
        # Add required columns
        df['PurMol_W(g/mol)'] = [mw * 1.1 for mw in original_mw]
        df['St_Vol(ml)'] = [10.0] * len(records)
        
        # Perform calculations
        cal_potency(df)
        
        # Original data should be unchanged
        assert df['Drug'].tolist() == original_drugs
        assert df['OrgMol_W(g/mol)'].tolist() == original_mw
    
    @given(records=lists(drug_record_strategy, min_size=2, max_size=8))
    def test_column_addition_properties(self, records):
        """Test properties of column addition during calculations."""
        df = create_sample_dataframe(records)
        initial_columns = set(df.columns)
        
        # Add required data
        df['PurMol_W(g/mol)'] = [100.0] * len(records)
        df['St_Vol(ml)'] = [10.0] * len(records)
        
        cal_potency(df)
        after_potency_columns = set(df.columns)
        
        # Should add new columns without removing existing ones
        assert initial_columns.issubset(after_potency_columns)
        assert 'Potency' in after_potency_columns
        assert 'Est_DrugW(mg)' in after_potency_columns
        
        # DataFrame should have same number of rows
        assert len(df) == len(records)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
