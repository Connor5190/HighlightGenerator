import os
import tempfile
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_file, abort
from werkzeug.utils import secure_filename
import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image, ImageDraw
import math
import time
import threading
import queue
import json
import base64

# Import the existing SoccerHighlightGenerator class
from main import SoccerHighlightGenerator

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size for free tier
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
app.config['OUTPUT_FOLDER'] = '/tmp/output'
app.config['FRAMES_FOLDER'] = '/tmp/frames'
app.config['STATUS_FOLDER'] = '/tmp/status'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
os.makedirs(app.config['FRAMES_FOLDER'], exist_ok=True)
os.makedirs(app.config['STATUS_FOLDER'], exist_ok=True)

# Global variables for processing
processing_queue = queue.Queue()

# Fallback to in-memory storage if file storage fails
processing_results = {}
video_analysis_results = {}

# Allowed file extensions
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def store_task_status(task_id, status_data):
    """Store task status in Redis or fallback to memory"""
    try:
        status_path = os.path.join(app.config['STATUS_FOLDER'], f"{task_id}.json")
        with open(status_path, 'w') as f:
            json.dump(status_data, f)
    except Exception as e:
        print(f"File store failed: {e}")
        processing_results[task_id] = status_data

def get_task_status(task_id):
    """Get task status from Redis or fallback to memory"""
    try:
        status_path = os.path.join(app.config['STATUS_FOLDER'], f"{task_id}.json")
        if os.path.exists(status_path):
            with open(status_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"File get failed: {e}")
    
    return processing_results.get(task_id)

def store_analysis_status(task_id, status_data):
    """Store analysis status in Redis or fallback to memory"""
    try:
        status_path = os.path.join(app.config['STATUS_FOLDER'], f"analysis_{task_id}.json")
        with open(status_path, 'w') as f:
            json.dump(status_data, f)
    except Exception as e:
        print(f"File store failed: {e}")
        video_analysis_results[task_id] = status_data

def get_analysis_status(task_id):
    """Get analysis status from Redis or fallback to memory"""
    try:
        status_path = os.path.join(app.config['STATUS_FOLDER'], f"analysis_{task_id}.json")
        if os.path.exists(status_path):
            with open(status_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"File get failed: {e}")
    
    return video_analysis_results.get(task_id)

def analyze_video_async(video_path, task_id):
    """Analyze video and extract frames with detected players"""
    try:
        generator = SoccerHighlightGenerator()
        generator.load_video(video_path)
        
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Limit processing for free tier (max 30 seconds of video)
        max_frames = min(total_frames, int(fps * 30))
        
        frames_data = []
        frame_count = 0
        
        # Update progress
        store_analysis_status(task_id, {
            'status': 'analyzing',
            'progress': 0,
            'message': 'Starting video analysis...',
            'frames': []
        })
        
        while frame_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Detect objects
            generator.detect_objects(frame)
            
            # If players are detected, save frame info
            if generator.players:
                # Save frame as image
                frame_filename = f"frame_{frame_count:06d}.jpg"
                frame_path = os.path.join(app.config['FRAMES_FOLDER'], frame_filename)
                cv2.imwrite(frame_path, frame)
                
                # Create frame data
                frame_data = {
                    'frame_number': frame_count,
                    'timestamp': frame_count / fps,
                    'frame_path': frame_filename,
                    'players': []
                }
                
                # Add player data
                for i, player in enumerate(generator.players):
                    # Ensure bbox coordinates are integers
                    bbox = player['bbox']
                    if isinstance(bbox, tuple):
                        bbox = [int(coord) for coord in bbox]
                    else:
                        bbox = [int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])]
                    
                    # Debug: Print first few player detections
                    if frame_count < 5 and i < 2:
                        print(f"Frame {frame_count}, Player {i}: bbox={bbox}, center={player['center']}")
                    
                    frame_data['players'].append({
                        'id': i,
                        'bbox': bbox,
                        'center': player['center'],
                        'confidence': player['confidence']
                    })
                
                frames_data.append(frame_data)
            
            frame_count += 1
            
            # Update progress every 10 frames
            if frame_count % 10 == 0:
                progress = (frame_count / max_frames) * 100
                store_analysis_status(task_id, {
                    'status': 'analyzing',
                    'progress': progress,
                    'message': f'Analyzing frame {frame_count}/{max_frames}',
                    'frames': frames_data
                })
        
        cap.release()
        
        # Final result
        store_analysis_status(task_id, {
            'status': 'completed',
            'progress': 100,
            'message': f'Analysis completed. Found {len(frames_data)} frames with players.',
            'frames': frames_data,
            'video_path': video_path,
            'fps': fps,
            'total_frames': max_frames
        })
        
    except Exception as e:
        store_analysis_status(task_id, {
            'status': 'error',
            'progress': 0,
            'message': f'Error analyzing video: {str(e)}',
            'frames': []
        })

def process_video_with_selections_async(video_path, selections, task_id):
    """Process video with user-selected highlights"""
    try:
        generator = SoccerHighlightGenerator()
        generator.load_video(video_path)
        
        # Set up output path
        input_name = os.path.splitext(os.path.basename(video_path))[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{input_name}_highlighted_{timestamp}.mp4")
        print(f"Output path: {output_path}")
        
        # Get video properties
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Limit processing for free tier
        max_frames = min(total_frames, int(fps * 30))
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = 0
        while frame_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Check if this frame has a selection
            frame_selection = None
            for selection in selections:
                if selection['frame_number'] == frame_count:
                    frame_selection = selection
                    print(f"Frame {frame_count}: Found selection: {frame_selection}")
                    break
            
            if frame_selection:
                # Detect objects in this frame
                generator.detect_objects(frame)
                
                # Find the selected player
                selected_player = None
                print(f"Frame {frame_count}: Looking for player with center: {frame_selection['player_center']}")
                print(f"Frame {frame_count}: Available players: {[(i, str(p['center'])) for i, p in enumerate(generator.players)]}")
                
                # Convert player_center to tuple for comparison
                target_center = tuple(frame_selection['player_center'])
                print(f"Frame {frame_count}: Target center (tuple): {target_center}")
                
                # Try exact match first
                for i, player in enumerate(generator.players):
                    print(f"Frame {frame_count}: Player {i}: center={player['center']}, type={type(player['center'])}, match={player['center'] == target_center}")
                    if player['center'] == target_center:
                        selected_player = player
                        print(f"Frame {frame_count}: Found selected player: {selected_player}")
                        break
                
                # If no exact match, try finding the closest player within a reasonable distance
                if selected_player is None:
                    print(f"Frame {frame_count}: No exact match found, trying closest player...")
                    min_distance = float('inf')
                    closest_player = None
                    
                    for i, player in enumerate(generator.players):
                        distance = ((player['center'][0] - target_center[0])**2 + 
                                  (player['center'][1] - target_center[1])**2)**0.5
                        print(f"Frame {frame_count}: Player {i}: distance={distance:.1f}")
                        
                        if distance < min_distance and distance < 50:  # Within 50 pixels
                            min_distance = distance
                            closest_player = player
                    
                    if closest_player:
                        selected_player = closest_player
                        print(f"Frame {frame_count}: Using closest player: {selected_player}")
                    else:
                        print(f"Frame {frame_count}: No player found within reasonable distance")
                
                # Add highlight and freeze frame if player found
                if selected_player:
                    print(f"Adding highlight to frame {frame_count}")
                    # Create freeze frame effect (3 seconds at 30fps = 90 frames)
                    freeze_duration_frames = int(fps * 3)  # 3 second freeze
                    
                    # Add highlight overlay to the frame
                    highlighted_frame = generator.add_highlight_overlay(frame.copy(), selected_player)
                    print(f"Highlighted frame shape: {highlighted_frame.shape}")
                    
                    # Write the highlighted frame multiple times to create freeze effect
                    for i in range(freeze_duration_frames):
                        success = out.write(highlighted_frame)
                        if i == 0:  # Only print for first frame
                            print(f"First freeze frame write success: {success}")
                    
                    # Don't skip ahead in the input video - we want to continue processing normally
                    # The freeze frames are added to the output, making the video longer
                else:
                    print(f"No player found for frame {frame_count}")
                    # If player not found, just write the original frame
                    out.write(frame)
            else:
                # No selection for this frame, write original
                out.write(frame)
            
            frame_count += 1
            
            # Update progress (account for freeze frames making output longer)
            # Calculate total output frames including freeze frames
            total_freeze_frames = 0
            for selection in selections:
                if selection['frame_number'] <= frame_count:
                    total_freeze_frames += int(fps * 3) - 1  # -1 because we replace the original frame
            
            effective_frame_count = frame_count + total_freeze_frames
            progress = min(100, (effective_frame_count / (max_frames + len(selections) * int(fps * 3))) * 100)
            store_task_status(task_id, {
                'status': 'processing',
                'progress': progress,
                'message': f'Processing frame {frame_count}/{max_frames} (output: {effective_frame_count} frames)'
            })
        
        cap.release()
        out.release()
        
        # Check if output file was created
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"Output file created: {output_path}, size: {file_size} bytes")
        else:
            print(f"Output file not found: {output_path}")
        
        # Update final result
        store_task_status(task_id, {
            'status': 'completed',
            'progress': 100,
            'output_path': output_path,
            'message': f'Video processing completed successfully with {len(selections)} highlights and freeze frames'
        })
        
    except Exception as e:
        store_task_status(task_id, {
            'status': 'error',
            'progress': 0,
            'message': f'Error processing video: {str(e)}'
        })

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

@app.route('/upload', methods=['POST'])
def upload_file():
    """Legacy upload endpoint for backward compatibility"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Start processing in background
        if file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            thread = threading.Thread(target=process_video_async, args=(file_path, task_id))
            thread.daemon = True
            thread.start()
            
            return jsonify({
                'task_id': task_id,
                'message': 'Video uploaded and processing started',
                'filename': unique_filename
            })
        else:
            # For images, process immediately
            generator = SoccerHighlightGenerator()
            result = generator.process_single_image_web(file_path)
            return jsonify({
                'task_id': task_id,
                'status': 'completed',
                'result': result,
                'filename': unique_filename
            })
            
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

def process_video_async(video_path, task_id):
    """Legacy video processing function for backward compatibility"""
    try:
        generator = SoccerHighlightGenerator()
        generator.load_video(video_path)
        
        # Set up output path
        input_name = os.path.splitext(os.path.basename(video_path))[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{input_name}_highlighted_{timestamp}.mp4")
        
        # Get video properties
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Limit processing for free tier
        max_frames = min(total_frames, int(fps * 30))
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = 0
        while frame_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Detect objects
            generator.detect_objects(frame)
            
            # Find closest player to ball
            closest_player = generator.find_closest_player_to_ball()
            
            # Add highlight if player found
            if closest_player:
                frame = generator.add_highlight_overlay(frame, closest_player)
            
            out.write(frame)
            frame_count += 1
            
            # Update progress
            progress = (frame_count / max_frames) * 100
            processing_results[task_id] = {
                'status': 'processing',
                'progress': progress,
                'message': f'Processing frame {frame_count}/{max_frames}'
            }
        
        cap.release()
        out.release()
        
        # Clean up input file to save space
        try:
            os.remove(video_path)
        except:
            pass
        
        # Update final result
        processing_results[task_id] = {
            'status': 'completed',
            'progress': 100,
            'output_path': output_path,
            'message': f'Video processing completed successfully (processed {frame_count} frames)'
        }
        
    except Exception as e:
        processing_results[task_id] = {
            'status': 'error',
            'progress': 0,
            'message': f'Error processing video: {str(e)}'
        }

@app.route('/status/<task_id>')
def get_status(task_id):
    result = get_task_status(task_id)
    if result is None:
        return jsonify({'error': 'Task not found'}), 404
    
    return jsonify(result)

@app.route('/download/<task_id>')
def download_result(task_id):
    result = get_task_status(task_id)
    if result is None:
        return jsonify({'error': 'Task not found'}), 404
    if result['status'] != 'completed':
        return jsonify({'error': 'Processing not completed'}), 400
    
    output_path = result.get('output_path')
    if not output_path or not os.path.exists(output_path):
        return jsonify({'error': 'Output file not found'}), 404
    
    return send_file(output_path, as_attachment=True)

@app.route('/api/detect', methods=['POST'])
def detect_objects():
    """API endpoint for object detection on images"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        return jsonify({'error': 'Only image files are supported for detection'}), 400
    
    try:
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Process image
        generator = SoccerHighlightGenerator()
        result = generator.process_single_image_web(file_path)
        
        # Clean up uploaded file
        try:
            os.remove(file_path)
        except:
            pass  # Ignore cleanup errors
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Detection failed: {str(e)}'}), 500

@app.route('/analyze', methods=['POST'])
def analyze_video():
    """Analyze video and extract frames with players"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Start analysis in background
        thread = threading.Thread(target=analyze_video_async, args=(file_path, task_id))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'task_id': task_id,
            'message': 'Video analysis started',
            'filename': unique_filename
        })
        
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/analysis-status/<task_id>')
def get_analysis_status_route(task_id):
    """Get video analysis status"""
    result = get_analysis_status(task_id)
    if result is None:
        return jsonify({'error': 'Task not found'}), 404
    
    return jsonify(result)

@app.route('/frame/<filename>')
def get_frame(filename):
    """Serve frame images"""
    frame_path = os.path.join(app.config['FRAMES_FOLDER'], filename)
    if not os.path.exists(frame_path):
        return jsonify({'error': 'Frame not found'}), 404
    
    return send_file(frame_path, mimetype='image/jpeg')

@app.route('/debug/frame-data/<task_id>')
def debug_frame_data(task_id):
    """Debug endpoint to see frame data structure"""
    result = get_analysis_status(task_id)
    if result is None:
        return jsonify({'error': 'Task not found'}), 404
    if result['status'] != 'completed':
        return jsonify({'error': 'Analysis not completed'}), 400
    
    # Return first few frames with player data
    debug_frames = result['frames'][:3] if len(result['frames']) >= 3 else result['frames']
    
    # Add detailed debugging info
    debug_info = []
    for frame in debug_frames:
        frame_debug = {
            'frame_number': frame['frame_number'],
            'timestamp': frame['timestamp'],
            'players_count': len(frame['players']),
            'players': []
        }
        for player in frame['players']:
            frame_debug['players'].append({
                'id': player['id'],
                'bbox': player['bbox'],
                'bbox_type': str(type(player['bbox'])),
                'bbox_length': len(player['bbox']) if player['bbox'] else None,
                'center': player['center'],
                'confidence': player['confidence']
            })
        debug_info.append(frame_debug)
    
    return jsonify({
        'total_frames': len(result['frames']),
        'sample_frames': debug_info
    })

@app.route('/process-selections', methods=['POST'])
def process_selections():
    """Process video with user selections"""
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        selections = data.get('selections', [])
        
        print(f"Received process-selections request:")
        print(f"  Task ID: {task_id}")
        print(f"  Selections: {selections}")
        
        analysis_result = get_analysis_status(task_id)
        if analysis_result is None:
            return jsonify({'error': 'Analysis task not found'}), 404
        if analysis_result['status'] != 'completed':
            return jsonify({'error': 'Video analysis not completed'}), 400
        
        video_path = analysis_result['video_path']
        print(f"  Video path: {video_path}")
        
        # Generate new task ID for processing
        process_task_id = str(uuid.uuid4())
        
        # Start processing in background
        thread = threading.Thread(target=process_video_with_selections_async, 
                                args=(video_path, selections, process_task_id))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'task_id': process_task_id,
            'message': 'Video processing started with selections'
        })
        
    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False) 