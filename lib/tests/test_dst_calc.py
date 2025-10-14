import unittest
import math
import dst_calc


class TestDstCalc(unittest.TestCase):
    """Test cases for dst_calc module functions."""
    
    def test_potency_known_values(self):
        """Test potency calculation with known values."""
        # Test case: identical molecular weights should give potency of 1.0
        result = dst_calc.potency(100.0, 100.0)
        self.assertEqual(result, 1.0)
        
        # Test case: purchased weight twice the original
        result = dst_calc.potency(200.0, 100.0)
        self.assertEqual(result, 2.0)
        
        # Test case: purchased weight half the original
        result = dst_calc.potency(50.0, 100.0)
        self.assertEqual(result, 0.5)
    
    def test_potency_edge_cases(self):
        """Test potency calculation edge cases."""
        # Test very small values
        result = dst_calc.potency(0.01, 0.01)
        self.assertEqual(result, 1.0)
        
        # Test very large values
        result = dst_calc.potency(10000.0, 5000.0)
        self.assertEqual(result, 2.0)
    
    def test_est_drugweight_known_values(self):
        """Test estimated drug weight calculation with known values."""
        # Test with typical values
        conc_crit = 1.0  # mg/mL
        vol_stock = 10.0  # mL
        potency = 1.0
        expected = (1.0 * 10.0 * 1.0 * 84) / 1000  # 0.84 mg
        result = dst_calc.est_drugweight(conc_crit, vol_stock, potency)
        self.assertAlmostEqual(result, expected, places=6)
    
    def test_vol_diluent_known_values(self):
        """Test volume diluent calculation with known values."""
        # Test case: estimated equals actual weight
        result = dst_calc.vol_diluent(10.0, 10.0, 5.0)
        self.assertEqual(result, 5.0)
        
        # Test case: actual weight is half estimated
        result = dst_calc.vol_diluent(10.0, 5.0, 10.0)
        self.assertEqual(result, 20.0)
    
    def test_conc_stock_known_values(self):
        """Test stock concentration calculation with known values."""
        # Test typical values
        act_drugweight = 10.0  # mg
        vol_diluent = 5.0  # mL
        expected = (10.0 * 1000) / 5.0  # 2000 μg/mL
        result = dst_calc.conc_stock(act_drugweight, vol_diluent)
        self.assertEqual(result, expected)
    
    def test_conc_ws_known_values(self):
        """Test working solution concentration calculation with known values."""
        # Test typical critical concentration
        crit_conc = 1.0  # mg/mL
        expected = (1.0 * 8.4) / 0.1  # 84 μg/mL
        result = dst_calc.conc_ws(crit_conc)
        self.assertEqual(result, expected)
    
    def test_vol_workingsol_known_values(self):
        """Test working solution volume calculation with known values."""
        # Test with specific number of tubes
        num_mgits = 5
        expected = (5 * 0.12) + 0.36  # 0.96 mL
        result = dst_calc.vol_workingsol(num_mgits)
        self.assertEqual(result, expected)
        
        # Test with 1 tube
        result = dst_calc.vol_workingsol(1)
        self.assertEqual(result, 0.48)  # (1 * 0.12) + 0.36
    
    def test_vol_ss_to_ws_known_values(self):
        """Test stock solution to working solution volume calculation."""
        # Test typical dilution
        vol_workingsol = 1.0  # mL
        conc_ws = 84.0  # μg/mL
        conc_stock = 2000.0  # μg/mL
        expected = (1.0 * 84.0) / 2000.0  # 0.042 mL
        result = dst_calc.vol_ss_to_ws(vol_workingsol, conc_ws, conc_stock)
        self.assertAlmostEqual(result, expected, places=6)
    
    def test_vol_final_dil_known_values(self):
        """Test final dilution volume calculation."""
        # Test simple subtraction
        vol_ss_to_ws = 0.042  # mL
        vol_workingsol = 1.0  # mL
        expected = 1.0 - 0.042  # 0.958 mL
        result = dst_calc.vol_final_dil(vol_ss_to_ws, vol_workingsol)
        self.assertAlmostEqual(result, expected, places=6)
    
    def test_vol_ssleft_known_values(self):
        """Test remaining stock solution volume calculation."""
        # Test typical values
        vol_ss_to_ws = 0.042  # mL used
        vol_diluent = 5.0  # mL total
        expected = 5.0 - 0.042  # 4.958 mL remaining
        result = dst_calc.vol_ssleft(vol_ss_to_ws, vol_diluent)
        self.assertAlmostEqual(result, expected, places=6)


class TestDstCalcEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions for dst_calc functions."""
    
    def test_potency_with_various_inputs(self):
        """Test potency function with various input combinations."""
        test_cases = [
            (1.0, 1.0, 1.0),
            (2.0, 1.0, 2.0),
            (0.5, 1.0, 0.5),
            (100.5, 50.25, 2.0),
            (0.001, 0.001, 1.0)
        ]
        
        for mol_purch, mol_org, expected in test_cases:
            with self.subTest(mol_purch=mol_purch, mol_org=mol_org):
                result = dst_calc.potency(mol_purch, mol_org)
                self.assertAlmostEqual(result, expected, places=6)
    
    def test_est_drugweight_with_various_inputs(self):
        """Test est_drugweight function with various inputs."""
        test_cases = [
            (1.0, 10.0, 1.0, 0.84),  # (conc_crit, vol_stock, potency, expected)
            (2.0, 5.0, 1.0, 0.84),   # Same result due to formula
            (1.0, 20.0, 0.5, 0.84),  # Same result due to formula
        ]
        
        for conc_crit, vol_stock, potency, expected in test_cases:
            with self.subTest(conc_crit=conc_crit, vol_stock=vol_stock, potency=potency):
                result = dst_calc.est_drugweight(conc_crit, vol_stock, potency)
                self.assertAlmostEqual(result, expected, places=6)
    
    def test_all_functions_return_float(self):
        """Test that all functions return float values."""
        # Test potency
        result = dst_calc.potency(100.0, 50.0)
        self.assertIsInstance(result, float)
        
        # Test est_drugweight
        result = dst_calc.est_drugweight(1.0, 10.0, 1.0)
        self.assertIsInstance(result, float)
        
        # Test vol_diluent
        result = dst_calc.vol_diluent(10.0, 8.0, 5.0)
        self.assertIsInstance(result, float)
        
        # Test conc_stock
        result = dst_calc.conc_stock(10.0, 5.0)
        self.assertIsInstance(result, float)
        
        # Test conc_ws
        result = dst_calc.conc_ws(1.0)
        self.assertIsInstance(result, float)
        
        # Test vol_workingsol
        result = dst_calc.vol_workingsol(5)
        self.assertIsInstance(result, float)
        
        # Test vol_ss_to_ws
        result = dst_calc.vol_ss_to_ws(1.0, 84.0, 2000.0)
        self.assertIsInstance(result, float)
        
        # Test vol_final_dil
        result = dst_calc.vol_final_dil(0.042, 1.0)
        self.assertIsInstance(result, float)
        
        # Test vol_ssleft
        result = dst_calc.vol_ssleft(0.042, 5.0)
        self.assertIsInstance(result, float)
    
    def test_calculation_consistency(self):
        """Test that related calculations are consistent."""
        # Test that potency calculation is consistent
        mol_purch = 210.0
        mol_org = 200.0
        potency_result = dst_calc.potency(mol_purch, mol_org)
        expected_potency = mol_purch / mol_org
        self.assertAlmostEqual(potency_result, expected_potency, places=6)
        
        # Test that volume calculations are consistent
        est_weight = 10.0
        act_weight = 8.0
        desired_vol = 5.0
        vol_dil = dst_calc.vol_diluent(est_weight, act_weight, desired_vol)
        
        # The dilution volume should account for the weight ratio
        expected_vol = (est_weight / act_weight) * desired_vol
        self.assertAlmostEqual(vol_dil, expected_vol, places=6)


if __name__ == "__main__":
    unittest.main()
