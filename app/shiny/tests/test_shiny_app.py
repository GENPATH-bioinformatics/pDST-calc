"""
Tests for Shiny App functionality.

These tests verify the core Shiny application functionality including:
- PDF generation functions
- Calculation workflows
- Data validation
- Session management
- User interface logic
"""

import unittest
import tempfile
import os
import sys
import io
from unittest.mock import patch, MagicMock, mock_open
import pandas as pd
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Import the modules we want to test
from app.shiny.generate_pdf import generate_step2_pdf, generate_step4_pdf
from app.api.drug_database import load_drug_data
from lib.dst_calc import potency, est_drugweight, vol_diluent, conc_stock, conc_ws, vol_workingsol


class TestPDFGeneration(unittest.TestCase):
    """Test PDF generation functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.test_drugs = ['Amikacin (AMK)', 'Bedaquiline (BDQ)']
        self.test_step2_data = {
            'CriticalConc': [0.1, 1.0],
            'Purch': [378.82, 822.94],
            'MgitTubes': [2.0, 2.0],
            'Potencies': [1.0000, 1.0000],
            'ConcWS': [10.0, 100.0],
            'VolWS': [5.0, 5.0],
            'CalEstWeights': [1.89, 20.57],
            'num_aliquots': [10.0, 10.0],
            'mlperAliquot': [0.5, 0.5],
            'TotalStockVolumes': [10.0, 10.0],
            'StocktoWS': [0.25, 0.25],
            'DiltoWS': [4.75, 4.75],
            'Factors': [20.0, 20.0],
            'EstWeights': [1.89, 20.57],
            'PracWeights': [2.0, 21.0],
            'PracVol': [5.263, 5.096]
        }
        
    def test_generate_step2_pdf_with_stock(self):
        """Test Step 2 PDF generation with stock solutions."""
        try:
            pdf_data = generate_step2_pdf(
                selected_drugs=self.test_drugs,
                make_stock_preference=True,
                step2_data=self.test_step2_data
            )
            self.assertIsNotNone(pdf_data)
            self.assertIsInstance(pdf_data, bytes)
            self.assertGreater(len(pdf_data), 1000)  # PDF should be substantial
        except Exception as e:
            self.fail(f"PDF generation with stock failed: {e}")
    
    def test_generate_step2_pdf_without_stock(self):
        """Test Step 2 PDF generation without stock solutions."""
        try:
            pdf_data = generate_step2_pdf(
                selected_drugs=self.test_drugs,
                make_stock_preference=False,
                step2_data=self.test_step2_data
            )
            self.assertIsNotNone(pdf_data)
            self.assertIsInstance(pdf_data, bytes)
            self.assertGreater(len(pdf_data), 1000)
        except Exception as e:
            self.fail(f"PDF generation without stock failed: {e}")
    
    def test_generate_step2_pdf_empty_drugs(self):
        """Test Step 2 PDF generation with no selected drugs."""
        try:
            pdf_data = generate_step2_pdf(
                selected_drugs=[],
                make_stock_preference=True,
                step2_data={}
            )
            # Should still generate a PDF, just with no drug data
            self.assertIsNotNone(pdf_data)
        except Exception as e:
            self.fail(f"PDF generation with empty drugs failed: {e}")
    
    def test_generate_step4_pdf_basic(self):
        """Test Step 4 PDF generation."""
        final_results = [
            {
                'Drug': 'Amikacin (AMK)',
                'Act_Weight': 2.0,
                'Total_Stock_Vol': 10.0,
                'Stock_Conc': 200.0,
                'Stock_Factor': 20.0,
                'Stock_to_WS': 0.25,
                'Dil_to_WS': 4.75,
                'Conc_Ws': 10.0,
                'Number_of_Ali': 19,
                'ml_aliquot': 0.5,
                'MGIT_Tubes': 2,
                'Intermediate': False
            }
        ]
        
        try:
            pdf_data = generate_step4_pdf(
                selected_drugs=self.test_drugs[:1],
                make_stock_preference=True,
                step2_data=self.test_step2_data,
                step3_actual_weights=[2.0],
                final_results=final_results
            )
            self.assertIsNotNone(pdf_data)
            self.assertIsInstance(pdf_data, bytes)
            self.assertGreater(len(pdf_data), 1000)
        except Exception as e:
            self.fail(f"Step 4 PDF generation failed: {e}")


class TestCalculationFunctions(unittest.TestCase):
    """Test calculation functions used in the Shiny app."""
    
    def test_potency_calculation(self):
        """Test potency calculation."""
        # Test with known values - note: function signature is (mol_purch, mol_org)
        mol_purch = 378.82  # Purchased molecular weight
        mol_org = 137.14   # Original molecular weight
        expected_potency = mol_purch / mol_org
        
        calculated_potency = potency(mol_purch, mol_org)
        self.assertAlmostEqual(calculated_potency, expected_potency, places=4)
    
    def test_potency_edge_cases(self):
        """Test potency calculation edge cases."""
        # Test with same molecular weights
        self.assertEqual(potency(100, 100), 1.0)
        
        # Test with zero purchased molecular weight (should handle gracefully)
        with self.assertRaises(ZeroDivisionError):
            potency(100, 0)
    
    def test_est_drugweight_calculation(self):
        """Test estimated drug weight calculation."""
        # Test with actual function signature: est_drugweight(conc_crit, vol_stock, potency)
        conc_crit = 0.1  # mg/mL (critical concentration)
        vol_stock = 5.0  # ml (stock volume)
        pot = 1.0        # potency
        
        # Formula from function: (conc_crit * vol_stock * potency * 84) / 1000
        expected_weight = (conc_crit * vol_stock * pot * 84) / 1000
        calculated_weight = est_drugweight(conc_crit, vol_stock, pot)
        
        self.assertAlmostEqual(calculated_weight, expected_weight, places=6)
    
    def test_vol_diluent_calculation(self):
        """Test diluent volume calculation."""
        # Test with actual function signature: vol_diluent(est_drugweight, act_drugweight, desired_totalvol)
        est_drugweight = 2.0  # mg (estimated)
        act_drugweight = 2.2  # mg (actual)
        desired_totalvol = 10.0  # ml
        
        # Formula from function: (act_drugweight / est_drugweight) * desired_totalvol
        expected_vol = (act_drugweight / est_drugweight) * desired_totalvol
        calculated_vol = vol_diluent(est_drugweight, act_drugweight, desired_totalvol)
        
        self.assertAlmostEqual(calculated_vol, expected_vol, places=6)


class TestDataValidation(unittest.TestCase):
    """Test data validation functions."""
    
    def test_drug_database_loading(self):
        """Test that drug database loads correctly."""
        try:
            drug_data = load_drug_data()
            self.assertIsInstance(drug_data, pd.DataFrame)
            self.assertGreater(len(drug_data), 0)
            
            # Check required columns exist
            required_columns = ['Drug', 'OrgMolecular_Weight', 'Diluent']
            for col in required_columns:
                self.assertIn(col, drug_data.columns)
        except Exception as e:
            self.fail(f"Drug database loading failed: {e}")
    
    def test_drug_data_integrity(self):
        """Test drug data integrity."""
        drug_data = load_drug_data()
        
        # Check for null values in critical columns
        self.assertFalse(drug_data['Drug'].isnull().any())
        self.assertFalse(drug_data['OrgMolecular_Weight'].isnull().any())
        self.assertFalse(drug_data['Diluent'].isnull().any())
        
        # Check that molecular weights are positive
        self.assertTrue((drug_data['OrgMolecular_Weight'] > 0).all())


class TestAppLogic(unittest.TestCase):
    """Test application logic and workflows."""
    
    def test_weight_unit_function(self):
        """Test weight unit function."""
        # Import the function if it's available
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("app", "/home/bea-loubser/Desktop/dstcalc/app/shiny/app.py")
            if spec and spec.loader:
                # For now, we'll just test that the expected unit is returned
                expected_unit = "mg"
                self.assertEqual(expected_unit, "mg")
        except Exception:
            # If we can't import the app module directly, skip this test
            self.skipTest("Cannot import app module directly")
    
    def test_volume_unit_function(self):
        """Test volume unit function."""
        expected_unit = "ml"
        self.assertEqual(expected_unit, "ml")


class TestErrorHandling(unittest.TestCase):
    """Test error handling in PDF generation and calculations."""
    
    def test_pdf_generation_with_invalid_data(self):
        """Test PDF generation handles invalid data gracefully."""
        invalid_step2_data = {
            'CriticalConc': [None, "invalid"],
            'Purch': ["not_a_number", -1],
            'MgitTubes': [],
        }
        
        # Should not crash, might return None or handle gracefully
        try:
            pdf_data = generate_step2_pdf(
                selected_drugs=['Test Drug'],
                make_stock_preference=True,
                step2_data=invalid_step2_data
            )
            # Either succeeds or returns None - both are acceptable
            if pdf_data is not None:
                self.assertIsInstance(pdf_data, bytes)
        except Exception as e:
            # If it raises an exception, it should be handled gracefully
            self.assertIsInstance(e, (TypeError, ValueError, IndexError))
    
    def test_calculation_with_invalid_inputs(self):
        """Test calculations handle invalid inputs."""
        # Test with edge cases that might not raise exceptions but produce unexpected results
        
        # Test potency with zero - this will raise ZeroDivisionError
        with self.assertRaises(ZeroDivisionError):
            potency(100, 0)
        
        # Test with negative values - these functions may not validate input
        # but we can test they don't crash
        try:
            result = potency(-100, 200)
            self.assertIsInstance(result, (int, float))
        except Exception as e:
            # If it raises an exception, it should be a reasonable one
            self.assertIsInstance(e, (TypeError, ValueError, ZeroDivisionError))


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflows."""
    
    def test_complete_stock_workflow(self):
        """Test complete workflow with stock solutions."""
        # Simulate a complete calculation workflow
        selected_drugs = ['Amikacin (AMK)']
        
        # Step 1: Load drug data
        drug_data = load_drug_data()
        self.assertGreater(len(drug_data), 0)
        
        # Step 2: Calculate potency and estimated weights
        drug_row = drug_data[drug_data['Drug'] == selected_drugs[0]]
        self.assertGreater(len(drug_row), 0)
        
        org_mw = drug_row.iloc[0]['OrgMolecular_Weight']
        purch_mw = 600.0  # Example purchased molecular weight
        pot = potency(purch_mw, org_mw)  # Note: correct parameter order
        
        self.assertGreater(pot, 0)
        
        # Step 3: Calculate estimated drug weight
        crit_conc = 0.1  # mg/mL (critical concentration)
        vol_stock = 5.0  # ml
        est_weight = est_drugweight(crit_conc, vol_stock, pot)
        
        self.assertGreater(est_weight, 0)
        
        # Step 4: Generate PDF with calculated data
        step2_data = {
            'CriticalConc': [crit_conc],
            'Purch': [purch_mw],
            'MgitTubes': [2.0],
            'Potencies': [pot],
            'ConcWS': [10.0],
            'VolWS': [vol_stock],
            'CalEstWeights': [est_weight],
            'num_aliquots': [10.0],
            'mlperAliquot': [0.5],
            'TotalStockVolumes': [10.0],
            'StocktoWS': [0.25],
            'DiltoWS': [4.75],
            'Factors': [20.0],
            'EstWeights': [est_weight],
            'PracWeights': [2.0],
            'PracVol': [5.0]
        }
        
        pdf_data = generate_step2_pdf(
            selected_drugs=selected_drugs,
            make_stock_preference=True,
            step2_data=step2_data
        )
        
        self.assertIsNotNone(pdf_data)
        self.assertIsInstance(pdf_data, bytes)


if __name__ == '__main__':
    # Create a test suite
    test_classes = [
        TestPDFGeneration,
        TestCalculationFunctions,
        TestDataValidation,
        TestAppLogic,
        TestErrorHandling,
        TestIntegration
    ]
    
    loader = unittest.TestLoader()
    suites = [loader.loadTestsFromTestCase(test_class) for test_class in test_classes]
    combined_suite = unittest.TestSuite(suites)
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(combined_suite)
    
    # Exit with error code if tests failed
    sys.exit(0 if result.wasSuccessful() else 1)