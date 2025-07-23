#!/usr/bin/env python3
"""
Basic compatibility test for Real Estate CRM module
Tests model definitions and basic functionality
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_model_imports():
    """Test that all models can be imported without errors"""
    try:
        # Test property model
        from addons.real_estate_crm.models.property_model import RealEstateProperty
        print("✓ Property model imported successfully")
        
        # Test client model
        from addons.real_estate_crm.models.client import ResPartner
        print("✓ Client model imported successfully")
        
        # Test lead model
        from addons.real_estate_crm.models.lead import RealEstateLead
        print("✓ Lead model imported successfully")
        
        # Test agent model
        from addons.real_estate_crm.models.agent import RealEstateAgent
        print("✓ Agent model imported successfully")
        
        # Test appointment model
        from addons.real_estate_crm.models.appointment import RealEstateAppointment
        print("✓ Appointment model imported successfully")
        
        # Test valuation model
        from addons.real_estate_crm.models.valuation import RealEstateValuation
        print("✓ Valuation model imported successfully")
        
        # Test contract model
        from addons.real_estate_crm.models.contract import RealEstateContract
        print("✓ Contract model imported successfully")
        
        # Test commission model
        from addons.real_estate_crm.models.commission import RealEstateCommission
        print("✓ Commission model imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_manifest():
    """Test manifest file structure"""
    try:
        import ast
        
        with open('addons/real_estate_crm/__manifest__.py', 'r') as f:
            manifest_content = f.read()
        
        # Parse manifest as Python dict
        manifest = ast.literal_eval(manifest_content)
        
        # Check required fields
        required_fields = ['name', 'version', 'depends', 'data', 'installable', 'application']
        for field in required_fields:
            if field not in manifest:
                print(f"✗ Missing required field in manifest: {field}")
                return False
        
        # Check Odoo 16 compatibility
        if not manifest['version'].startswith('16.0'):
            print(f"✗ Version should start with 16.0, got: {manifest['version']}")
            return False
        
        print("✓ Manifest file structure is valid")
        return True
        
    except Exception as e:
        print(f"✗ Manifest test error: {e}")
        return False

def test_file_structure():
    """Test that all required files exist"""
    required_files = [
        'addons/real_estate_crm/__init__.py',
        'addons/real_estate_crm/__manifest__.py',
        'addons/real_estate_crm/models/__init__.py',
        'addons/real_estate_crm/security/ir.model.access.csv',
        'addons/real_estate_crm/security/real_estate_security.xml',
        'config/odoo.conf',
        'requirements.txt',
        'README.md',
        '.gitignore'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"✗ Missing required files: {missing_files}")
        return False
    
    print("✓ All required files present")
    return True

def test_dependencies():
    """Test that requirements.txt has necessary dependencies"""
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read().lower()
        
        # Check for critical dependencies
        critical_deps = ['requests', 'psycopg2', 'pillow', 'lxml']
        missing_deps = []
        
        for dep in critical_deps:
            if dep not in requirements:
                missing_deps.append(dep)
        
        if missing_deps:
            print(f"✗ Missing critical dependencies: {missing_deps}")
            return False
        
        print("✓ Critical dependencies present in requirements.txt")
        return True
        
    except Exception as e:
        print(f"✗ Dependencies test error: {e}")
        return False

def main():
    """Run all tests"""
    print("Real Estate CRM - Compatibility Test")
    print("=" * 40)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Manifest File", test_manifest), 
        ("Dependencies", test_dependencies),
        ("Model Imports", test_model_imports),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nTesting {test_name}...")
        if test_func():
            passed += 1
        
    print("\n" + "=" * 40)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! Module is ready for Odoo 16 deployment.")
        return 0
    else:
        print("✗ Some tests failed. Please fix issues before deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(main())