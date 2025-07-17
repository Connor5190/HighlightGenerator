#!/usr/bin/env python3
"""
Test script for soccer detection functionality
"""

import cv2
import os
from main import SoccerHighlightGenerator

def test_with_sample_images():
    """Test detection with sample images from screenshots folder"""
    generator = SoccerHighlightGenerator()
    
    # Look for images in screenshots folder
    screenshots_dir = "screenshots"
    if os.path.exists(screenshots_dir):
        image_files = [f for f in os.listdir(screenshots_dir) if f.endswith('.png')]
        
        if image_files:
            print(f"Found {len(image_files)} images in screenshots folder")
            
            # Test with first few images
            for i, image_file in enumerate(image_files[:3]):
                image_path = os.path.join(screenshots_dir, image_file)
                print(f"\nTesting with: {image_file}")
                generator.process_single_image(image_path)
                
                if i < len(image_files) - 1:
                    input("Press Enter to continue to next image...")
        else:
            print("No PNG images found in screenshots folder")
    else:
        print("Screenshots folder not found")

def test_video_detection():
    """Test with a video file"""
    generator = SoccerHighlightGenerator()
    
    # Look for video files
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
    video_files = []
    
    for ext in video_extensions:
        for file in os.listdir('.'):
            if file.lower().endswith(ext):
                video_files.append(file)
    
    if video_files:
        print(f"Found video files: {video_files}")
        video_path = video_files[0]
        print(f"Testing with: {video_path}")
        
        try:
            generator.load_video(video_path)
            generator.play_video_interactive()
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("No video files found in current directory")
        print("Please add a video file (.mp4, .avi, .mov, .mkv) to test")

if __name__ == "__main__":
    print("=== Soccer Detection Test ===")
    print("1. Test with sample images")
    print("2. Test with video file")
    
    choice = input("Choose test (1 or 2): ").strip()
    
    if choice == '1':
        test_with_sample_images()
    elif choice == '2':
        test_video_detection()
    else:
        print("Invalid choice")