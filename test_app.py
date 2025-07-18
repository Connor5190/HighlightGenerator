#!/usr/bin/env python3
"""
Simple test script to verify the Flask app is working correctly
"""

import requests
import time
import os

def test_flask_server():
    """Test if Flask server is running and responding"""
    try:
        print("Testing Flask server...")
        response = requests.get('http://localhost:5000/test', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Flask server is running!")
            print(f"   Status: {data['status']}")
            print(f"   Message: {data['message']}")
            print(f"   Model loaded: {data['model_loaded']}")
            return True
        else:
            print(f"❌ Server responded with status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask server. Make sure it's running on localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        return False

def test_model_loading():
    """Test YOLO model loading time"""
    print("\nTesting YOLO model loading...")
    start_time = time.time()
    
    try:
        from ultralytics import YOLO
        model = YOLO('yolov8n.pt')
        load_time = time.time() - start_time
        print(f"✅ YOLO model loaded successfully in {load_time:.2f} seconds")
        return True
    except Exception as e:
        print(f"❌ Error loading YOLO model: {e}")
        return False

def check_directories():
    """Check if required directories exist"""
    print("\nChecking directories...")
    dirs = ['uploads', 'output', 'static/temp', 'templates', 'static/css', 'static/js']
    
    all_good = True
    for dir_path in dirs:
        if os.path.exists(dir_path):
            print(f"✅ {dir_path} exists")
        else:
            print(f"❌ {dir_path} missing")
            all_good = False
    
    return all_good

def main():
    print("🚀 Soccer Highlight Generator - Web App Test")
    print("=" * 50)
    
    # Test directories
    dirs_ok = check_directories()
    
    # Test model loading
    model_ok = test_model_loading()
    
    # Test Flask server
    server_ok = test_flask_server()
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   Directories: {'✅ OK' if dirs_ok else '❌ Issues'}")
    print(f"   YOLO Model: {'✅ OK' if model_ok else '❌ Issues'}")
    print(f"   Flask Server: {'✅ OK' if server_ok else '❌ Issues'}")
    
    if all([dirs_ok, model_ok, server_ok]):
        print("\n🎉 All tests passed! Your web app should be working correctly.")
        print("   Open http://localhost:5000 in your browser to use the app.")
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")
        
        if not server_ok:
            print("\n💡 To start the Flask server, run:")
            print("   python app.py")

if __name__ == "__main__":
    main()