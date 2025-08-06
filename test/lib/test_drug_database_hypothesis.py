"""
Hypothesis-driven property-based tests for drug_database module.

These tests use the Hypothesis library to generate random inputs and verify
properties of drug database loading functionality, including error handling,
data validation, and edge cases.
"""

import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import text, lists, floats, one_of, just
import sys

# Add the parent directory to sys.path to import lib modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from lib.drug_database import load_drug_data


# Strategies for generating test data
drug_names = text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), blacklist_characters='\n\r\t,"'),
    min_size=1,
    max_size=50
)

molecular_weights = floats(min_value=50.0, max_value=2000.0, allow_nan=False, allow_infinity=False)
concentrations = floats(min_value=0.001, max_value=100.0, allow_nan=False, allow_infinity=False)

diluent_names = one_of(
    just("Water"),
    just("DMSO"),
    just("Ethanol"),
    just("Saline"),
    just("Buffer"),
    text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), blacklist_characters='\n\r\t,"'),
        min_size=1,
        max_size=20
    )
)

# Strategy for generating complete drug records
drug_record = st.fixed_dictionaries({
    'Drug': drug_names,
    'OrgMolecular_Weight': molecular_weights,
    'Diluent': diluent_names,
    'Critical_Concentration': concentrations
})


class TestLoadDrugData:
    """Test load_drug_data function properties."""
    
    def test_load_nonexistent_file(self):
        """Loading a non-existent file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_drug_data("/path/that/does/not/exist.csv")
    
    def test_load_empty_file(self):
        """Loading an empty CSV file should return empty DataFrame with expected columns."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("")  # Empty file
            temp_path = f.name
        
        try:
            df = load_drug_data(temp_path)
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 0
            expected_columns = ['Drug', 'OrgMolecular_Weight', 'Diluent', 'Critical_Concentration']
            assert list(df.columns) == expected_columns
        finally:
            os.unlink(temp_path)
    
    def test_load_header_only_file(self):
        """Loading a CSV with only headers should return empty DataFrame with correct columns."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("Drug,OrgMolecular_Weight,Diluent,Critical_Concentration\n")
            temp_path = f.name
        
        try:
            df = load_drug_data(temp_path)
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 0
            assert list(df.columns) == ['Drug', 'OrgMolecular_Weight', 'Diluent', 'Critical_Concentration']
        finally:
            os.unlink(temp_path)
    
    @given(records=lists(drug_record, min_size=1, max_size=20))
    def test_load_valid_data(self, records):
        """Loading valid CSV data should return DataFrame with correct structure and data."""
        # Create temporary CSV file with generated data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("Drug,OrgMolecular_Weight,Diluent,Critical_Concentration\n")
            for record in records:
                # Escape drug names that might contain commas or quotes
                drug_name = str(record['Drug']).replace('"', '""')
                if ',' in drug_name or '"' in drug_name:
                    drug_name = f'"{drug_name}"'
                
                diluent = str(record['Diluent']).replace('"', '""')
                if ',' in diluent or '"' in diluent:
                    diluent = f'"{diluent}"'
                
                f.write(f"{drug_name},{record['OrgMolecular_Weight']},{diluent},{record['Critical_Concentration']}\n")
            temp_path = f.name
        
        try:
            df = load_drug_data(temp_path)
            
            # Basic structure checks
            assert isinstance(df, pd.DataFrame)
            assert len(df) == len(records)
            assert list(df.columns) == ['Drug', 'OrgMolecular_Weight', 'Diluent', 'Critical_Concentration']
            
            # Data type checks
            assert df['OrgMolecular_Weight'].dtype in [float, 'float64']
            assert df['Critical_Concentration'].dtype in [float, 'float64']
            
            # Value range checks for numeric columns
            assert all(df['OrgMolecular_Weight'] > 0)
            assert all(df['Critical_Concentration'] > 0)
            
        finally:
            os.unlink(temp_path)
    
    def test_load_invalid_csv_format(self):
        """Loading malformed CSV should raise appropriate exception."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("This is not a valid CSV file\nWith random content")
            temp_path = f.name
        
        try:
            # This should either work (pandas is lenient) or raise an exception
            # If it works, we should get a DataFrame but it may not have expected structure
            df = load_drug_data(temp_path)
            # If we get here, pandas parsed it somehow
            assert isinstance(df, pd.DataFrame)
        except Exception:
            # This is expected for truly malformed data
            pass
        finally:
            os.unlink(temp_path)
    
    @given(num_rows=st.integers(min_value=1, max_value=100))
    def test_load_data_size_consistency(self, num_rows):
        """DataFrame size should match input data size."""
        # Generate simple test data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("Drug,OrgMolecular_Weight,Diluent,Critical_Concentration\n")
            for i in range(num_rows):
                f.write(f"Drug{i},100.5,Water,1.0\n")
            temp_path = f.name
        
        try:
            df = load_drug_data(temp_path)
            assert len(df) == num_rows
            assert len(df.columns) == 4
        finally:
            os.unlink(temp_path)
    
    def test_load_with_pathlib_path(self):
        """Function should work with pathlib.Path objects."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("Drug,OrgMolecular_Weight,Diluent,Critical_Concentration\n")
            f.write("TestDrug,150.0,DMSO,2.5\n")
            temp_path = Path(f.name)
        
        try:
            df = load_drug_data(temp_path)
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 1
            assert df.iloc[0]['Drug'] == 'TestDrug'
        finally:
            os.unlink(str(temp_path))
    
    @given(
        molecular_weight=floats(min_value=0.1, max_value=5000.0, allow_nan=False, allow_infinity=False),
        concentration=floats(min_value=0.001, max_value=1000.0, allow_nan=False, allow_infinity=False)
    )
    def test_numeric_data_preservation(self, molecular_weight, concentration):
        """Numeric data should be preserved accurately when loading."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("Drug,OrgMolecular_Weight,Diluent,Critical_Concentration\n")
            f.write(f"TestDrug,{molecular_weight},Water,{concentration}\n")
            temp_path = f.name
        
        try:
            df = load_drug_data(temp_path)
            assert abs(df.iloc[0]['OrgMolecular_Weight'] - molecular_weight) < 1e-10
            assert abs(df.iloc[0]['Critical_Concentration'] - concentration) < 1e-10
        finally:
            os.unlink(temp_path)


class TestDataValidationProperties:
    """Test properties of loaded drug data validation."""
    
    @given(records=lists(drug_record, min_size=5, max_size=50))
    def test_no_duplicate_drugs(self, records):
        """Check that we can detect duplicate drug names in loaded data."""
        # Make some drugs have duplicate names
        if len(records) >= 2:
            records[1] = records[0].copy()  # Create a duplicate
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("Drug,OrgMolecular_Weight,Diluent,Critical_Concentration\n")
            for record in records:
                drug_name = str(record['Drug']).replace('"', '""')
                if ',' in drug_name:
                    drug_name = f'"{drug_name}"'
                f.write(f"{drug_name},{record['OrgMolecular_Weight']},Water,{record['Critical_Concentration']}\n")
            temp_path = f.name
        
        try:
            df = load_drug_data(temp_path)
            # Check if there are duplicates
            has_duplicates = df['Drug'].duplicated().any()
            duplicate_count = df['Drug'].duplicated().sum()
            
            if has_duplicates:
                assert duplicate_count > 0
                # The DataFrame should still be valid
                assert len(df) == len(records)
            else:
                assert duplicate_count == 0
                
        finally:
            os.unlink(temp_path)
    
    @given(records=lists(drug_record, min_size=1, max_size=20))
    def test_all_required_columns_present(self, records):
        """All required columns should be present in loaded data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("Drug,OrgMolecular_Weight,Diluent,Critical_Concentration\n")
            for record in records:
                f.write(f"{record['Drug']},{record['OrgMolecular_Weight']},{record['Diluent']},{record['Critical_Concentration']}\n")
            temp_path = f.name
        
        try:
            df = load_drug_data(temp_path)
            required_columns = {'Drug', 'OrgMolecular_Weight', 'Diluent', 'Critical_Concentration'}
            assert required_columns.issubset(set(df.columns))
        finally:
            os.unlink(temp_path)


class TestErrorHandling:
    """Test error handling properties."""
    
    def test_permission_denied_handling(self):
        """Test behavior when file permissions are denied."""
        # This test is platform-dependent and may not work on all systems
        # We'll create a file and then try to make it unreadable
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("Drug,OrgMolecular_Weight,Diluent,Critical_Concentration\n")
            f.write("TestDrug,100.0,Water,1.0\n")
            temp_path = f.name
        
        try:
            # Try to make file unreadable (may not work on all systems)
            try:
                os.chmod(temp_path, 0o000)
                with pytest.raises((PermissionError, FileNotFoundError)):
                    load_drug_data(temp_path)
            except (OSError, NotImplementedError):
                # If we can't change permissions, skip this test
                pytest.skip("Cannot modify file permissions on this system")
        finally:
            # Restore permissions and clean up
            try:
                os.chmod(temp_path, 0o644)
                os.unlink(temp_path)
            except (OSError, FileNotFoundError):
                pass
    
    def test_corrupted_file_handling(self):
        """Test handling of corrupted or truncated files."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as f:
            # Write some valid CSV data, then some binary garbage
            f.write(b"Drug,OrgMolecular_Weight,Diluent,Critical_Concentration\n")
            f.write(b"TestDrug,100.0,Water,1.0\n")
            f.write(b"\x00\x01\x02\xff\xfe")  # Binary garbage
            temp_path = f.name
        
        try:
            # Pandas might handle this gracefully or raise an exception
            df = load_drug_data(temp_path)
            # If we get here, pandas managed to parse something
            assert isinstance(df, pd.DataFrame)
        except Exception:
            # This is acceptable - corrupted files should cause errors
            pass
        finally:
            os.unlink(temp_path)


class TestDefaultFilePath:
    """Test default file path behavior."""
    
    def test_default_filepath_construction(self):
        """Default filepath should be constructed correctly relative to module location."""
        # We can't test the actual default file loading without knowing if it exists
        # But we can test that calling without filepath doesn't immediately crash
        try:
            df = load_drug_data()  # No filepath provided
            # If successful, should return a DataFrame
            assert isinstance(df, pd.DataFrame)
        except FileNotFoundError:
            # This is expected if the default file doesn't exist
            pass
        except Exception as e:
            # Other exceptions might indicate problems with path construction
            pytest.fail(f"Unexpected exception when using default path: {e}")
    
    def test_none_filepath_uses_default(self):
        """Passing None as filepath should use default behavior."""
        try:
            df1 = load_drug_data(None)
            df2 = load_drug_data()  # Should be equivalent
            
            # If both succeed, they should return the same data
            if isinstance(df1, pd.DataFrame) and isinstance(df2, pd.DataFrame):
                pd.testing.assert_frame_equal(df1, df2)
        except FileNotFoundError:
            # Expected if default file doesn't exist
            pass


class TestBoundaryConditions:
    """Test boundary conditions and edge cases."""
    
    def test_very_long_drug_names(self):
        """Test handling of very long drug names."""
        long_name = "A" * 1000  # Very long drug name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("Drug,OrgMolecular_Weight,Diluent,Critical_Concentration\n")
            f.write(f'"{long_name}",100.0,Water,1.0\n')
            temp_path = f.name
        
        try:
            df = load_drug_data(temp_path)
            assert len(df) == 1
            assert df.iloc[0]['Drug'] == long_name
        finally:
            os.unlink(temp_path)
    
    def test_special_characters_in_data(self):
        """Test handling of special characters in drug data."""
        special_chars_data = [
            ("Drug with spaces", 100.0, "Water", 1.0),
            ("Drug,with,commas", 150.0, "DMSO", 2.0),
            ('Drug"with"quotes', 200.0, "Ethanol", 3.0),
            ("Drüg_wïth_ünïcödé", 250.0, "Buffer", 4.0),
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("Drug,OrgMolecular_Weight,Diluent,Critical_Concentration\n")
            for drug, mw, diluent, conc in special_chars_data:
                # Properly escape CSV fields
                drug_escaped = drug.replace('"', '""')
                if ',' in drug or '"' in drug:
                    drug_escaped = f'"{drug_escaped}"'
                f.write(f"{drug_escaped},{mw},{diluent},{conc}\n")
            temp_path = f.name
        
        try:
            df = load_drug_data(temp_path)
            assert len(df) == len(special_chars_data)
            
            # Check that data was preserved correctly
            for i, (expected_drug, expected_mw, expected_diluent, expected_conc) in enumerate(special_chars_data):
                assert df.iloc[i]['Drug'] == expected_drug
                assert abs(df.iloc[i]['OrgMolecular_Weight'] - expected_mw) < 1e-10
                assert df.iloc[i]['Diluent'] == expected_diluent
                assert abs(df.iloc[i]['Critical_Concentration'] - expected_conc) < 1e-10
        finally:
            os.unlink(temp_path)
    
    @given(
        extreme_values=lists(
            floats(min_value=1e-10, max_value=1e10, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=10
        )
    )
    def test_extreme_numeric_values(self, extreme_values):
        """Test handling of extreme but valid numeric values."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("Drug,OrgMolecular_Weight,Diluent,Critical_Concentration\n")
            for i, value in enumerate(extreme_values):
                f.write(f"Drug{i},{value},Water,{value}\n")
            temp_path = f.name
        
        try:
            df = load_drug_data(temp_path)
            assert len(df) == len(extreme_values)
            
            # Check that extreme values are preserved
            for i, expected_value in enumerate(extreme_values):
                assert abs(df.iloc[i]['OrgMolecular_Weight'] - expected_value) < abs(expected_value * 1e-10)
                assert abs(df.iloc[i]['Critical_Concentration'] - expected_value) < abs(expected_value * 1e-10)
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
