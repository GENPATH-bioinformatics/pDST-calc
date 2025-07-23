import unittest
from unittest.mock import patch
import pandas as pd
from cli import main

class TestCliMain(unittest.TestCase):   
    
    def setUp(self):
        # Create a small sample DataFrame
        self.df = pd.DataFrame({
            'Drug': ['DrugA', 'DrugB', 'DrugC'],
            'MolecularWeight': [100, 200, 300],
            'Critical_Concentration': [1, 2, 3]
        })

    @patch('builtins.input', side_effect=['1 2', 'y'])
    def test_select_drugs(self, mock_input):
        """Test that select_drugs returns the correct drugs based on user input."""
        result = main.select_drugs(self.df)
        self.assertListEqual(list(result['Drug']), ['DrugA', 'DrugB'])

    @patch('builtins.input', side_effect=['y','6'])
    def test_custom_critical_values(self, mock_input):
        """Test that custom_critical_values updates the critical values for selected drugs based on user input."""
        results = main.custom_critical_values(self.df)
        self.a

    def test_purchased_weights(self):
        """Test that purchased_weights collects and validates user input for purchased molecular weights and updates the dataframe."""
        pass

    def test_stock_volume(self):
        """Test that stock_volume collects and validates user input for stock solution volumes and updates the dataframe."""
        pass

    def test_act_drugweight(self):
        """Test that act_drugweight collects and validates user input for actual drug weights and updates the dataframe."""
        pass

    def test_mgit_tubes(self):
        """Test that mgit_tubes collects and validates user input for the number of MGIT tubes and updates the dataframe."""
        pass

    def test_main(self):
        """Test the main workflow, including integration of all steps and correct final output."""
        pass

if __name__ == "__main__":
    unittest.main() 