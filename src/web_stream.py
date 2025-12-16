"""
Web streaming module.
HTTP server for MJPEG video streaming.
"""

import cv2
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

from .shared_state import shared

# Configuration
HOST = '0.0.0.0'
PORT = 8080


class StreamHandler(BaseHTTPRequestHandler):
    """HTTP handler for video streaming."""
    
    def log_message(self, format, *args):
        pass  # Suppress HTTP logs
    
    def do_GET(self):
        if self.path == '/':
            self._serve_index()
        elif self.path == '/stream':
            self._serve_stream()
        else:
            self.send_response(404)
            self.end_headers()
    
    def _serve_index(self):
        """Serve the HTML index page."""
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
    
    def _serve_stream(self):
        """Serve the MJPEG video stream."""
        self.send_response(200)
        self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
        self.end_headers()
        
        try:
            while shared.running:
                frame = shared.get_frame()
                
                if frame is None:
                    time.sleep(0.033)
                    continue
                
                _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                self.wfile.write(b'--frame\r\n')
                self.wfile.write(b'Content-Type: image/jpeg\r\n\r\n')
                self.wfile.write(jpeg.tobytes())
                self.wfile.write(b'\r\n')
                time.sleep(0.033)
                
        except (BrokenPipeError, ConnectionResetError):
            pass


def run_web_server():
    """Start the HTTP streaming server."""
    server = HTTPServer((HOST, PORT), StreamHandler)
    print(f"Web server running on port {PORT}")
    
    while shared.running:
        server.handle_request()
    
    server.server_close()
    print("Web server stopped")
