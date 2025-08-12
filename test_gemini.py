#!/usr/bin/env python3
"""
Test script to verify Gemini API integration.
This script tests if the Gemini API key is working and AI functionality is enabled.
"""

import os
import sys
import json
import requests
from datetime import datetime

def test_gemini_api_key():
    """Test if the Gemini API key is valid."""
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment variables")
        return False
    
    print(f"✅ GEMINI_API_KEY found: {api_key[:10]}...")
    
    # Test Gemini API with a simple request
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": "Hello, this is a test message. Please respond with 'AI is working' if you can read this."
            }]
        }]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                text = result['candidates'][0]['content']['parts'][0]['text']
                print(f"✅ Gemini API test successful: {text[:50]}...")
                return True
            else:
                print("❌ Unexpected response format from Gemini API")
                return False
        else:
            print(f"❌ Gemini API test failed with status {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Gemini API: {e}")
        return False

def test_backend_ai_functionality():
    """Test if the backend can use Gemini for AI functionality."""
    try:
        # Import the main module to test AI functionality
        import main
        
        # Check if AI tools are available
        if hasattr(main, 'get_signals') and callable(main.get_signals):
            print("✅ Backend AI functionality is available")
            return True
        else:
            print("❌ Backend AI functionality not found")
            return False
            
    except Exception as e:
        print(f"❌ Error testing backend AI functionality: {e}")
        return False

def test_environment_setup():
    """Test the complete environment setup."""
    print("🔍 Testing Gemini Integration Setup...\n")
    
    tests = [
        ("Gemini API Key", test_gemini_api_key),
        ("Backend AI Functionality", test_backend_ai_functionality)
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
        print("🎉 Gemini integration is working! AI functionality is enabled.")
        print("\nNext steps:")
        print("1. Start the server: python unified_server.py")
        print("2. Test discovery with AI: curl -X POST http://localhost:8000/a2a/task -H 'Content-Type: application/json' -d '{\"type\":\"discovery\",\"parameters\":{\"query\":\"sports enthusiasts\"},\"taskId\":\"test\"}'")
        print("3. Check for 'proposed_segments' in the response (indicates AI is working)")
        return 0
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(test_environment_setup())
