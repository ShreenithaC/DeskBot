"""
Vision tracking module.
Handles camera capture, face detection, and motor control commands.
"""

import cv2
import sys
import time

from .shared_state import shared
from .motor_control import control_motors, stop_motors

# Configuration
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480


def load_face_cascade():
    """Load the Haar cascade classifier for face detection."""
    try:
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    except AttributeError:
        cascade_path = '/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml'
    
    face_cascade = cv2.CascadeClassifier(cascade_path)
    
    if face_cascade.empty():
        print("Error: Could not load face cascade classifier")
        sys.exit(1)
    
    return face_cascade


def run_vision_tracker():
    """Main vision tracking loop."""
    face_cascade = load_face_cascade()
    
    # Open camera
    cap = cv2.VideoCapture(CAMERA_INDEX)
    
    if not cap.isOpened():
        print(f"Error: Could not open camera at index {CAMERA_INDEX}")
        sys.exit(1)
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    
    print("Camera ready")
    
    try:
        while shared.running:
            ret, frame = cap.read()
            
            if not ret:
                time.sleep(0.1)
                continue
            
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            frame_height, frame_width = frame.shape[:2]
            frame_center_x = frame_width // 2
            frame_center_y = frame_height // 2
            
            # Track the largest face
            if len(faces) > 0:
                # Find largest face
                largest_face = max(faces, key=lambda f: f[2] * f[3])
                x, y, w, h = largest_face
                
                # Draw rectangle around face
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), 2)
                
                # Calculate offset from center
                face_center_x = x + w // 2
                face_center_y = y + h // 2
                offset_x = face_center_x - frame_center_x
                offset_y = face_center_y - frame_center_y
                
                # Control motors based on offset (if tracking enabled)
                if shared.tracking_enabled:
                    control_motors(offset_x, offset_y)
                else:
                    stop_motors()
            else:
                # No face detected, stop motors
                stop_motors()
            
            # Update shared frame for streaming
            shared.set_frame(frame)
            
            time.sleep(0.01)
            
    finally:
        print("Closing camera...")
        cap.release()
        stop_motors()
