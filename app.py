from flask import Flask, render_template, request, jsonify, send_file, url_for
import os
import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image, ImageDraw
import base64
import io
import json
import time
import threading
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
os.makedirs('static/temp', exist_ok=True)

class WebSoccerHighlightGenerator:
    def __init__(self):
        print("Loading YOLO model...")
        self.model = YOLO('yolov8n.pt')
        self.PERSON_CLASS_ID = 0
        self.SPORTS_BALL_CLASS_ID = 32
        print("YOLO model loaded successfully!")
        
    def detect_objects_in_frame(self, frame):
        """Detect objects and return structured data"""
        results = self.model(frame, verbose=False)
        
        players = []
        balls = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    
                    if confidence > 0.5:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        center_x = int((x1 + x2) / 2)
                        center_y = int((y1 + y2) / 2)
                        
                        detection_data = {
                            'bbox': [int(x1), int(y1), int(x2), int(y2)],
                            'center': [center_x, center_y],
                            'confidence': confidence
                        }
                        
                        if class_id == self.PERSON_CLASS_ID:
                            players.append(detection_data)
                        elif class_id == self.SPORTS_BALL_CLASS_ID:
                            balls.append(detection_data)
        
        return players, balls
    
    def process_image(self, image_path):
        """Process single image and return detection data"""
        frame = cv2.imread(image_path)
        if frame is None:
            return None, None, None
            
        players, balls = self.detect_objects_in_frame(frame)
        
        # Convert frame to base64 for web display
        _, buffer = cv2.imencode('.jpg', frame)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return players, balls, img_base64
    
    def extract_video_info(self, video_path):
        """Extract basic video info and first frame only for fast preview"""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return None
            
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Get first frame only for initial preview
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return None
        
        # Resize frame for web display
        if width > 800:
            scale = 800 / width
            new_width = 800
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height))
        
        # Process first frame only
        players, balls = self.detect_objects_in_frame(frame)
        
        # Convert to base64
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return {
            'total_frames': total_frames,
            'fps': fps,
            'duration': total_frames / fps,
            'width': width,
            'height': height,
            'first_frame': {
                'frame_number': 0,
                'timestamp': 0,
                'image': img_base64,
                'players': players,
                'balls': balls
            }
        }
    
    def get_video_frame(self, video_path, frame_number):
        """Get a specific frame from video with detection"""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return None
            
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return None
        
        # Resize frame for web display
        height, width = frame.shape[:2]
        if width > 800:
            scale = 800 / width
            new_width = 800
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height))
        
        # Detect objects
        players, balls = self.detect_objects_in_frame(frame)
        
        # Convert to base64
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        fps = cap.get(cv2.CAP_PROP_FPS) if cap.isOpened() else 30
        
        return {
            'frame_number': frame_number,
            'timestamp': frame_number / fps,
            'image': img_base64,
            'players': players,
            'balls': balls
        }
    
    def add_highlight_overlay(self, frame, player_bbox):
        """Add dynamic red highlight overlay matching the player's dimensions"""
        x1, y1, x2, y2 = player_bbox
        
        # Calculate dimensions
        width = x2 - x1
        height = y2 - y1
        
        # Add padding around the player (10% of dimensions)
        padding_x = int(width * 0.1)
        padding_y = int(height * 0.1)
        
        # Expand bounding box with padding
        highlight_x1 = max(0, x1 - padding_x)
        highlight_y1 = max(0, y1 - padding_y)
        highlight_x2 = min(frame.shape[1], x2 + padding_x)
        highlight_y2 = min(frame.shape[0], y2 + padding_y)
        
        # Create overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (highlight_x1, highlight_y1), (highlight_x2, highlight_y2), 
                     (0, 0, 255), -1)  # Red fill
        
        # Blend with original frame
        alpha = 0.3  # Transparency
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        
        # Add border
        cv2.rectangle(frame, (highlight_x1, highlight_y1), (highlight_x2, highlight_y2), 
                     (0, 0, 255), 3)  # Red border
        
        return frame
    
    def find_closest_player_to_reference(self, current_players, reference_player):
        """Find the player in current frame closest to the reference player"""
        if not current_players:
            return None
            
        ref_center = reference_player['center']
        min_distance = float('inf')
        closest_player = None
        
        for player in current_players:
            player_center = player['center']
            
            # Calculate Euclidean distance
            distance = ((ref_center[0] - player_center[0])**2 + 
                       (ref_center[1] - player_center[1])**2)**0.5
            
            if distance < min_distance:
                min_distance = distance
                closest_player = player
                
        # Only return if the distance is reasonable (player hasn't moved too far)
        if min_distance < 200:  # Adjust threshold as needed
            return closest_player
        return None
    
    def scale_bbox_to_full_resolution(self, bbox, original_width, original_height, display_width=800):
        """Scale bounding box from display resolution back to full video resolution"""
        x1, y1, x2, y2 = bbox
        
        # Calculate scale factor
        if original_width > display_width:
            scale_factor = original_width / display_width
            display_height = int(original_height * display_width / original_width)
        else:
            scale_factor = 1.0
        
        # Scale coordinates back to full resolution
        scaled_x1 = int(x1 * scale_factor)
        scaled_y1 = int(y1 * scale_factor)
        scaled_x2 = int(x2 * scale_factor)
        scaled_y2 = int(y2 * scale_factor)
        
        return [scaled_x1, scaled_y1, scaled_x2, scaled_y2]
    
    def create_highlight_video_freeze_only(self, video_path, selected_frame_number, selected_frame_data, output_path):
        """Create highlight video with red rectangles ONLY during freeze frame"""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return False
            
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Set up video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = 0
        freeze_duration_frames = int(fps * 1.5)  # 1.5 second freeze
        
        print(f"Processing {total_frames} frames...")
        print(f"Video resolution: {width}x{height}")
        print(f"Selected frame: {selected_frame_number}, Freeze duration: {freeze_duration_frames} frames")
        print(f"Red rectangles will ONLY appear during freeze frame")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Check if we're at the selected frame for freeze effect
            if frame_count == selected_frame_number:
                print(f"Adding freeze frame effect at frame {frame_count}")
                
                # Detect players in the current frame for accurate positioning
                players, balls = self.detect_objects_in_frame(frame)
                
                # Create highlighted freeze frame
                highlighted_frame = frame.copy()
                
                # Scale the selected player bounding boxes to full resolution
                for selected_player in selected_frame_data:
                    # Scale bbox from display resolution (800px) to full video resolution
                    scaled_bbox = self.scale_bbox_to_full_resolution(
                        selected_player['bbox'], width, height
                    )
                    
                    print(f"Original bbox: {selected_player['bbox']}")
                    print(f"Scaled bbox: {scaled_bbox}")
                    
                    # Find closest matching player in current detections
                    scaled_selected_player = {
                        'bbox': scaled_bbox,
                        'center': [
                            (scaled_bbox[0] + scaled_bbox[2]) // 2,
                            (scaled_bbox[1] + scaled_bbox[3]) // 2
                        ],
                        'confidence': selected_player.get('confidence', 0.8)
                    }
                    
                    closest_player = self.find_closest_player_to_reference(players, scaled_selected_player)
                    if closest_player:
                        # Use the detected player's position for accuracy
                        highlighted_frame = self.add_highlight_overlay(highlighted_frame, closest_player['bbox'])
                        print(f"Using detected player bbox: {closest_player['bbox']}")
                    else:
                        # Fallback to scaled original position
                        highlighted_frame = self.add_highlight_overlay(highlighted_frame, scaled_bbox)
                        print(f"Using scaled original bbox: {scaled_bbox}")
                
                # Write the freeze frame multiple times (3 seconds)
                for i in range(freeze_duration_frames):
                    out.write(highlighted_frame)
                    if i % 30 == 0:  # Print every second
                        print(f"Writing freeze frame {i+1}/{freeze_duration_frames}")
                
                # Skip ahead in the original video to maintain sync
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count + 1)
                frame_count += freeze_duration_frames
                
            else:
                # Normal frame processing - NO HIGHLIGHTING, just original video
                out.write(frame)
                frame_count += 1
            
            # Print progress
            if frame_count % 100 == 0:
                progress = (frame_count / total_frames) * 100
                print(f"Progress: {progress:.1f}% ({frame_count}/{total_frames} frames)")
        
        cap.release()
        out.release()
        
        print(f"Highlight video created successfully: {output_path}")
        print("Red rectangles appear ONLY during the 3-second freeze frame")
        return True

# Global generator instance
generator = WebSoccerHighlightGenerator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test')
def test():
    """Test endpoint to verify Flask is working"""
    return jsonify({
        'status': 'success',
        'message': 'Flask server is running!',
        'model_loaded': hasattr(generator, 'model')
    })

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        timestamp = str(int(time.time()))
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Determine file type
        file_ext = filename.lower().split('.')[-1]
        
        if file_ext in ['jpg', 'jpeg', 'png', 'bmp']:
            # Process image
            players, balls, img_base64 = generator.process_image(filepath)
            
            if players is None:
                return jsonify({'error': 'Could not process image'}), 400
            
            return jsonify({
                'type': 'image',
                'filename': filename,
                'image': img_base64,
                'players': players,
                'balls': balls
            })
            
        elif file_ext in ['mp4', 'avi', 'mov', 'mkv']:
            # Process video - get basic info and first frame only
            video_info = generator.extract_video_info(filepath)
            
            if video_info is None:
                return jsonify({'error': 'Could not process video'}), 400
            
            return jsonify({
                'type': 'video',
                'filename': filename,
                'video_info': video_info
            })
        
        else:
            return jsonify({'error': 'Unsupported file format'}), 400

@app.route('/get_frame/<filename>/<int:frame_number>')
def get_frame(filename, frame_number):
    """Get a specific frame from video with detection"""
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'Video file not found'}), 404
    
    frame_data = generator.get_video_frame(filepath, frame_number)
    
    if frame_data is None:
        return jsonify({'error': 'Could not get frame'}), 400
    
    return jsonify(frame_data)

@app.route('/highlight', methods=['POST'])
def create_highlight():
    data = request.json
    filename = data.get('filename')
    selected_players = data.get('selected_players', [])
    selected_frame_data = data.get('selected_frame_data', [])
    selected_frame_number = data.get('selected_frame_number', 0)
    
    if not filename or not selected_players:
        return jsonify({'error': 'Missing filename or selected players'}), 400
    
    # Get input file path
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(input_path):
        return jsonify({'error': 'Input file not found'}), 404
    
    # Generate output filename
    base_name = os.path.splitext(filename)[0]
    output_filename = f"highlight_{base_name}.mp4"
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
    
    try:
        # Create highlight video using the new tracking method
        print(f"Creating highlight video for {len(selected_players)} players...")
        print(f"Selected frame: {selected_frame_number}")
        
        # If we don't have frame data, we need to get it from the selected frame
        if not selected_frame_data:
            # Get the selected frame to extract player data
            frame_data = generator.get_video_frame(input_path, selected_frame_number)
            if frame_data and frame_data.get('players'):
                selected_frame_data = []
                for player_index in selected_players:
                    if player_index < len(frame_data['players']):
                        selected_frame_data.append(frame_data['players'][player_index])
        
        if not selected_frame_data:
            return jsonify({'error': 'Could not get player data for highlighting'}), 400
        
        success = generator.create_highlight_video_freeze_only(
            input_path, 
            selected_frame_number,
            selected_frame_data, 
            output_path
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Highlight created for {len(selected_players)} players with freeze frame at frame {selected_frame_number}',
                'output_file': output_filename,
                'download_url': f'/download/{output_filename}'
            })
        else:
            return jsonify({'error': 'Failed to create highlight video'}), 500
            
    except Exception as e:
        print(f"Error creating highlight: {e}")
        return jsonify({'error': f'Error creating highlight: {str(e)}'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_file(
            os.path.join(app.config['OUTPUT_FOLDER'], filename),
            as_attachment=True
        )
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)