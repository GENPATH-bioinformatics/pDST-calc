# Shiny App Test Suite

This directory contains comprehensive tests for the pDST Calculator Shiny web application. The test suite ensures the reliability and correctness of PDF generation, calculation functions, data validation, and application workflows.

## 📁 Test Structure

```
app/shiny/tests/
├── __init__.py              # Python package initialization
├── test_shiny_app.py        # Main test suite
├── test_runner.py           # Custom test runner with utilities
├── run_tests.py             # Alternative test runner
└── README.md                # This documentation
```

## 🧪 Test Categories

### 1. PDF Generation Tests (`TestPDFGeneration`)
Tests the core PDF generation functionality for laboratory instructions:

- **Step 2 PDF Generation**: Tests PDF creation for drug preparation instructions
  - With stock solutions (multi-step workflow)
  - Without stock solutions (direct dilution)
  - Empty drug lists (edge case handling)

- **Step 4 PDF Generation**: Tests final results PDF with complete laboratory protocols
  - Stock solution preparation instructions
  - Working solution preparation
  - MGIT tube setup protocols

### 2. Calculation Function Tests (`TestCalculationFunctions`)
Validates the mathematical functions used throughout the application:

- **Potency Calculations**: `potency(mol_purch, mol_org)`
  - Molecular weight ratio calculations
  - Edge cases (equal weights, zero values)

- **Drug Weight Estimation**: `est_drugweight(conc_crit, vol_stock, potency)`
  - Critical concentration-based weight calculations
  - Formula: `(conc_crit * vol_stock * potency * 84) / 1000`

- **Diluent Volume Calculations**: `vol_diluent(est_drugweight, act_drugweight, desired_totalvol)`
  - Volume adjustments based on actual vs estimated weights
  - Formula: `(act_drugweight / est_drugweight) * desired_totalvol`

### 3. Data Validation Tests (`TestDataValidation`)
Ensures data integrity and database functionality:

- **Drug Database Loading**: Validates the SQLite database connection and data retrieval
- **Data Integrity**: Checks for required columns, null values, and data types
- **Available Drugs**: Verifies the 21 supported anti-tuberculosis drugs

### 4. Application Logic Tests (`TestAppLogic`)
Tests core application components and utilities:

- **Unit Functions**: Weight (mg) and volume (ml) unit consistency
- **Basic App Components**: Foundational application logic

### 5. Error Handling Tests (`TestErrorHandling`)
Validates graceful handling of invalid inputs and edge cases:

- **PDF Generation Errors**: Tests behavior with malformed data
- **Calculation Errors**: Tests mathematical functions with invalid inputs
- **Type Safety**: Ensures proper error types are raised

### 6. Integration Tests (`TestIntegration`)
End-to-end workflow testing:

- **Complete Stock Workflow**: Tests entire calculation pipeline
- **Multi-Step Validation**: Verifies data flow between calculation steps
- **Real Drug Data**: Uses actual database entries for realistic testing

## 🚀 Running Tests

### Quick Start
```bash
# Run all tests
cd /home/bea-loubser/Desktop/dstcalc
uv run pytest app/shiny/tests/test_shiny_app.py -v

# Or use the custom test runner
python app/shiny/tests/test_runner.py
```

### Test Runner Options

#### 1. Full Test Suite
```bash
# Using pytest (recommended)
uv run pytest app/shiny/tests/test_shiny_app.py -v

# Using unittest directly
uv run python app/shiny/tests/test_shiny_app.py

# Using custom runner
python app/shiny/tests/test_runner.py
```

#### 2. Quick Smoke Test
```bash
# Fast validation of core functionality
python app/shiny/tests/test_runner.py quick
```

#### 3. Specific Test Classes
```bash
# Test only PDF generation
uv run pytest app/shiny/tests/test_shiny_app.py::TestPDFGeneration -v

# Test only calculations
uv run pytest app/shiny/tests/test_shiny_app.py::TestCalculationFunctions -v

# Test only data validation
uv run pytest app/shiny/tests/test_shiny_app.py::TestDataValidation -v
```

#### 4. Individual Test Methods
```bash
# Test specific functionality
uv run pytest app/shiny/tests/test_shiny_app.py::TestPDFGeneration::test_generate_step2_pdf_with_stock -v
```

## 📊 Test Coverage

The test suite covers:

- ✅ **PDF Generation**: Step 2 and Step 4 PDF creation with ReportLab
- ✅ **Mathematical Functions**: All DST calculation formulas
- ✅ **Database Operations**: Drug data loading and validation
- ✅ **Error Handling**: Invalid input processing and graceful failures
- ✅ **Integration Workflows**: Complete calculation pipelines
- ✅ **Edge Cases**: Empty inputs, boundary conditions, and type safety

### Supported Drug Testing
The tests use real drugs from the database:
- Amikacin (AMK)
- Bedaquiline (BDQ)
- Clofazimine (CFZ)
- Cycloserine (CYC)
- Delamanid (DMD)
- And 16 others...

## 🔧 Test Dependencies

### Required Packages
All dependencies are managed through the project's `pyproject.toml`:

```toml
dependencies = [
    "reportlab>=4.0.0",    # PDF generation
    "pandas>=2.3.1",       # Data manipulation
    "shiny>=1.4.0",        # Web framework
    "numpy>=2.2.6",        # Numerical computations
]

[dependency-groups]
test = [
    "pytest>=8",           # Test framework
    "pytest-cov>=6.0.0",  # Coverage reporting
    "hypothesis>=6.135.32" # Property-based testing
]
```

### Test Environment Setup
```bash
# Install all dependencies including test tools
uv sync

# Or install specific test dependencies
uv add --group test pytest pytest-cov
```

## 📝 Writing New Tests

### Test Structure Template
```python
class TestNewFeature(unittest.TestCase):
    """Test new feature functionality."""
    
    def setUp(self):
        """Set up test data before each test method."""
        self.test_data = {
            'input': 'value',
            'expected': 'result'
        }
    
    def test_basic_functionality(self):
        """Test basic feature operation."""
        # Arrange
        input_data = self.test_data['input']
        expected = self.test_data['expected']
        
        # Act
        result = function_to_test(input_data)
        
        # Assert
        self.assertEqual(result, expected)
    
    def test_error_handling(self):
        """Test error conditions."""
        with self.assertRaises(ExpectedExceptionType):
            function_to_test(invalid_input)
```

### Best Practices

1. **Test Naming**: Use descriptive names that explain what is being tested
2. **Test Independence**: Each test should be able to run independently
3. **Edge Cases**: Always include boundary conditions and error cases
4. **Real Data**: Use actual drug names and realistic values when possible
5. **Documentation**: Include docstrings explaining test purpose

### Common Patterns

```python
# Testing PDF generation
def test_pdf_generation(self):
    pdf_data = generate_pdf_function(test_inputs)
    self.assertIsNotNone(pdf_data)
    self.assertIsInstance(pdf_data, bytes)
    self.assertGreater(len(pdf_data), 1000)  # Reasonable size

# Testing calculations
def test_calculation(self):
    result = calculation_function(input_val)
    self.assertAlmostEqual(result, expected_val, places=6)
    self.assertGreater(result, 0)  # Positive result expected

# Testing error handling
def test_error_case(self):
    with self.assertRaises(ValueError):
        function_with_validation(invalid_input)
```

## 🐛 Debugging Test Failures

### Common Issues and Solutions

#### 1. PDF Generation Failures
```bash
# Check if ReportLab is installed
uv run python -c "import reportlab; print('ReportLab OK')"

# Verify test data format
# Ensure drug names exist in database
```

#### 2. Database Connection Issues
```bash
# Verify database file exists
ls -la dstcalc.db

# Test database loading
uv run python -c "from app.api.drug_database import load_drug_data; print(len(load_drug_data()))"
```

#### 3. Import Errors
```bash
# Check Python path
uv run python -c "import sys; print(sys.path)"

# Verify module structure
find . -name "*.py" | head -10
```

### Verbose Test Output
```bash
# Run with maximum verbosity
uv run pytest app/shiny/tests/test_shiny_app.py -vvv --tb=long

# Show print statements
uv run pytest app/shiny/tests/test_shiny_app.py -v -s
```

## 📈 Continuous Integration

The tests are designed to work with CI/CD pipelines:

```yaml
# Example GitHub Actions integration
- name: Run Shiny Tests
  run: |
    uv sync
    uv run pytest app/shiny/tests/test_shiny_app.py -v --junit-xml=test-results.xml
```

## 🔍 Test Maintenance

### Regular Maintenance Tasks

1. **Update Test Data**: Keep drug names and molecular weights current
2. **Add New Features**: Write tests for new PDF features or calculations
3. **Performance Testing**: Monitor test execution time
4. **Coverage Analysis**: Ensure new code is tested

### Adding Support for New Drugs
When adding new drugs to the database:

1. Update test data in `setUp()` methods
2. Add integration tests with new drug names
3. Verify PDF generation with new drug properties
4. Test special handling requirements (e.g., DMSO, light sensitivity)

## 📞 Support

For test-related issues:

1. Check this README for common solutions
2. Review test output for specific error messages
3. Verify all dependencies are installed with `uv sync`
4. Ensure the database file `dstcalc.db` is present and readable

---

*This test suite ensures the reliability of the pDST Calculator for laboratory use in tuberculosis drug susceptibility testing.*