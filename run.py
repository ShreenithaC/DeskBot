#!/usr/bin/env python3
"""
Entry point script to run the face tracker.

Usage:
    python run.py                    # Run face tracker with voice commands
    python run.py --list-devices     # List audio input devices
    python run.py --mic 3            # Use microphone device index 3
"""

import sys

from src.main import main
from src.voice_commands import list_audio_devices

if __name__ == "__main__":
    # Parse simple command line args
    mic_device = None
    
    if '--list-devices' in sys.argv:
        list_audio_devices()
        sys.exit(0)
    
    if '--mic' in sys.argv:
        try:
            idx = sys.argv.index('--mic')
            mic_device = int(sys.argv[idx + 1])
            print(f"Using microphone device: {mic_device}")
        except (IndexError, ValueError):
            print("Error: --mic requires a device index number")
            print("Use --list-devices to see available devices")
            sys.exit(1)
    
    main(mic_device=mic_device)
