# Soccer Highlight Generator

A YOLOv8-based program that detects soccer players and balls in videos, allowing users to interactively highlight the player closest to the ball during video playback.

## Features

- **Real-time Detection**: Uses YOLOv8 to detect soccer players and balls in video frames
- **Interactive Video Player**: Play videos with spacebar control to highlight players
- **Closest Player Detection**: Automatically finds and highlights the player closest to any detected ball
- **Visual Feedback**: Shows bounding boxes for all detected objects
- **Image Testing**: Test detection on single images

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. The program will automatically download the YOLOv8 model on first run.

## Usage

### Interactive Video Mode

1. Run the main program:
```bash
python main.py
```

2. Choose option 1 to process a video file
3. Enter the path to your video file
4. Use these controls during playback:
   - **SPACEBAR**: Highlight the player closest to the ball
   - **'p'**: Pause/Resume video
   - **'r'**: Reset/remove highlights
   - **'q'**: Quit

### Image Testing Mode

1. Run the main program and choose option 2
2. Enter the path to an image file
3. The program will show detected players and balls, highlighting the closest player-ball pair

### Quick Testing

Run the test script to try with sample images:
```bash
python test_detection.py
```

## How It Works

1. **Object Detection**: YOLOv8 detects persons (soccer players) and sports balls in each frame
2. **Distance Calculation**: Calculates Euclidean distance between each player and ball
3. **Highlighting**: When spacebar is pressed, adds a red circle overlay on the closest player
4. **Real-time Processing**: Processes video frames in real-time during playback

## File Structure

- `main.py`: Main program with detection and video playback logic
- `test_detection.py`: Test script for quick testing
- `requirements.txt`: Python dependencies
- `screenshots/`: Sample images for testing (if available)

## Requirements

- Python 3.7+
- OpenCV
- YOLOv8 (ultralytics)
- PIL/Pillow
- NumPy

## Notes

- The program uses YOLOv8n (nano) model for faster processing
- Detection confidence threshold is set to 0.5
- Works with common video formats (MP4, AVI, MOV, MKV)
- Red circle overlay indicates the highlighted player