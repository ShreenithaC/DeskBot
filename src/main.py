#!/usr/bin/env python3
"""
Face Tracking with Motor Control - Main Entry Point
Starts all components and handles clean shutdown.
"""

import sys
import signal
import socket
import time
import subprocess
from threading import Thread

from .shared_state import shared
from .motor_control import stop_motors
from .vision_tracker import run_vision_tracker
from .web_stream import run_web_server, PORT
from .voice_commands import start_voice_commands, list_audio_devices
from .music_player import start_music_player

# Global references for cleanup
voice_thread = None
music_player = None
music_cmd_queue = None


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


def shutdown(signum=None, frame=None):
    """Clean shutdown handler."""
    print("\nShutting down...")
    shared.running = False
    
    if voice_thread:
        voice_thread.stop()
    
    if music_player:
        music_player.shutdown()
    
    stop_motors()


def say_greeting():
    """Speak the greeting using espeak."""
    message = "hello papi ur so sexy and cute i hope you have a good day and by the way your roommate andrew is so ugly and gay."
    try:
        print(f">>> Speaking: {message}")
        subprocess.run(['espeak', '-v', 'en-us+f3', '-s', '150', '-p', '65', message])
    except Exception as e:
        print(f"TTS error: {e}")


def process_commands():
    """
    Process commands from the voice command queue.
    Routes commands to appropriate handlers.
    """
    global music_cmd_queue
    
    while shared.running:
        command = shared.get_command(timeout=0.1)
        
        if command:
            cmd_type = command.get('type')
            action = command.get('action')
            
            # Greeting command
            if cmd_type == 'greeting':
                Thread(target=say_greeting, daemon=True).start()
            
            # Tracking commands
            elif cmd_type == 'tracking':
                if action == 'off':
                    print(">>> Tracking disabled")
                    shared.tracking_enabled = False
                elif action == 'on':
                    print(">>> Tracking enabled")
                    shared.tracking_enabled = True
            
            # Music commands -> route to music player queue
            elif cmd_type == 'music':
                if music_cmd_queue:
                    music_cmd_queue.put({
                        'action': action,
                        'query': command.get('query')
                    })
            
            # Volume commands -> route to music player
            elif cmd_type == 'volume':
                if music_cmd_queue:
                    if action == 'up':
                        music_cmd_queue.put({'action': 'volume_up'})
                    elif action == 'down':
                        music_cmd_queue.put({'action': 'volume_down'})


def main(mic_device=None):
    """
    Main entry point.
    
    Args:
        mic_device: Optional microphone device index. Use list_audio_devices() to find it.
    """
    global voice_thread, music_player, music_cmd_queue
    
    # Setup signal handlers for clean shutdown
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    
    local_ip = get_local_ip()
    
    print("=" * 50)
    print("  FACE TRACKER WITH VOICE & MUSIC")
    print("=" * 50)
    print(f"\n  Stream: http://{local_ip}:{PORT}")
    print("\n  Voice commands:")
    print("    - 'hello' - get a greeting")
    print("    - 'play [song]', 'pause', 'stop'")
    print("    - 'volume up', 'volume down'")
    print("    - 'tracking on', 'tracking off'")
    print("\n  Ctrl+C to stop")
    print("=" * 50 + "\n")
    
    # Start music player thread
    music_player, music_cmd_queue = start_music_player()
    
    # Start web server thread
    web_thread = Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # Start voice command thread
    voice_thread = start_voice_commands(device_index=mic_device)
    
    # Start command router thread
    cmd_thread = Thread(target=process_commands, daemon=True)
    cmd_thread.start()
    
    # Run vision tracker in main thread
    try:
        run_vision_tracker()
    except KeyboardInterrupt:
        pass
    finally:
        shutdown()


if __name__ == "__main__":
    # Check for --list-devices flag
    if len(sys.argv) > 1 and sys.argv[1] == '--list-devices':
        list_audio_devices()
    else:
        main()
