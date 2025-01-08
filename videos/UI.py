import os

from torch.ao.nn.quantized.functional import threshold
# import shutil
# import subprocess
# import tempfile
# import tkinter as tk
# from tkinter import filedialog
from ultralytics import YOLO
import cv2

from ultralytics import YOLO
import cv2
import os

# Paths
VIDEOS_DIR = '/Users/connormcilhinney/Desktop/highlight_Project/videos'
video_path = os.path.join(VIDEOS_DIR, 'TestClip.mp4')
output_frames_dir = os.path.join(VIDEOS_DIR, 'output_frames')
os.makedirs(output_frames_dir, exist_ok=True)
output_video_path = os.path.join(VIDEOS_DIR, 'TestClip_out.mp4')
model_path = '/Users/connormcilhinney/Desktop/highlight_Project/videos/runs/detect/train3/weights/best.pt'

# Open video file
cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    raise IOError(f"Cannot open video file: {video_path}")

# Load YOLO model
model = YOLO(model_path)

# Get frame rate and dimensions
fps = int(cap.get(cv2.CAP_PROP_FPS))
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
frame_index = 0

# Prepare video writer (using H.264 codec)
out = cv2.VideoWriter(
    output_video_path,
    cv2.VideoWriter_fourcc(*'mp4v'),
    fps,
    (frame_width, frame_height)
)

# Process video frame by frame
while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Process frame with YOLO (add detections)
    results = model(frame)  # Run YOLO on the frame
    annotated_frame = results[0].plot()  # Annotate frame with detections

    # Save frame to output video
    out.write(annotated_frame)
    frame_index += 1

cap.release()
out.release()
print(f"Processed {frame_index} frames. Output saved to {output_video_path}")

# model = YOLO("yolov8n.yaml") # Load Model
# results = model.train(data="config.yaml", epochs=1) # Train Model

#
# # Global variable to store the selected file path and output video path
# selected_file = None
# output_video = None
#
# def place_mp4_file():
#     global selected_file
#     file_path = filedialog.askopenfilename(
#         title="Select an MP4 file",
#         filetypes=(("MP4 Files", "*.mp4"), ("All Files", "*.*"), ("Mov Files", "*.mov"))
#     )
#     if file_path:
#         file_label.config(text=f"Selected File: {file_path}")
#         selected_file = file_path  # Store the file path globally
#         add_overlay()  # Add overlay as soon as a file is selected
#     else:
#         file_label.config(text="No file selected")
#
#
# def add_overlay():
#     global output_video
#     try:
#         # Create a temporary file for the output video (do not save it in the same folder)
#         temp_dir = tempfile.mkdtemp()  # Temporary directory
#         output_video = os.path.join(temp_dir, 'EDITED.mp4')
#
#         # FFmpeg command to apply the overlay
#         cmd = [
#             'ffmpeg',
#             '-i', selected_file,
#             '-i', 'redCircle.png',
#             '-filter_complex',
#             '[1:v]scale=100:-1[overlay];[0:v][overlay]overlay=W-w-1000:H-h-10',
#             # Resize the overlay image to 100px width and apply it
#             '-codec:a', 'copy',  # Keep the audio as is
#             output_video  # Save output to the temporary file
#         ]
#
#         # Run the FFmpeg command
#         subprocess.run(cmd, check=True)
#         print(f"Overlay added successfully! Output saved temporarily as {output_video}")
#
#         # Ensure the output video file exists
#         if os.path.exists(output_video):
#             print(f"Output video file exists: {output_video}")
#         else:
#             print(f"Error: Output video not found at {output_video}")
#
#         # Enable the "Download" button after processing is done
#         download_button.config(state=tk.NORMAL)
#
#     except subprocess.CalledProcessError as e:
#         print(f"Error occurred: {e}")
#         status_label.config(text=f"Error occurred during overlay processing.")
#
#
# # Function to download (move) the processed video to the Desktop
# def download_file():
#     global output_video
#     if output_video and os.path.exists(output_video):
#         # Get the Downloads folder path (Desktop in this case)
#         desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
#
#         # Ensure that the directory exists
#         if not os.path.exists(desktop_path):
#             os.makedirs(desktop_path)
#
#         # Get the base file name of the output video
#         file_name = os.path.basename(output_video)
#
#         # Create the full destination path on the Desktop
#         destination = os.path.join(desktop_path, file_name)
#
#         try:
#             # Move the output video to the Desktop
#             shutil.move(output_video, destination)
#             # Update the status label with the location of the downloaded file
#             status_label.config(text=f"File successfully downloaded to: {destination}")
#             print(f"File moved to: {destination}")
#         except Exception as e:
#             status_label.config(text=f"Error: {e}")
#             print(f"Error moving file: {e}")
#     else:
#         status_label.config(text="No processed video to download.")
#
#
# # Create the main window
# print("ksdhffdkls")
# root = tk.Tk()
# root.title("MP4 File Selector and Downloader")
# root.geometry("700x300")
#
# # Add a button to select the MP4 file
# select_button = tk.Button(root, text="Place MP4 File", command=place_mp4_file)
# select_button.pack(pady=20)
#
# # Label to display the selected file path
# file_label = tk.Label(root, text="No file selected", wraplength=300)
# file_label.pack(pady=20)
#
# # Add a button to download the processed video (initially disabled)
# download_button = tk.Button(root, text="Download", command=download_file, state=tk.DISABLED)
# download_button.pack(pady=20)
#
# # Status label to show result or errors
# status_label = tk.Label(root, text="")
# status_label.pack(pady=20)
#
# # Start the main loop to run the GUI
# root.mainloop()
