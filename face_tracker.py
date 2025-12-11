#!/usr/bin/env python3
"""
Face Tracking with Motor Control for Raspberry Pi
Tracks faces and controls a DC motor to follow horizontal movement.
"""

import cv2
import sys
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread, Lock
import time

# Motor control
try:
    from adafruit_motorkit import MotorKit
    kit = MotorKit()
    motor1 = kit.motor1  # M1 - horizontal (left/right)
    motor2 = kit.motor2  # M2 - vertical (up/down)
    MOTOR_AVAILABLE = True
    print("Motors initialized on M1 and M2")
except Exception as e:
    print(f"Motors not available: {e}")
    MOTOR_AVAILABLE = False
    motor1 = None
    motor2 = None

# Global variables
current_frame = None
frame_lock = Lock()

# Configuration
HOST = '0.0.0.0'
PORT = 8080
CAMERA_INDEX = 0

# Motor control settings
DEAD_ZONE = 50  # Pixels from center where motor won't move (face is "centered")
MOTOR_SPEED = 0.7  # Motor speed (0.0 to 1.0)


def get_local_ip():
    """Get the local IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"


def control_motors(offset_x, offset_y):
    """Control motors based on face offset from center."""
    if not MOTOR_AVAILABLE:
        return
    
    # Horizontal control (M1)
    if motor1 is not None:
        if offset_x > DEAD_ZONE:
            # Face is to the right, turn motor left to follow
            motor1.throttle = -MOTOR_SPEED
        elif offset_x < -DEAD_ZONE:
            # Face is to the left, turn motor right to follow
            motor1.throttle = MOTOR_SPEED
        else:
            motor1.throttle = 0
    
    # Vertical control (M2)
    if motor2 is not None:
        if offset_y > DEAD_ZONE:
            # Face is too low, turn motor to follow
            motor2.throttle = MOTOR_SPEED
        elif offset_y < -DEAD_ZONE:
            # Face is too high, turn motor to follow
            motor2.throttle = -MOTOR_SPEED
        else:
            motor2.throttle = 0


def stop_motors():
    """Stop both motors."""
    if MOTOR_AVAILABLE:
        if motor1 is not None:
            motor1.throttle = 0
        if motor2 is not None:
            motor2.throttle = 0


class StreamHandler(BaseHTTPRequestHandler):
    """HTTP handler for video streaming."""
    
    def log_message(self, format, *args):
        pass
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = '''<!DOCTYPE html>
<html>
<head>
    <title>Face Tracker</title>
    <style>
        * { margin: 0; padding: 0; }
        body {
            background: #000;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        img {
            max-width: 100vw;
            max-height: 100vh;
            object-fit: contain;
        }
    </style>
</head>
<body>
    <img src="/stream" alt="Stream">
</body>
</html>'''
            self.wfile.write(html.encode())
            
        elif self.path == '/stream':
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()
            
            try:
                while True:
                    with frame_lock:
                        if current_frame is not None:
                            frame_data = current_frame.copy()
                        else:
                            continue
                    
                    _, jpeg = cv2.imencode('.jpg', frame_data, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    self.wfile.write(b'--frame\r\n')
                    self.wfile.write(b'Content-Type: image/jpeg\r\n\r\n')
                    self.wfile.write(jpeg.tobytes())
                    self.wfile.write(b'\r\n')
                    time.sleep(0.033)
            except (BrokenPipeError, ConnectionResetError):
                pass
        else:
            self.send_response(404)
            self.end_headers()


def start_server():
    """Start the HTTP server."""
    server = HTTPServer((HOST, PORT), StreamHandler)
    server.serve_forever()


def process_frames():
    """Main loop for capturing and processing frames."""
    global current_frame
    
    # Load face cascade
    try:
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    except AttributeError:
        cascade_path = '/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml'
    
    face_cascade = cv2.CascadeClassifier(cascade_path)
    
    if face_cascade.empty():
        print("Error: Could not load face cascade classifier")
        sys.exit(1)
    
    # Open camera
    cap = cv2.VideoCapture(CAMERA_INDEX)
    
    if not cap.isOpened():
        print(f"Error: Could not open camera at index {CAMERA_INDEX}")
        sys.exit(1)
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    print("Camera ready")
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            time.sleep(0.1)
            continue
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
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
            
            # Draw simple rectangle around face
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), 2)
            
            # Calculate offset from center
            face_center_x = x + w // 2
            face_center_y = y + h // 2
            offset_x = face_center_x - frame_center_x
            offset_y = face_center_y - frame_center_y
            
            # Control motors
            control_motors(offset_x, offset_y)
        else:
            # No face detected, stop motors
            stop_motors()
        
        # Update frame for streaming
        with frame_lock:
            current_frame = frame.copy()
        
        time.sleep(0.01)
    
    cap.release()
    stop_motors()


def main():
    local_ip = get_local_ip()
    
    print("=" * 40)
    print("  FACE TRACKER")
    print("=" * 40)
    print(f"\n  http://{local_ip}:{PORT}")
    print("\n  Ctrl+C to stop")
    print("=" * 40 + "\n")
    
    # Start server
    server_thread = Thread(target=start_server, daemon=True)
    server_thread.start()
    
    try:
        process_frames()
    except KeyboardInterrupt:
        print("\nStopping...")
        stop_motors()


if __name__ == "__main__":
    main()
