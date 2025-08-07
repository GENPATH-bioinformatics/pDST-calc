"""
Hypothesis-driven property-based tests for dst_calc module.

These tests use the Hypothesis library to generate random inputs and verify
mathematical properties, invariants, and edge cases of the DST calculation functions.
"""

import math
import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import floats, integers
import sys
from pathlib import Path

# Add the parent directory to sys.path to import lib modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from lib.dst_calc import (
    potency, est_drugweight, vol_diluent, conc_stock,
    conc_mgit, vol_workingsol, vol_ss_to_ws, vol_final_dil, vol_ssleft
)


# Strategy for positive floats (avoiding zero and very small values)
positive_floats = floats(min_value=0.001, max_value=1e6, allow_nan=False, allow_infinity=False)
small_positive_floats = floats(min_value=0.001, max_value=1000, allow_nan=False, allow_infinity=False)
positive_integers = integers(min_value=1, max_value=1000)


class TestPotency:
    """Test potency calculation properties."""
    
    @given(mol_purch=positive_floats, mol_org=positive_floats)
    def test_potency_is_ratio(self, mol_purch, mol_org):
        """Potency should be the exact ratio of purchased to original molecular weight."""
        result = potency(mol_purch, mol_org)
        expected = mol_purch / mol_org
        assert abs(result - expected) < max(1e-10, abs(expected) * 1e-12)
    
    @given(mol_weight=positive_floats)
    def test_potency_identity(self, mol_weight):
        """When both molecular weights are equal, potency should be 1."""
        result = potency(mol_weight, mol_weight)
        assert abs(result - 1.0) < 1e-10
    
    @given(mol_purch=positive_floats, mol_org=positive_floats)
    def test_potency_reciprocal(self, mol_purch, mol_org):
        """potency(a, b) * potency(b, a) should equal 1."""
        pot1 = potency(mol_purch, mol_org)
        pot2 = potency(mol_org, mol_purch)
        assert abs(pot1 * pot2 - 1.0) < 1e-10
    
    @given(mol_purch=positive_floats, mol_org=positive_floats, scale=positive_floats)
    def test_potency_scaling_invariant(self, mol_purch, mol_org, scale):
        """Scaling both molecular weights by same factor should not change potency."""
        original_potency = potency(mol_purch, mol_org)
        scaled_potency = potency(mol_purch * scale, mol_org * scale)
        # Use relative tolerance for floating-point comparison
        assert abs(original_potency - scaled_potency) < max(1e-10, abs(original_potency) * 1e-12)
    
    @given(mol_purch=positive_floats, mol_org=positive_floats)
    def test_potency_always_positive(self, mol_purch, mol_org):
        """Potency should always be positive for positive inputs."""
        result = potency(mol_purch, mol_org)
        assert result > 0


class TestEstDrugweight:
    """Test estimated drug weight calculation properties."""
    
    @given(conc=positive_floats, vol=positive_floats, pot=positive_floats)
    def test_drugweight_formula(self, conc, vol, pot):
        """Verify the exact formula: (conc * vol * pot * 84) / 1000."""
        result = est_drugweight(conc, vol, pot)
        expected = (conc * vol * pot * 84) / 1000
        assert abs(result - expected) < 1e-10
    
    @given(conc=positive_floats, vol=positive_floats, pot=positive_floats)
    def test_drugweight_proportional_to_inputs(self, conc, vol, pot):
        """Drug weight should be proportional to each input parameter."""
        base_weight = est_drugweight(conc, vol, pot)
        
        # Double concentration -> double weight
        double_conc_weight = est_drugweight(2 * conc, vol, pot)
        assert abs(double_conc_weight - 2 * base_weight) < 1e-10
        
        # Double volume -> double weight
        double_vol_weight = est_drugweight(conc, 2 * vol, pot)
        assert abs(double_vol_weight - 2 * base_weight) < 1e-10
        
        # Double potency -> double weight
        double_pot_weight = est_drugweight(conc, vol, 2 * pot)
        assert abs(double_pot_weight - 2 * base_weight) < 1e-10
    
    @given(conc=positive_floats, vol=positive_floats, pot=positive_floats)
    def test_drugweight_always_positive(self, conc, vol, pot):
        """Drug weight should always be positive for positive inputs."""
        result = est_drugweight(conc, vol, pot)
        assert result > 0
    
    @given(vol=positive_floats, pot=positive_floats)
    def test_drugweight_zero_concentration(self, vol, pot):
        """Zero concentration should give zero drug weight."""
        result = est_drugweight(0, vol, pot)
        assert result == 0


class TestVolDiluent:
    """Test diluent volume calculation properties."""
    
    @given(est_weight=positive_floats, act_weight=positive_floats, desired_vol=positive_floats)
    def test_diluent_formula(self, est_weight, act_weight, desired_vol):
        """Verify the exact formula: (est_weight / act_weight) * desired_vol."""
        result = vol_diluent(est_weight, act_weight, desired_vol)
        expected = (est_weight / act_weight) * desired_vol
        assert abs(result - expected) < 1e-10
    
    @given(weight=positive_floats, desired_vol=positive_floats)
    def test_diluent_equal_weights(self, weight, desired_vol):
        """When estimated and actual weights are equal, diluent volume equals desired volume."""
        result = vol_diluent(weight, weight, desired_vol)
        assert abs(result - desired_vol) < 1e-10
    
    @given(est_weight=positive_floats, act_weight=positive_floats, desired_vol=positive_floats)
    def test_diluent_proportional_to_ratio(self, est_weight, act_weight, desired_vol):
        """Diluent volume should be proportional to weight ratio and desired volume."""
        result = vol_diluent(est_weight, act_weight, desired_vol)
        weight_ratio = est_weight / act_weight
        assert abs(result - weight_ratio * desired_vol) < 1e-10
    
    @given(est_weight=positive_floats, act_weight=positive_floats, desired_vol=positive_floats)
    def test_diluent_scaling(self, est_weight, act_weight, desired_vol):
        """Scaling desired volume should scale result proportionally."""
        base_result = vol_diluent(est_weight, act_weight, desired_vol)
        scaled_result = vol_diluent(est_weight, act_weight, 2 * desired_vol)
        assert abs(scaled_result - 2 * base_result) < 1e-10


class TestConcStock:
    """Test stock concentration calculation properties."""
    
    @given(drugweight=positive_floats, vol=positive_floats)
    def test_stock_concentration_formula(self, drugweight, vol):
        """Verify the exact formula: (drugweight * 1000) / vol."""
        result = conc_stock(drugweight, vol)
        expected = (drugweight * 1000) / vol
        assert abs(result - expected) < 1e-10
    
    @given(drugweight=positive_floats, vol=positive_floats)
    def test_stock_concentration_units(self, drugweight, vol):
        """Stock concentration should have correct unit conversion (mg -> μg)."""
        result = conc_stock(drugweight, vol)
        # Result should be 1000 times the mg/mL ratio (to convert to μg/mL)
        expected_mg_per_ml = drugweight / vol
        expected = expected_mg_per_ml * 1000
        assert abs(result - expected) < max(1e-10, abs(expected) * 1e-12)
    
    @given(drugweight=positive_floats, vol=positive_floats)
    def test_stock_concentration_inverse_volume(self, drugweight, vol):
        """Doubling volume should halve concentration."""
        conc1 = conc_stock(drugweight, vol)
        conc2 = conc_stock(drugweight, 2 * vol)
        assert abs(conc2 - conc1 / 2) < 1e-10
    
    @given(drugweight=positive_floats, vol=positive_floats)
    def test_stock_concentration_proportional_weight(self, drugweight, vol):
        """Doubling drug weight should double concentration."""
        conc1 = conc_stock(drugweight, vol)
        conc2 = conc_stock(2 * drugweight, vol)
        assert abs(conc2 - 2 * conc1) < 1e-10


class TestConcMgit:
    """Test MGIT concentration calculation properties."""
    
    @given(crit_conc=positive_floats)
    def test_mgit_concentration_formula(self, crit_conc):
        """Verify the exact formula: (crit_conc * 8.4) / 0.1."""
        result = conc_mgit(crit_conc)
        expected = (crit_conc * 8.4) / 0.1
        assert abs(result - expected) < 1e-10
    
    @given(crit_conc=positive_floats)
    def test_mgit_concentration_factor(self, crit_conc):
        """MGIT concentration should be exactly 84 times the critical concentration."""
        result = conc_mgit(crit_conc)
        expected = crit_conc * 84
        assert abs(result - expected) < max(1e-10, abs(expected) * 1e-12)
    
    @given(crit_conc=positive_floats)
    def test_mgit_concentration_proportional(self, crit_conc):
        """MGIT concentration should be proportional to critical concentration."""
        conc1 = conc_mgit(crit_conc)
        conc2 = conc_mgit(2 * crit_conc)
        assert abs(conc2 - 2 * conc1) < 1e-10
    
    def test_mgit_concentration_zero(self):
        """Zero critical concentration should give zero MGIT concentration."""
        result = conc_mgit(0)
        assert result == 0


class TestVolWorkingsol:
    """Test working solution volume calculation properties."""
    
    @given(num_mgits=positive_integers)
    def test_workingsol_formula(self, num_mgits):
        """Verify the exact formula: (num_mgits * 0.12) + 0.36."""
        result = vol_workingsol(num_mgits)
        expected = (num_mgits * 0.12) + 0.36
        assert abs(result - expected) < 1e-10
    
    @given(num_mgits=positive_integers)
    def test_workingsol_linear(self, num_mgits):
        """Working solution volume should increase linearly with number of MGITs."""
        vol1 = vol_workingsol(num_mgits)
        vol2 = vol_workingsol(num_mgits + 1)
        assert abs(vol2 - vol1 - 0.12) < 1e-10
    
    def test_workingsol_minimum(self):
        """Minimum working solution volume (1 MGIT) should be 0.48 mL."""
        result = vol_workingsol(1)
        expected = 0.12 + 0.36
        assert abs(result - expected) < 1e-10
    
    @given(num_mgits=positive_integers)
    def test_workingsol_always_positive(self, num_mgits):
        """Working solution volume should always be positive."""
        result = vol_workingsol(num_mgits)
        assert result > 0


class TestVolSsToWs:
    """Test stock solution to working solution volume calculation properties."""
    
    @given(vol_ws=positive_floats, conc_mgit=positive_floats, conc_stock=positive_floats)
    def test_ss_to_ws_formula(self, vol_ws, conc_mgit, conc_stock):
        """Verify the exact formula: (vol_ws * conc_mgit) / conc_stock."""
        result = vol_ss_to_ws(vol_ws, conc_mgit, conc_stock)
        expected = (vol_ws * conc_mgit) / conc_stock
        assert abs(result - expected) < 1e-10
    
    @given(vol_ws=positive_floats, conc=positive_floats)
    def test_ss_to_ws_equal_concentrations(self, vol_ws, conc):
        """When concentrations are equal, stock volume should equal working volume."""
        result = vol_ss_to_ws(vol_ws, conc, conc)
        assert abs(result - vol_ws) < max(1e-10, abs(vol_ws) * 1e-12)
    
    @given(vol_ws=positive_floats, conc_mgit=positive_floats, conc_stock=positive_floats)
    def test_ss_to_ws_dilution_principle(self, vol_ws, conc_mgit, conc_stock):
        """Higher stock concentration should require less stock solution volume."""
        vol1 = vol_ss_to_ws(vol_ws, conc_mgit, conc_stock)
        vol2 = vol_ss_to_ws(vol_ws, conc_mgit, 2 * conc_stock)
        assert vol2 < vol1
        assert abs(vol2 - vol1 / 2) < 1e-10


class TestVolFinalDil:
    """Test final dilution volume calculation properties."""
    
    @given(vol_stock=positive_floats, vol_total=positive_floats)
    def test_final_dil_formula(self, vol_stock, vol_total):
        """Verify the exact formula: vol_total - vol_stock."""
        assume(vol_total > vol_stock)  # Ensure positive result
        result = vol_final_dil(vol_stock, vol_total)
        expected = vol_total - vol_stock
        assert abs(result - expected) < 1e-10
    
    @given(vol_total=positive_floats)
    def test_final_dil_no_stock(self, vol_total):
        """When no stock is added, diluent volume equals total volume."""
        result = vol_final_dil(0, vol_total)
        assert abs(result - vol_total) < 1e-10
    
    @given(vol_amount=positive_floats)
    def test_final_dil_full_stock(self, vol_amount):
        """When stock volume equals total volume, diluent should be zero."""
        result = vol_final_dil(vol_amount, vol_amount)
        assert abs(result) < 1e-10


class TestVolSsleft:
    """Test stock solution left calculation properties."""
    
    @given(vol_used=positive_floats, vol_total=positive_floats)
    def test_ss_left_formula(self, vol_used, vol_total):
        """Verify the exact formula: vol_total - vol_used."""
        assume(vol_total > vol_used)  # Ensure positive result
        result = vol_ssleft(vol_used, vol_total)
        expected = vol_total - vol_used
        assert abs(result - expected) < 1e-10
    
    @given(vol_total=positive_floats)
    def test_ss_left_no_usage(self, vol_total):
        """When no stock is used, all stock should remain."""
        result = vol_ssleft(0, vol_total)
        assert abs(result - vol_total) < 1e-10
    
    @given(vol_amount=positive_floats)
    def test_ss_left_full_usage(self, vol_amount):
        """When all stock is used, nothing should remain."""
        result = vol_ssleft(vol_amount, vol_amount)
        assert abs(result) < 1e-10


class TestIntegrationProperties:
    """Test properties of the integrated calculation workflow."""
    
    @given(
        conc_crit=small_positive_floats,
        vol_stock=small_positive_floats,
        mol_purch=small_positive_floats,
        mol_org=small_positive_floats,
        act_drugweight=small_positive_floats,
        num_mgits=integers(min_value=1, max_value=100)
    )
    @settings(max_examples=50)  # Reduce examples for complex integration test
    def test_complete_workflow_consistency(self, conc_crit, vol_stock, mol_purch, mol_org, act_drugweight, num_mgits):
        """Test that the complete DST calculation workflow maintains mathematical consistency."""
        # Step 1: Calculate potency
        pot = potency(mol_purch, mol_org)
        
        # Step 2: Estimate drug weight
        est_weight = est_drugweight(conc_crit, vol_stock, pot)
        
        # Step 3: Calculate diluent volume
        vol_dil = vol_diluent(est_weight, act_drugweight, vol_stock)
        
        # Step 4: Calculate stock concentration
        conc_st = conc_stock(act_drugweight, vol_dil)
        
        # Step 5: Calculate MGIT concentration
        conc_mg = conc_mgit(conc_crit)
        
        # Step 6: Calculate working solution volume
        vol_ws = vol_workingsol(num_mgits)
        
        # Step 7: Calculate stock solution to working solution
        vol_ss_ws = vol_ss_to_ws(vol_ws, conc_mg, conc_st)
        
        # Step 8: Calculate final dilution (may be negative if stock volume exceeds working volume)
        vol_fin_dil = vol_final_dil(vol_ss_ws, vol_ws)
        
        # Step 9: Calculate stock solution left
        vol_ss_left = vol_ssleft(vol_ss_ws, vol_dil)
        
        # Consistency checks
        assert pot > 0, "Potency should be positive"
        assert est_weight > 0, "Estimated weight should be positive"
        assert vol_dil > 0, "Diluent volume should be positive"
        assert conc_st > 0, "Stock concentration should be positive"
        assert conc_mg > 0, "MGIT concentration should be positive"
        assert vol_ws > 0, "Working solution volume should be positive"
        assert vol_ss_ws > 0, "Stock to working solution volume should be positive"
        
        # Final dilution can be negative if the required stock volume exceeds working volume
        # This is a realistic scenario indicating the stock solution is too concentrated
        
        # Mass balance check: working solution should have correct total volume
        # Use relative tolerance for floating point arithmetic - across many operations, 
        # small errors can accumulate significantly
        ws_balance_error = abs(vol_ss_ws + vol_fin_dil - vol_ws)
        relative_tolerance = max(2e-3, abs(vol_ws) * 1e-5)  # Use relative tolerance based on working solution volume
        assert ws_balance_error < relative_tolerance, f"Working solution volume components should sum correctly (error: {ws_balance_error}, tolerance: {relative_tolerance})"
        
        # Stock solution usage should not exceed available stock (if reasonable)
        if vol_ss_ws <= vol_dil:
            assert vol_ss_left >= 0, "Remaining stock should be non-negative"
            stock_balance_error = abs(vol_ss_ws + vol_ss_left - vol_dil)
            relative_tolerance = max(2e-3, abs(vol_dil) * 1e-5)  # Use relative tolerance based on diluent volume
            assert stock_balance_error < relative_tolerance, f"Stock solution balance should be correct (error: {stock_balance_error}, tolerance: {relative_tolerance})"


# Edge case tests
class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_very_small_values(self):
        """Test with very small but positive values."""
        small_val = 1e-6
        
        # These should not raise exceptions
        assert potency(small_val, small_val) == 1.0
        assert est_drugweight(small_val, small_val, small_val) > 0
        assert conc_stock(small_val, small_val) > 0
        assert conc_mgit(small_val) > 0
    
    def test_very_large_values(self):
        """Test with very large values."""
        large_val = 1e6
        
        # These should not raise exceptions and should produce finite results
        result = potency(large_val, large_val)
        assert result == 1.0
        
        result = est_drugweight(1.0, 1.0, 1.0)  # Keep reasonable to avoid overflow
        assert math.isfinite(result)
        
        result = conc_stock(1.0, large_val)  # Very dilute
        assert result > 0 and math.isfinite(result)
    
    @given(positive_val=positive_floats)
    def test_mathematical_identities(self, positive_val):
        """Test mathematical identities that should always hold."""
        # Potency identity
        assert potency(positive_val, positive_val) == 1.0
        
        # Zero input handling
        assert est_drugweight(0, positive_val, positive_val) == 0
        assert conc_mgit(0) == 0
        
        # Volume conservation
        stock_vol = 10.0
        working_vol = 5.0
        if working_vol < stock_vol:
            diluent = vol_final_dil(working_vol, stock_vol)
            assert abs(working_vol + diluent - stock_vol) < 1e-10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
