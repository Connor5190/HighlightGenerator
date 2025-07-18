#!/usr/bin/env python3
"""
Startup script for Soccer Highlight Generator Web App
"""

import os
import sys
import time
import webbrowser
from threading import Timer

def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        'flask', 'ultralytics', 'opencv-python', 
        'pillow', 'numpy', 'werkzeug'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'opencv-python':
                import cv2
            elif package == 'pillow':
                import PIL
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for pkg in missing_packages:
            print(f"   - {pkg}")
        print("\n💡 Install missing packages with:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True

def create_directories():
    """Create required directories if they don't exist"""
    dirs = ['uploads', 'output', 'static/temp']
    
    for dir_path in dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"📁 Created directory: {dir_path}")

def open_browser():
    """Open browser after a short delay"""
    time.sleep(2)  # Wait for server to start
    webbrowser.open('http://localhost:5000')

def main():
    print("🚀 Starting Soccer Highlight Generator Web App")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    print("✅ Dependencies checked")
    print("✅ Directories ready")
    print("🔄 Starting Flask server...")
    print("\n📱 The web app will open in your browser automatically")
    print("🌐 Or manually go to: http://localhost:5000")
    print("\n⚠️  Note: First time loading may take a moment to download YOLO model")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Open browser after delay
    Timer(3.0, open_browser).start()
    
    # Import and run Flask app
    try:
        from app import app
        app.run(debug=False, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()