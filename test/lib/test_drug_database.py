import unittest
import pandas as pd
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from lib import drug_database


class TestDrugDatabase(unittest.TestCase):
    """Test cases for drug_database module functions."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create sample drug data for testing
        self.sample_drug_data = {
            'Drug': ['Amikacin (AMK)', 'Bedaquiline (BDQ)', 'Clofazimine (CFZ)'],
            'OrgMolecular_Weight': [585.6, 555.5, 473.39],
            'Diluent': ['Water', 'DMSO', 'DMSO'],
            'Critical_Concentration': [1, 1, 1]
        }
        
        # Create temporary CSV file for testing
        self.temp_csv = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        pd.DataFrame(self.sample_drug_data).to_csv(self.temp_csv.name, index=False)
        self.temp_csv.close()

    def tearDown(self):
        """Clean up after each test method."""
        # Remove temporary file
        if os.path.exists(self.temp_csv.name):
            os.unlink(self.temp_csv.name)

    def test_load_drug_data_default_path(self):
        """Test loading drug data with default path."""
        # This test assumes the default data file exists
        try:
            df = drug_database.load_drug_data()
            
            # Check if DataFrame is returned
            self.assertIsInstance(df, pd.DataFrame)
            
            # Check if expected columns exist
            expected_columns = ['Drug', 'OrgMolecular_Weight', 'Diluent', 'Critical_Concentration']
            for col in expected_columns:
                self.assertIn(col, df.columns)
                
            # Check if DataFrame is not empty
            self.assertGreater(len(df), 0)
            
        except FileNotFoundError:
            self.skipTest("Default drug data file not found")

    def test_load_drug_data_custom_filepath(self):
        """Test loading drug data with custom filepath."""
        df = drug_database.load_drug_data(self.temp_csv.name)
        
        # Check if DataFrame is returned
        self.assertIsInstance(df, pd.DataFrame)
        
        # Check data content
        self.assertEqual(len(df), 3)
        self.assertEqual(list(df['Drug']), self.sample_drug_data['Drug'])
        
        # Check data types
        self.assertTrue(pd.api.types.is_numeric_dtype(df['OrgMolecular_Weight']))
        self.assertTrue(pd.api.types.is_numeric_dtype(df['Critical_Concentration']))

    def test_load_drug_data_pathlib_path(self):
        """Test loading drug data with pathlib.Path object."""
        path_obj = Path(self.temp_csv.name)
        df = drug_database.load_drug_data(path_obj)
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 3)

    def test_load_drug_data_nonexistent_file(self):
        """Test loading drug data with nonexistent file."""
        with self.assertRaises(FileNotFoundError):
            drug_database.load_drug_data('nonexistent_file.csv')

    def test_load_drug_data_invalid_csv_format(self):
        """Test loading drug data with invalid CSV format."""
        # Create temporary file with invalid content
        invalid_csv = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        invalid_csv.write("invalid,csv,content\n1,2")  # Missing column
        invalid_csv.close()
        
        try:
            # This should still work with pandas but might have unexpected structure
            df = drug_database.load_drug_data(invalid_csv.name)
            self.assertIsInstance(df, pd.DataFrame)
        except Exception:
            # Any parsing error is acceptable for invalid format
            pass
        finally:
            os.unlink(invalid_csv.name)

    def test_load_drug_data_empty_file(self):
        """Test loading drug data with empty file."""
        empty_csv = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        empty_csv.close()
        
        try:
            df = drug_database.load_drug_data(empty_csv.name)
            # Empty DataFrame should still be valid
            self.assertIsInstance(df, pd.DataFrame)
            self.assertEqual(len(df), 0)
        finally:
            os.unlink(empty_csv.name)

    def test_load_drug_data_with_missing_columns(self):
        """Test loading drug data with missing expected columns."""
        # Create CSV with different columns
        different_data = {
            'Name': ['Drug1', 'Drug2'],
            'Weight': [100.0, 200.0]
        }
        
        different_csv = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        pd.DataFrame(different_data).to_csv(different_csv.name, index=False)
        different_csv.close()
        
        try:
            df = drug_database.load_drug_data(different_csv.name)
            self.assertIsInstance(df, pd.DataFrame)
            
            # Check that unexpected columns are present
            self.assertIn('Name', df.columns)
            self.assertIn('Weight', df.columns)
            
            # Check that expected columns are missing
            self.assertNotIn('Drug', df.columns)
            
        finally:
            os.unlink(different_csv.name)

    def test_load_drug_data_with_special_characters(self):
        """Test loading drug data with special characters in drug names."""
        special_data = {
            'Drug': ['Drug-1 (TEST)', 'Drug/2 [Special]', 'Drug & More'],
            'OrgMolecular_Weight': [100.0, 200.0, 300.0],
            'Diluent': ['Water', 'DMSO', 'Water'],
            'Critical_Concentration': [1, 2, 3]
        }
        
        special_csv = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        pd.DataFrame(special_data).to_csv(special_csv.name, index=False)
        special_csv.close()
        
        try:
            df = drug_database.load_drug_data(special_csv.name)
            self.assertIsInstance(df, pd.DataFrame)
            self.assertEqual(len(df), 3)
            
            # Check that special characters are preserved
            for expected_name in special_data['Drug']:
                self.assertIn(expected_name, df['Drug'].values)
                
        finally:
            os.unlink(special_csv.name)

    def test_load_drug_data_with_nan_values(self):
        """Test loading drug data with NaN values."""
        nan_data = {
            'Drug': ['Drug1', 'Drug2', 'Drug3'],
            'OrgMolecular_Weight': [100.0, None, 300.0],
            'Diluent': ['Water', 'DMSO', None],
            'Critical_Concentration': [1, 2, None]
        }
        
        nan_csv = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        pd.DataFrame(nan_data).to_csv(nan_csv.name, index=False)
        nan_csv.close()
        
        try:
            df = drug_database.load_drug_data(nan_csv.name)
            self.assertIsInstance(df, pd.DataFrame)
            self.assertEqual(len(df), 3)
            
            # Check that NaN values are handled properly
            self.assertTrue(pd.isna(df.iloc[1]['OrgMolecular_Weight']))
            self.assertTrue(pd.isna(df.iloc[2]['Diluent']))
            
        finally:
            os.unlink(nan_csv.name)


class TestDrugDatabaseIntegration(unittest.TestCase):
    """Integration tests for drug_database module."""
    
    def test_real_data_structure(self):
        """Test that real drug data has expected structure."""
        try:
            df = drug_database.load_drug_data()
            
            # Test basic structure
            self.assertIsInstance(df, pd.DataFrame)
            
            # Test expected columns
            expected_columns = ['Drug', 'OrgMolecular_Weight', 'Diluent', 'Critical_Concentration']
            for col in expected_columns:
                self.assertIn(col, df.columns)
            
            # Test data types
            self.assertTrue(pd.api.types.is_numeric_dtype(df['OrgMolecular_Weight']))
            self.assertTrue(pd.api.types.is_numeric_dtype(df['Critical_Concentration']))
            
            # Test that there are actual drug entries
            self.assertGreater(len(df), 0)
            
            # Test that drug names are strings
            for drug_name in df['Drug']:
                if pd.notna(drug_name):
                    self.assertIsInstance(drug_name, str)
            
            # Test that molecular weights are positive
            for weight in df['OrgMolecular_Weight']:
                if pd.notna(weight):
                    self.assertGreater(weight, 0)
            
            # Test that critical concentrations are positive
            for conc in df['Critical_Concentration']:
                if pd.notna(conc):
                    self.assertGreater(conc, 0)
                    
        except FileNotFoundError:
            self.skipTest("Default drug data file not found")

    def test_drug_names_uniqueness(self):
        """Test that drug names are unique in the dataset."""
        try:
            df = drug_database.load_drug_data()
            
            # Check for duplicate drug names
            duplicate_drugs = df[df['Drug'].duplicated()]['Drug'].values
            self.assertEqual(len(duplicate_drugs), 0, 
                           f"Found duplicate drugs: {duplicate_drugs}")
            
        except FileNotFoundError:
            self.skipTest("Default drug data file not found")


if __name__ == '__main__':
    unittest.main()
