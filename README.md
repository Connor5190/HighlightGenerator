# Soccer Highlight Generator

An interactive AI-powered tool that automatically detects soccer players and balls in videos using YOLOv8, allowing you to create highlight reels by clicking on players to generate freeze-frame effects.

## Features

- **Real-time Object Detection**: Uses YOLOv8 to detect soccer players and balls in video streams
- **Interactive Player Selection**: Click on any player during video playbook to highlight them
- **Freeze Frame Effects**: Automatically creates 3-second freeze frames when a player is selected
- **Dynamic Highlighting**: Adds red overlay highlights that adapt to player dimensions
- **Video Export**: Saves processed videos with highlights and effects
- **Image Testing**: Test detection capabilities on single images

## Requirements

- Python 3.7+
- OpenCV
- YOLOv8 (ultralytics)
- PIL (Pillow)
- NumPy

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd soccer-highlight-generator
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. The YOLOv8 model (`yolov8n.pt`) will be downloaded automatically on first run.

## Usage

### Web Application (Recommended)

**Quick Start:**
```bash
# Option 1: Use the startup script (recommended)
python run_web_app.py

# Option 2: Manual start
python app.py
```

**Using the Web Interface:**

1. **Upload**: Drag & drop or select a video/image file
2. **Preview**: View AI detection results immediately
3. **Select Players**: Click on players in the preview to highlight them
4. **Navigate**: Use the slider to browse video frames
5. **Create Highlight**: Click "Create Highlight" to generate the video
6. **Download**: Download your processed highlight video

**Supported Formats:**
- **Videos**: MP4, AVI, MOV, MKV
- **Images**: JPG, PNG, BMP

### Desktop Application (Legacy)

1. Run the main application:
```bash
python main.py
```

2. Select option 1 to process a video file
3. Enter the path to your soccer video
4. Use the interactive controls:
   - **Mouse Click**: Click on any player to highlight them with a freeze frame
   - **'q'**: Quit and save the processed video
   - **'r'**: Reset/remove all highlights
   - **'p'**: Pause/Resume playback

### Image Testing

1. Run the application and select option 2
2. Enter the path to a soccer image
3. View detection results with automatic highlighting of the player closest to the ball

## Output

Processed videos are saved in the `output/` directory with timestamps and highlight effects applied. The output includes:
- Original video with detection overlays
- Freeze frame effects for selected players
- Dynamic red highlighting that adapts to player size

## Project Structure

```
├── main.py              # Main application file
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── yolov8n.pt          # YOLOv8 model (downloaded automatically)
├── screenshots/        # Sample screenshots/images
├── output/             # Generated highlight videos
└── uploads/            # Input video files
```

## How It Works

1. **Object Detection**: Uses YOLOv8 to identify soccer players (person class) and balls (sports ball class)
2. **Interactive Selection**: Mouse clicks are mapped to player bounding boxes
3. **Highlight Generation**: Creates dynamic red overlays with transparency and padding
4. **Freeze Frame**: Pauses video for 3 seconds when a player is selected
5. **Video Export**: Combines all effects into a final MP4 output

## Technical Details

- **Model**: YOLOv8 nano version for optimal speed/accuracy balance
- **Detection Confidence**: Minimum 50% confidence threshold
- **Video Format**: MP4 output with H.264 encoding
- **Highlight Style**: Semi-transparent red overlay with dynamic sizing

## Troubleshooting

### Common Issues

**"Processing" gets stuck during upload:**
- Large video files take time to process initially
- First frame detection typically takes 2-5 seconds
- Check browser console (F12) for error messages

**"Create Highlight" gets stuck:**
- This was fixed in the optimized version
- Make sure you're using the latest code
- Highlight generation time depends on video length
- Check terminal/console for progress updates

**Performance Issues:**
- Use smaller video files (under 100MB recommended)
- Lower resolution videos process faster
- Close other applications to free up memory
- Consider using shorter video clips for testing

**Dependencies:**
```bash
# Test if everything is working
python test_app.py

# Install missing packages
pip install -r requirements.txt

# Update packages if needed
pip install --upgrade ultralytics opencv-python flask
```

**Web App Won't Start:**
- Check if port 5000 is already in use
- Try running: `python run_web_app.py` instead of `python app.py`
- Ensure all files are in the correct directory structure

**Video Won't Upload:**
- Check file size (max 500MB)
- Ensure file format is supported (MP4, AVI, MOV, MKV)
- Try with a smaller test video first

## License

This project is open source and available under the MIT License.