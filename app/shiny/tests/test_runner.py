#!/usr/bin/env python3
"""
Quick test runner for Shiny app functionality.

This script provides simple commands to test the Shiny application components.
"""

import os
import sys
import subprocess

def run_shiny_tests():
    """Run all Shiny app tests."""
    print("🧪 Running Shiny App Tests...")
    print("=" * 50)
    
    # Change to project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    os.chdir(project_root)
    
    # Run tests using uv and pytest
    try:
        result = subprocess.run([
            'uv', 'run', 'pytest', 
            'app/shiny/tests/test_shiny_app.py', 
            '-v',
            '--tb=short'
        ], capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n✅ All Shiny tests passed!")
        else:
            print("\n❌ Some tests failed.")
            
        return result.returncode == 0
        
    except FileNotFoundError:
        print("❌ Error: 'uv' command not found. Please install uv or run tests manually.")
        return False

def run_quick_test():
    """Run a quick smoke test of core functionality."""
    print("🚀 Running Quick Smoke Test...")
    print("=" * 50)
    
    try:
        # Test imports
        print("📦 Testing imports...")
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        
        from app.api.drug_database import load_drug_data
        from lib.dst_calc import potency, est_drugweight
        
        # Test drug database
        print("💊 Testing drug database...")
        drug_data = load_drug_data()
        assert len(drug_data) > 0, "Drug database is empty"
        print(f"   ✓ Loaded {len(drug_data)} drugs")
        
        # Test calculations
        print("🧮 Testing calculations...")
        pot = potency(600.0, 137.14)
        assert pot > 0, "Potency calculation failed"
        print(f"   ✓ Potency calculation: {pot:.4f}")
        
        est_weight = est_drugweight(0.1, 5.0, 1.0)
        assert est_weight > 0, "Drug weight estimation failed"
        print(f"   ✓ Estimated weight: {est_weight:.4f} mg")
        
        print("\n✅ Quick test passed! Core functionality is working.")
        return True
        
    except Exception as e:
        print(f"\n❌ Quick test failed: {e}")
        return False

def show_help():
    """Show help information."""
    print("Shiny App Test Runner")
    print("=" * 20)
    print("Commands:")
    print("  python test_runner.py          - Run all tests")
    print("  python test_runner.py quick    - Run quick smoke test")
    print("  python test_runner.py help     - Show this help")
    print()
    print("Manual test commands:")
    print("  uv run pytest app/shiny/tests/test_shiny_app.py -v")
    print("  uv run python app/shiny/tests/test_shiny_app.py")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == 'quick':
            success = run_quick_test()
        elif command == 'help':
            show_help()
            success = True
        else:
            print(f"Unknown command: {command}")
            show_help()
            success = False
    else:
        success = run_shiny_tests()
    
    sys.exit(0 if success else 1)