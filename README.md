# Soccer Highlight Generator

A YOLOv8-based program that detects soccer players and balls in videos, allowing users to interactively highlight the player closest to the ball during video playback. Now available as a web application for easy deployment and use.

## Features

- **Real-time Detection**: Uses YOLOv8 to detect soccer players and balls in video frames
- **Interactive Video Player**: Play videos with spacebar control to highlight players
- **Closest Player Detection**: Automatically finds and highlights the player closest to any detected ball
- **Visual Feedback**: Shows bounding boxes for all detected objects
- **Image Testing**: Test detection on single images
- **Web Interface**: Modern, responsive web UI with drag-and-drop file upload
- **Cloud Deployment**: Ready for deployment on Fly.io with Docker

## Quick Start

### Local Development

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Run the web application:
```bash
python app.py
```

3. Open your browser to `http://localhost:8080`

### Command Line Interface

1. Run the main program:
```bash
python main.py
```

2. Choose option 1 to process a video file
3. Enter the path to your video file
4. Use these controls during playback:
   - **MOUSE CLICK**: Click on any player to highlight them
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

## Web Application

### Features
- **Drag & Drop Upload**: Easy file upload with visual feedback
- **Real-time Processing**: Live progress updates during video processing
- **Multiple File Types**: Support for videos (MP4, AVI, MOV, MKV) and images (PNG, JPG, JPEG)
- **Automatic Download**: Processed videos are automatically available for download
- **Responsive Design**: Works on desktop and mobile devices

### API Endpoints
- `GET /` - Main web interface
- `GET /health` - Health check endpoint
- `POST /upload` - File upload endpoint
- `GET /status/<task_id>` - Processing status
- `GET /download/<task_id>` - Download processed file
- `POST /api/detect` - Image detection API

## Deployment

### Fly.io Deployment

This application is ready for deployment on Fly.io. See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

Quick deployment:
```bash
# Install Fly CLI
brew install flyctl

# Login to Fly.io
fly auth login

# Create volume for persistent storage (optional - not needed for free tier)
# fly volumes create highlight_data --size 10 --region iad

# Deploy the application
fly deploy
```

### Docker Deployment

The application includes a complete Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t highlightgenerator .

# Run the container
docker run -p 8080:8080 highlightgenerator
```

## How It Works

1. **Object Detection**: YOLOv8 detects persons (soccer players) and sports balls in each frame
2. **Distance Calculation**: Calculates Euclidean distance between each player and ball
3. **Highlighting**: Automatically highlights the player closest to any detected ball
4. **Real-time Processing**: Processes video frames in real-time during playback
5. **Web Interface**: Provides a modern web UI for easy file upload and processing

## File Structure

- `main.py`: Main program with detection and video playback logic
- `app.py`: Flask web application
- `test_detection.py`: Test script for quick testing
- `requirements.txt`: Python dependencies
- `templates/index.html`: Web interface template
- `fly.toml`: Fly.io configuration
- `Dockerfile`: Docker configuration
- `DEPLOYMENT.md`: Detailed deployment guide
- `screenshots/`: Sample images for testing (if available)

## Requirements

- Python 3.7+
- OpenCV
- YOLOv8 (ultralytics)
- PIL/Pillow
- NumPy
- Flask (for web interface)

## Configuration

### Web Application Settings
- **Max File Size**: 50MB (free tier limit)
- **Supported Formats**: MP4, AVI, MOV, MKV, PNG, JPG, JPEG
- **Processing**: Asynchronous background processing for videos (up to 30 seconds)
- **Storage**: Local temporary storage with automatic cleanup

### Detection Settings
- **Model**: YOLOv8n (nano) for faster processing
- **Confidence Threshold**: 0.5
- **Classes**: Person (soccer players) and Sports Ball

## Notes

- The program uses YOLOv8n (nano) model for faster processing
- Detection confidence threshold is set to 0.5
- Works with common video formats (MP4, AVI, MOV, MKV)
- Red highlight overlay indicates the highlighted player
- Web interface provides a user-friendly alternative to command-line usage
- Ready for production deployment with proper error handling and security measures