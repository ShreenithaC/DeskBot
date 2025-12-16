"""
Shared state for thread-safe communication between components.
"""

from threading import Lock
from queue import Queue


class SharedState:
    """Thread-safe shared state for frame and commands."""
    
    def __init__(self):
        self._frame = None
        self._frame_lock = Lock()
        self._command_queue = Queue()
        self._running = True
        self._tracking_enabled = True
    
    def set_frame(self, frame):
        """Update the current frame (thread-safe)."""
        with self._frame_lock:
            self._frame = frame.copy() if frame is not None else None
    
    def get_frame(self):
        """Get the current frame (thread-safe)."""
        with self._frame_lock:
            return self._frame.copy() if self._frame is not None else None
    
    def put_command(self, command):
        """Add a command to the queue."""
        self._command_queue.put(command)
    
    def get_command(self, timeout=None):
        """Get a command from the queue (blocking with optional timeout)."""
        try:
            return self._command_queue.get(timeout=timeout)
        except:
            return None
    
    def has_command(self):
        """Check if there are commands in the queue."""
        return not self._command_queue.empty()
    
    @property
    def running(self):
        return self._running
    
    @running.setter
    def running(self, value):
        self._running = value
    
    @property
    def tracking_enabled(self):
        return self._tracking_enabled
    
    @tracking_enabled.setter
    def tracking_enabled(self, value):
        self._tracking_enabled = value


# Global shared state instance
shared = SharedState()
