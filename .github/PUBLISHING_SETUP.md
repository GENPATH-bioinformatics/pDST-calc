# Separate Publishing Setup for pDST-calc

This document explains how the pDST-calc project is structured to publish both the core library and CLI tool as separate packages on TestPyPI.

## Package Structure

### 1. Library Package (`pdst-calc-lib`)
- **Location**: `lib/` directory
- **Package Name**: `pdst-calc-lib`
- **Description**: Core DST calculation library
- **Contains**:
  - `dst_calc.py` - Core calculation functions
  - `drug_database.py` - Drug data loading functionality
  - `supp_calc.py` - Supporting calculation functions
- **Configuration**: `lib/pyproject.toml`

### 2. CLI Package (`pdst-calc-cli`)
- **Location**: `app/cli/` directory
- **Package Name**: `pdst-calc-cli`
- **Description**: Command-line interface for DST calculations
- **Contains**:
  - `main.py` - Main CLI application
  - `styling.py` - Terminal styling functions
- **Dependencies**: Depends on `pdst-calc-lib` from TestPyPI
- **Configuration**: `app/cli/pyproject.toml`

## Publishing Workflow

### Library Publishing
1. **Workflow File**: `.github/workflows/test-pypi-publish.yml`
2. **Triggers**: Push to main branch or manual dispatch
3. **Process**:
   - Builds the library package from `lib/` directory
   - Auto-increments version with timestamp suffix (e.g., `0.1.0.dev20240814151754`)
   - Publishes to TestPyPI as `pdst-calc-lib`

### CLI Publishing
1. **Workflow File**: `.github/workflows/test-pypi-publish-cli.yml`
2. **Triggers**: Push to main branch or manual dispatch (after library is published)
3. **Process**:
   - Waits for library to be available
   - Updates CLI's dependency to match the exact library version published
   - Builds the CLI package from `app/cli/` directory
   - Auto-increments version with timestamp suffix
   - Publishes to TestPyPI as `pdst-calc-cli`

## Installation

### Installing Both Packages from TestPyPI

Install the library:
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pdst-calc-lib
```

Install the CLI tool (includes library dependency):
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pdst-calc-cli
```

### Usage

After installing the CLI package, you can run:
```bash
pdst-calc --help
```

## Development Notes

### Import Strategy
The CLI code uses a fallback import strategy:
1. **First**: Try to import from the published `pdst-calc-lib` package
2. **Fallback**: If not available, import from local `lib/` directory for development

### Version Synchronization
- Both packages use automatic version generation with timestamps
- The CLI workflow automatically updates its dependency to match the exact library version published
- This ensures compatibility between the packages

### Directory Structure
```
pDST-calc/
├── lib/                          # Library package
│   ├── pyproject.toml           # Library configuration
│   ├── README.md
│   ├── __init__.py
│   ├── dst_calc.py
│   ├── drug_database.py
│   └── supp_calc.py
├── app/cli/                      # CLI package
│   ├── pyproject.toml           # CLI configuration
│   ├── README.md
│   ├── main.py
│   └── styling.py
├── .github/workflows/
│   ├── test-pypi-publish.yml    # Library publishing workflow
│   └── test-pypi-publish-cli.yml # CLI publishing workflow
└── ...
```

## Benefits of This Setup

1. **Separation of Concerns**: Library and CLI can be developed and versioned independently
2. **Reusability**: Other projects can use just the library without CLI dependencies
3. **Flexible Installation**: Users can install just what they need
4. **Automated Publishing**: Both packages are automatically published with proper dependency management
5. **Development Friendly**: Fallback imports allow local development without published dependencies

## Testing the Setup

1. **Local Development**: Run the CLI from the project directory - it will use local library files
2. **Published Package Testing**: Install the CLI from TestPyPI and run it - it will use the published library
3. **CI/CD**: Both workflows will run automatically on pushes to main branch

This setup provides a robust foundation for maintaining and distributing the pDST-calc tools as separate, well-organized packages.
