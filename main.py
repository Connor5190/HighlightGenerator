import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image, ImageDraw
import os
import math
import time

class SoccerHighlightGenerator:
    def __init__(self):
        # Load YOLOv8 model
        self.model = YOLO('yolov8n.pt')  # Using nano version for speed
        
        # Class IDs for person and sports ball in COCO dataset
        self.PERSON_CLASS_ID = 0
        self.SPORTS_BALL_CLASS_ID = 32
        
        # Video properties
        self.video_path = None
        self.cap = None
        self.current_frame = None
        self.frame_count = 0
        self.fps = 30
        
        # Detection results
        self.players = []
        self.balls = []
        
        # Mouse interaction
        self.mouse_selection_mode = True  # Always in selection mode
        self.highlighted_player = None
        self.window_name = 'Soccer Highlight Generator'
        
        # Freeze frame functionality
        self.freeze_frame = None
        self.freeze_start_time = None
        self.freeze_duration = 3.0  # 3 second freeze
        self.is_frozen = False
        
        # Video recording
        self.video_writer = None
        self.output_path = None
        self.is_recording = False
        
        # Highlight overlay - no longer needed as fixed overlay
        pass
        
    def load_video(self, video_path):
        """Load video file for processing"""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
            
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        
        if not self.cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
            
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"Video loaded: {video_path}")
        print(f"FPS: {self.fps}, Total frames: {self.frame_count}")
        
    def detect_objects(self, frame):
        """Detect soccer players and balls in the current frame"""
        results = self.model(frame, verbose=False)
        
        self.players = []
        self.balls = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    
                    # Filter for high confidence detections
                    if confidence > 0.5:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        center_x = int((x1 + x2) / 2)
                        center_y = int((y1 + y2) / 2)
                        
                        if class_id == self.PERSON_CLASS_ID:
                            self.players.append({
                                'bbox': (int(x1), int(y1), int(x2), int(y2)),
                                'center': (center_x, center_y),
                                'confidence': confidence
                            })
                        elif class_id == self.SPORTS_BALL_CLASS_ID:
                            self.balls.append({
                                'bbox': (int(x1), int(y1), int(x2), int(y2)),
                                'center': (center_x, center_y),
                                'confidence': confidence
                            })
    
    def find_closest_player_to_ball(self):
        """Find the player closest to any detected ball"""
        if not self.players or not self.balls:
            return None
            
        min_distance = float('inf')
        closest_player = None
        
        for ball in self.balls:
            ball_center = ball['center']
            
            for player in self.players:
                player_center = player['center']
                
                # Calculate Euclidean distance
                distance = math.sqrt(
                    (ball_center[0] - player_center[0])**2 + 
                    (ball_center[1] - player_center[1])**2
                )
                
                if distance < min_distance:
                    min_distance = distance
                    closest_player = player
                    
        return closest_player
    
    def draw_detections(self, frame):
        """Draw bounding boxes for detected objects"""
        # Draw players in blue
        for player in self.players:
            x1, y1, x2, y2 = player['bbox']
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.putText(frame, f"Player {player['confidence']:.2f}", 
                       (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
        # Draw balls in green
        for ball in self.balls:
            x1, y1, x2, y2 = ball['bbox']
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"Ball {ball['confidence']:.2f}", 
                       (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return frame
    
    def add_highlight_overlay(self, frame, player):
        """Add dynamic red highlight overlay matching the player's dimensions"""
        if player is None:
            return frame
            
        x1, y1, x2, y2 = player['bbox']
        
        # Calculate dimensions
        width = x2 - x1
        height = y2 - y1
        
        # Add padding around the player (20% of dimensions for more visibility)
        padding_x = int(width * 0.2)
        padding_y = int(height * 0.2)
        
        # Expand bounding box with padding
        highlight_x1 = max(0, x1 - padding_x)
        highlight_y1 = max(0, y1 - padding_y)
        highlight_x2 = min(frame.shape[1], x2 + padding_x)
        highlight_y2 = min(frame.shape[0], y2 + padding_y)
        
        # Create overlay with player's dimensions
        overlay_width = highlight_x2 - highlight_x1
        overlay_height = highlight_y2 - highlight_y1
        
        if overlay_width <= 0 or overlay_height <= 0:
            return frame
        
        # Create dynamic overlay matching player dimensions
        overlay = Image.new('RGBA', (overlay_width, overlay_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Draw red rectangle with rounded corners and transparency
        border_width = max(3, min(width, height) // 30)  # Thinner border for subtlety
        
        # Draw filled rectangle with less opacity for more transparency
        draw.rectangle([0, 0, overlay_width-1, overlay_height-1], 
                      fill=(255, 0, 0, 80))  # More transparent red fill
        
        # Draw border with thinner lines for subtlety
        for i in range(border_width):
            draw.rectangle([i, i, overlay_width-1-i, overlay_height-1-i], 
                          outline=(255, 0, 0, 255), fill=None)
        
        # Convert to numpy array
        overlay_np = np.array(overlay)
        
        # Extract the region to overlay from the original BGR frame
        region = frame[highlight_y1:highlight_y2, highlight_x1:highlight_x2]
        
        # Ensure we have matching dimensions
        if region.shape[:2] != overlay_np.shape[:2]:
            return frame
        
        # Convert region to RGBA for blending
        region_rgba = cv2.cvtColor(region, cv2.COLOR_BGR2RGBA)
        
        # Blend the overlay with the frame region
        alpha = overlay_np[:, :, 3:4] / 255.0
        blended = region_rgba[:, :, :3] * (1 - alpha) + overlay_np[:, :, :3] * alpha
        
        # Convert back to BGR and put it back in the frame
        blended_bgr = cv2.cvtColor(blended.astype(np.uint8), cv2.COLOR_RGB2BGR)
        frame[highlight_y1:highlight_y2, highlight_x1:highlight_x2] = blended_bgr
        
        return frame
    
    def find_player_at_position(self, x, y):
        """Find which player (if any) was clicked at the given position"""
        for player in self.players:
            x1, y1, x2, y2 = player['bbox']
            if x1 <= x <= x2 and y1 <= y <= y2:
                return player
        return None
    
    def setup_video_writer(self):
        """Set up video writer for saving the edited video"""
        if not os.path.exists('output'):
            os.makedirs('output')
            
        # Generate output filename
        input_name = os.path.splitext(os.path.basename(self.video_path))[0]
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.output_path = f"output/{input_name}_highlighted_{timestamp}.mp4"
        
        # Get video properties
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Set up video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(self.output_path, fourcc, self.fps, (width, height))
        self.is_recording = True
        
        print(f"Recording to: {self.output_path}")
    
    def write_frame_to_video(self, frame):
        """Write a frame to the output video"""
        if self.is_recording and self.video_writer is not None:
            self.video_writer.write(frame)
    
    def finalize_video(self):
        """Finalize and save the video"""
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None
            self.is_recording = False
            print(f"Video saved to: {self.output_path}")

    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse clicks for player selection"""
        if event == cv2.EVENT_LBUTTONDOWN and not self.is_frozen:
            clicked_player = self.find_player_at_position(x, y)
            if clicked_player:
                # Start freeze frame sequence
                self.highlighted_player = clicked_player
                self.freeze_frame = self.current_frame.copy()
                self.freeze_start_time = time.time()
                self.is_frozen = True
                print(f"Selected player at ({x}, {y}) - confidence: {clicked_player['confidence']:.2f}")
                print("Freeze frame activated for 3 seconds...")
            else:
                print(f"No player found at position ({x}, {y})")
    
    def play_video_interactive(self):
        """Play video with interactive mouse player selection"""
        if self.cap is None:
            print("No video loaded. Please load a video first.")
            return
            
        print("\n=== Interactive Video Player ===")
        print("Controls:")
        print("- MOUSE CLICK: Click on any player to highlight them")
        print("- 'q': Quit and save video")
        print("- 'r': Reset/remove highlights")
        print("- 'p': Pause/Resume")
        print("================================\n")
        
        # Set up video recording
        self.setup_video_writer()
        
        # Set up mouse callback
        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)
        
        paused = False
        freeze_frames_written = 0
        
        while True:
            display_frame = None
            output_frame = None  # Frame to write to video (without UI elements)
            
            # Handle freeze frame logic
            if self.is_frozen:
                # Check if freeze duration has elapsed
                if time.time() - self.freeze_start_time >= self.freeze_duration:
                    # End freeze frame
                    self.is_frozen = False
                    self.highlighted_player = None
                    self.freeze_frame = None
                    freeze_frames_written = 0
                    print("Freeze frame ended, resuming video...")
                else:
                    # Show frozen frame with highlight
                    display_frame = self.draw_detections(self.freeze_frame.copy())
                    output_frame = self.freeze_frame.copy()  # Clean frame for output
                    
                    if self.highlighted_player is not None:
                        display_frame = self.add_highlight_overlay(display_frame, self.highlighted_player)
                        output_frame = self.add_highlight_overlay(output_frame, self.highlighted_player)
                    
                    # Add freeze frame indicator (only for display, not output)
                    cv2.putText(display_frame, "FREEZE FRAME", 
                               (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
                    
                    # Write multiple copies of freeze frame to maintain 1-second duration
                    freeze_frames_needed = int(self.fps * self.freeze_duration)
                    if freeze_frames_written < freeze_frames_needed:
                        self.write_frame_to_video(output_frame)
                        freeze_frames_written += 1
            else:
                # Normal video playback
                if not paused:
                    ret, frame = self.cap.read()
                    if not ret:
                        print("End of video reached.")
                        break
                        
                    self.current_frame = frame.copy()
                    
                    # Detect objects in current frame
                    self.detect_objects(frame)
                    
                    # Draw detection boxes for display
                    display_frame = self.draw_detections(frame.copy())
                    
                    # Clean frame for output (no detection boxes)
                    output_frame = frame.copy()
                    
                    # Write frame to output video
                    self.write_frame_to_video(output_frame)
            
            # Add frame info (if we have a display frame)
            if display_frame is not None:
                info_text = f"Players: {len(self.players)}, Balls: {len(self.balls)}"
                if self.mouse_selection_mode:
                    info_text += " | CLICK ON A PLAYER TO HIGHLIGHT"
                if self.is_recording:
                    info_text += " | RECORDING"
                cv2.putText(display_frame, info_text, 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                cv2.imshow(self.window_name, display_frame)
            
            # Handle key presses with appropriate wait time
            if self.is_frozen:
                # During freeze, check more frequently for smoother timing
                key = cv2.waitKey(50) & 0xFF
            else:
                # Normal video timing
                key = cv2.waitKey(int(1000/self.fps)) & 0xFF
            
            if key == ord('q'):
                break

            elif key == ord('r'):  # Reset highlights
                self.highlighted_player = None
                self.mouse_selection_mode = False
                self.is_frozen = False
                self.freeze_frame = None
                print("Highlights and freeze frame reset")
            elif key == ord('p'):  # Pause/Resume
                if not self.is_frozen:
                    paused = not paused
                    print("Paused" if paused else "Resumed")
                else:
                    print("Cannot pause during freeze frame.")
        
        # Finalize and save the video
        self.finalize_video()
        
        self.cap.release()
        cv2.destroyAllWindows()
    
    def process_single_image(self, image_path):
        """Process a single image for testing detection"""
        if not os.path.exists(image_path):
            print(f"Image file not found: {image_path}")
            return
            
        frame = cv2.imread(image_path)
        if frame is None:
            print(f"Could not load image: {image_path}")
            return
            
        print(f"Processing image: {image_path}")
        
        # Detect objects
        self.detect_objects(frame)
        
        # Draw detections
        result_frame = self.draw_detections(frame.copy())
        
        # Find and highlight closest player to ball
        closest_player = self.find_closest_player_to_ball()
        if closest_player:
            result_frame = self.add_highlight_overlay(result_frame, closest_player)
            print(f"Found {len(self.players)} players and {len(self.balls)} balls")
            print("Highlighted player closest to ball")
        else:
            print(f"Found {len(self.players)} players and {len(self.balls)} balls")
            print("No player-ball pair to highlight")
        
        # Display result
        cv2.imshow('Detection Result', result_frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def process_single_image_web(self, image_path):
        """Process a single image for web API"""
        if not os.path.exists(image_path):
            return {'error': f'Image file not found: {image_path}'}
            
        frame = cv2.imread(image_path)
        if frame is None:
            return {'error': f'Could not load image: {image_path}'}
        
        # Detect objects
        self.detect_objects(frame)
        
        # Find closest player to ball
        closest_player = self.find_closest_player_to_ball()
        
        # Prepare result
        result = {
            'players_detected': len(self.players),
            'balls_detected': len(self.balls),
            'players': [],
            'balls': [],
            'highlighted_player': None
        }
        
        # Add player details
        for i, player in enumerate(self.players):
            result['players'].append({
                'id': i,
                'bbox': player['bbox'],
                'center': player['center'],
                'confidence': player['confidence']
            })
        
        # Add ball details
        for i, ball in enumerate(self.balls):
            result['balls'].append({
                'id': i,
                'bbox': ball['bbox'],
                'center': ball['center'],
                'confidence': ball['confidence']
            })
        
        # Add highlighted player info
        if closest_player:
            result['highlighted_player'] = {
                'bbox': closest_player['bbox'],
                'center': closest_player['center'],
                'confidence': closest_player['confidence']
            }
        
        return result

def main():
    generator = SoccerHighlightGenerator()
    
    print("=== Soccer Highlight Generator ===")
    print("This program detects soccer players and balls using YOLOv8")
    print("Click on any player during video playback to highlight them with a 3-second freeze frame")
    print("===================================\n")
    
    while True:
        print("\nOptions:")
        print("1. Process video file")
        print("2. Test with single image")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            video_path = input("Enter video file path: ").strip()
            try:
                generator.load_video(video_path)
                generator.play_video_interactive()
            except Exception as e:
                print(f"Error processing video: {e}")
                
        elif choice == '2':
            image_path = input("Enter image file path: ").strip()
            generator.process_single_image(image_path)
            
        elif choice == '3':
            print("Goodbye!")
            break
            
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()