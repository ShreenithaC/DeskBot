#!/usr/bin/env python3
"""
Test script for voice commands.
Run this to test microphone and speech recognition separately.
"""

import sys
import time

from src.voice_commands import (
    list_audio_devices,
    find_usb_microphone,
    start_voice_commands,
    parse_command
)
from src.shared_state import shared


def test_parsing():
    """Test command parsing."""
    print("\n" + "=" * 40)
    print("  COMMAND PARSING TEST")
    print("=" * 40)
    
    test_phrases = [
        "play some jazz music",
        "play",
        "pause",
        "stop",
        "volume up",
        "turn it up",
        "volume down",
        "quieter",
        "tracking on",
        "start tracking",
        "tracking off",
        "stop tracking",
        "hello world",  # Should return None
        "",  # Should return None
    ]
    
    for phrase in test_phrases:
        result = parse_command(phrase)
        status = "✓" if result else "✗"
        print(f"  {status} '{phrase}' -> {result}")


def test_microphone(device_index=None):
    """Test microphone input and speech recognition."""
    print("\n" + "=" * 40)
    print("  MICROPHONE TEST")
    print("=" * 40)
    print("  Speak commands into the microphone.")
    print("  Press Ctrl+C to stop.")
    print("=" * 40 + "\n")
    
    # Start voice command thread
    voice_thread = start_voice_commands(device_index=device_index)
    
    try:
        # Monitor for commands
        while True:
            command = shared.get_command(timeout=0.5)
            if command:
                print(f"\n>>> Received command: {command}\n")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping...")
        voice_thread.stop()
        shared.running = False


if __name__ == "__main__":
    if '--list-devices' in sys.argv or '-l' in sys.argv:
        list_audio_devices()
    elif '--parse' in sys.argv or '-p' in sys.argv:
        test_parsing()
    else:
        # Get optional device index
        device_index = None
        if '--mic' in sys.argv:
            try:
                idx = sys.argv.index('--mic')
                device_index = int(sys.argv[idx + 1])
            except (IndexError, ValueError):
                pass
        
        # List devices first
        list_audio_devices()
        
        # Run microphone test
        test_microphone(device_index)
