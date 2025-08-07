import unittest
from hypothesis import given, strategies as st
import math
from db.src import dst_calc

class TestDstCalc(unittest.TestCase):
    @given(st.floats(min_value=0.1, max_value=1000), st.floats(min_value=0.1, max_value=1000))
    def test_potency(self, mol_purch, mol_org):
        result = dst_calc.potency(mol_purch, mol_org)
        self.assertIsInstance(result, float)
        self.assertAlmostEqual(result, mol_purch / mol_org)

    @given(
        st.floats(min_value=0.1, max_value=100),
        st.floats(min_value=0.1, max_value=1000),
        st.floats(min_value=0.01, max_value=10)
    )
    def test_est_drugweight(self, conc_crit, vol_stock, potency):
        result = dst_calc.est_drugweight(conc_crit, vol_stock, potency)
        self.assertIsInstance(result, float)

    @given(
        st.floats(min_value=0.1, max_value=1000),
        st.floats(min_value=0.1, max_value=1000),
        st.floats(min_value=0.1, max_value=1000)
    )
    def test_vol_diluent(self, est_drugweight, act_drugweight, desired_totalvol):
        result = dst_calc.vol_diluent(est_drugweight, act_drugweight, desired_totalvol)
        self.assertIsInstance(result, float)

    @given(
        st.floats(min_value=0.1, max_value=1000),
        st.floats(min_value=0.1, max_value=1000)
    )
    def test_conc_stock(self, act_drugweight, vol_diluent):
        result = dst_calc.conc_stock(act_drugweight, vol_diluent)
        self.assertIsInstance(result, float)

    @given(st.floats(min_value=0.1, max_value=1000))
    def test_conc_mgit(self, crit_concentration):
        result = dst_calc.conc_mgit(crit_concentration)
        self.assertIsInstance(result, float)

    @given(st.integers(min_value=1, max_value=100))
    def test_vol_workingsol(self, num_mgits):
        result = dst_calc.vol_workingsol(num_mgits)
        self.assertIsInstance(result, float)

    @given(
        st.floats(min_value=0.1, max_value=1000),
        st.floats(min_value=0.1, max_value=1000),
        st.floats(min_value=0.1, max_value=1000)
    )
    def test_vol_ss_to_ws(self, vol_workingsol, conc_mgit, conc_stock):
        result = dst_calc.vol_ss_to_ws(vol_workingsol, conc_mgit, conc_stock)
        self.assertIsInstance(result, float)

    @given(
        st.floats(min_value=0.1, max_value=1000),
        st.floats(min_value=0.1, max_value=1000)
    )
    def test_vol_final_dil(self, vol_ss_to_ws, vol_workingsol):
        result = dst_calc.vol_final_dil(vol_ss_to_ws, vol_workingsol)
        self.assertIsInstance(result, float)

    @given(
        st.floats(min_value=0.1, max_value=1000),
        st.floats(min_value=0.1, max_value=1000)
    )
    def test_vol_ssleft(self, vol_ss_to_ws, vol_diluent):
        result = dst_calc.vol_ssleft(vol_ss_to_ws, vol_diluent)
        self.assertIsInstance(result, float)

if __name__ == "__main__":
    unittest.main()
