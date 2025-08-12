#!/usr/bin/env python3
"""
Simple test script to verify the Signals Agent backend setup.
This script checks if the required files and structure are in place.
"""

import os
import json
import sys

def test_file_structure():
    """Test that required files exist."""
    required_files = [
        'unified_server.py',
        'sample_data.json',
        'schemas.py',
        'database.py',
        'config_loader.py',
        'requirements.txt',
        'pyproject.toml'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
        return True

def test_sample_data():
    """Test that sample_data.json is valid and contains data."""
    try:
        with open('sample_data.json', 'r') as f:
            data = json.load(f)
        
        if 'segments' in data and len(data['segments']) > 0:
            print(f"✅ Sample data loaded: {len(data['segments'])} segments")
            return True
        else:
            print("❌ Sample data is empty or invalid")
            return False
    except Exception as e:
        print(f"❌ Error loading sample data: {e}")
        return False

def test_python_syntax():
    """Test that Python files have valid syntax."""
    python_files = [
        'unified_server.py',
        'schemas.py',
        'database.py',
        'config_loader.py'
    ]
    
    for file in python_files:
        try:
            with open(file, 'r') as f:
                compile(f.read(), file, 'exec')
            print(f"✅ {file} has valid Python syntax")
        except Exception as e:
            print(f"❌ {file} has syntax errors: {e}")
            return False
    
    return True

def test_endpoints():
    """Test that the server defines the expected endpoints."""
    try:
        with open('unified_server.py', 'r') as f:
            content = f.read()
        
        required_endpoints = [
            '@app.get("/health")',
            '@app.post("/a2a/task")'
        ]
        
        missing_endpoints = []
        for endpoint in required_endpoints:
            if endpoint not in content:
                missing_endpoints.append(endpoint)
        
        if missing_endpoints:
            print(f"❌ Missing endpoints: {missing_endpoints}")
            return False
        else:
            print("✅ All required endpoints defined")
            return True
    except Exception as e:
        print(f"❌ Error checking endpoints: {e}")
        return False

def main():
    """Run all tests."""
    print("🔍 Testing Signals Agent Backend Setup...\n")
    
    tests = [
        ("File Structure", test_file_structure),
        ("Sample Data", test_sample_data),
        ("Python Syntax", test_python_syntax),
        ("API Endpoints", test_endpoints)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Testing {test_name}...")
        if test_func():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The backend is ready to run.")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Set up environment: cp env.example .env")
        print("3. Start server: python unified_server.py")
        return 0
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
