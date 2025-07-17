import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image, ImageDraw
import os
import math

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
        
        # Highlight overlay
        self.highlight_overlay = None
        self.create_highlight_overlay()
        
    def create_highlight_overlay(self):
        """Create a red circle PNG overlay for highlighting players"""
        size = 100
        overlay = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Draw red circle with transparency
        draw.ellipse([10, 10, size-10, size-10], 
                    outline=(255, 0, 0, 255), 
                    fill=(255, 0, 0, 80), 
                    width=5)
        
        self.highlight_overlay = np.array(overlay)
        
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
        """Add red circle overlay on the specified player"""
        if player is None:
            return frame
            
        center_x, center_y = player['center']
        overlay_size = self.highlight_overlay.shape[0]
        
        # Calculate overlay position
        start_x = max(0, center_x - overlay_size // 2)
        start_y = max(0, center_y - overlay_size // 2)
        end_x = min(frame.shape[1], start_x + overlay_size)
        end_y = min(frame.shape[0], start_y + overlay_size)
        
        # Adjust overlay size if it goes beyond frame boundaries
        overlay_end_x = overlay_size - max(0, (start_x + overlay_size) - frame.shape[1])
        overlay_end_y = overlay_size - max(0, (start_y + overlay_size) - frame.shape[0])
        
        # Convert frame to RGBA for blending
        frame_rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        
        # Extract the region to overlay
        region = frame_rgba[start_y:end_y, start_x:end_x]
        overlay_region = self.highlight_overlay[:overlay_end_y, :overlay_end_x]
        
        # Blend the overlay with the frame
        alpha = overlay_region[:, :, 3:4] / 255.0
        blended = region * (1 - alpha) + overlay_region[:, :, :3] * alpha
        
        # Put the blended region back
        frame_rgba[start_y:end_y, start_x:end_x] = blended.astype(np.uint8)
        
        # Convert back to BGR
        return cv2.cvtColor(frame_rgba, cv2.COLOR_RGBA2BGR)
    
    def play_video_interactive(self):
        """Play video with interactive spacebar highlighting"""
        if self.cap is None:
            print("No video loaded. Please load a video first.")
            return
            
        print("\n=== Interactive Video Player ===")
        print("Controls:")
        print("- SPACEBAR: Highlight player closest to ball")
        print("- 'q': Quit")
        print("- 'r': Reset/remove highlights")
        print("- 'p': Pause/Resume")
        print("================================\n")
        
        paused = False
        highlighted_player = None
        
        while True:
            if not paused:
                ret, frame = self.cap.read()
                if not ret:
                    print("End of video reached.")
                    break
                    
                self.current_frame = frame.copy()
                
                # Detect objects in current frame
                self.detect_objects(frame)
                
                # Draw detection boxes
                display_frame = self.draw_detections(frame.copy())
                
                # Add highlight if spacebar was pressed
                if highlighted_player is not None:
                    display_frame = self.add_highlight_overlay(display_frame, highlighted_player)
                
                # Add frame info
                cv2.putText(display_frame, f"Players: {len(self.players)}, Balls: {len(self.balls)}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                cv2.imshow('Soccer Highlight Generator', display_frame)
            
            # Handle key presses
            key = cv2.waitKey(int(1000/self.fps)) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord(' '):  # Spacebar
                closest_player = self.find_closest_player_to_ball()
                if closest_player:
                    highlighted_player = closest_player
                    print(f"Highlighted player closest to ball (distance calculated)")
                else:
                    print("No player-ball pair found to highlight")
            elif key == ord('r'):  # Reset highlights
                highlighted_player = None
                print("Highlights reset")
            elif key == ord('p'):  # Pause/Resume
                paused = not paused
                print("Paused" if paused else "Resumed")
        
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

def main():
    generator = SoccerHighlightGenerator()
    
    print("=== Soccer Highlight Generator ===")
    print("This program detects soccer players and balls using YOLOv8")
    print("Press spacebar during video playback to highlight the player closest to the ball")
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