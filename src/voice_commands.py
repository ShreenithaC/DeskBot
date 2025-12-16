"""
Offline voice command recognition using Vosk.
Runs in a background thread and publishes commands to the shared queue.
"""

import os
import json
import re
import time
from threading import Thread

# Audio capture
try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    print("sounddevice not available - run: pip install sounddevice")

# Vosk offline speech recognition
try:
    from vosk import Model, KaldiRecognizer, SetLogLevel
    SetLogLevel(-1)  # Suppress Vosk logs
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    print("vosk not available - run: pip install vosk")

from .shared_state import shared

# Configuration
MODEL_PATH = "./models/vosk-model-small-en-us-0.15"
SAMPLE_RATE = 16000
BLOCK_SIZE = 8000


def list_audio_devices():
    """List all available audio input devices."""
    if not SOUNDDEVICE_AVAILABLE:
        print("sounddevice not installed")
        return []
    
    print("\n" + "=" * 50)
    print("  AUDIO INPUT DEVICES")
    print("=" * 50)
    
    devices = sd.query_devices()
    input_devices = []
    
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            input_devices.append({
                'index': i,
                'name': device['name'],
                'channels': device['max_input_channels'],
                'sample_rate': device['default_samplerate']
            })
            marker = " <-- default" if i == sd.default.device[0] else ""
            print(f"  [{i}] {device['name']}{marker}")
            print(f"      Channels: {device['max_input_channels']}, "
                  f"Sample Rate: {device['default_samplerate']}")
    
    print("=" * 50 + "\n")
    return input_devices


def find_usb_microphone():
    """Find a USB microphone device index."""
    if not SOUNDDEVICE_AVAILABLE:
        return None
    
    devices = sd.query_devices()
    
    # Look for USB/webcam microphones
    keywords = ['usb', 'webcam', 'camera', 'c920', 'c270', 'logitech']
    
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            name_lower = device['name'].lower()
            for keyword in keywords:
                if keyword in name_lower:
                    print(f"Found USB microphone: [{i}] {device['name']}")
                    return i
    
    # Fall back to default input device
    default_input = sd.default.device[0]
    if default_input is not None:
        print(f"Using default input device: [{default_input}]")
        return default_input
    
    return None


def parse_command(text):
    """
    Parse recognized text into a command dict.
    Returns None if no command matched.
    """
    text = text.lower().strip()
    
    if not text:
        return None
    
    # Greeting command
    if text in ['hello', 'hi', 'hey', 'hello debo']:
        return {'type': 'greeting', 'action': 'hello'}
    
    # Music commands
    if text.startswith('play'):
        # Extract optional song name after "play"
        query = text[4:].strip()
        return {
            'type': 'music',
            'action': 'play',
            'query': query if query else None
        }
    
    if text in ['pause', 'pause music', 'pause it']:
        return {'type': 'music', 'action': 'pause'}
    
    if text in ['stop', 'stop music', 'stop it', 'stop playing']:
        return {'type': 'music', 'action': 'stop'}
    
    # Volume commands
    if re.match(r'volume up|louder|turn it up|increase volume', text):
        return {'type': 'volume', 'action': 'up'}
    
    if re.match(r'volume down|quieter|turn it down|decrease volume', text):
        return {'type': 'volume', 'action': 'down'}
    
    # Tracking commands
    if re.match(r'tracking on|enable tracking|start tracking|track me', text):
        return {'type': 'tracking', 'action': 'on'}
    
    if re.match(r'tracking off|disable tracking|stop tracking|don\'t track', text):
        return {'type': 'tracking', 'action': 'off'}
    
    return None


def print_vosk_instructions():
    """Print instructions for downloading the Vosk model."""
    print("\n" + "=" * 60)
    print("  VOSK MODEL NOT FOUND")
    print("=" * 60)
    print(f"""
  Voice commands require a Vosk speech recognition model.

  To download the small English model:

  1. Create the models directory:
     mkdir -p ./models

  2. Download the model:
     cd ./models
     wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
     unzip vosk-model-small-en-us-0.15.zip
     rm vosk-model-small-en-us-0.15.zip

  Or download manually from:
     https://alphacephei.com/vosk/models

  Expected path: {MODEL_PATH}
""")
    print("=" * 60 + "\n")


class VoiceCommandThread(Thread):
    """Background thread for voice command recognition."""
    
    def __init__(self, device_index=None, model_path=MODEL_PATH):
        super().__init__(daemon=True)
        self.device_index = device_index
        self.model_path = model_path
        self.model = None
        self.recognizer = None
        self._running = True
    
    def _load_model(self):
        """Load the Vosk model."""
        if not VOSK_AVAILABLE:
            print("Vosk not available")
            return False
        
        if not os.path.exists(self.model_path):
            print_vosk_instructions()
            return False
        
        try:
            print(f"Loading Vosk model from {self.model_path}...")
            self.model = Model(self.model_path)
            self.recognizer = KaldiRecognizer(self.model, SAMPLE_RATE)
            print("Vosk model loaded successfully")
            return True
        except Exception as e:
            print(f"Failed to load Vosk model: {e}")
            return False
    
    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for audio stream - processes audio data."""
        if status:
            print(f"Audio status: {status}")
        
        # Convert to bytes for Vosk
        audio_data = bytes(indata)
        
        if self.recognizer.AcceptWaveform(audio_data):
            result = json.loads(self.recognizer.Result())
            text = result.get('text', '')
            
            if text:
                print(f"Heard: '{text}'")
                command = parse_command(text)
                
                if command:
                    print(f"Command: {command}")
                    shared.put_command(command)
    
    def run(self):
        """Main thread loop."""
        if not SOUNDDEVICE_AVAILABLE:
            print("Voice commands disabled: sounddevice not available")
            return
        
        if not self._load_model():
            print("Voice commands disabled: model not loaded")
            return
        
        # Find microphone if not specified
        if self.device_index is None:
            self.device_index = find_usb_microphone()
        
        if self.device_index is None:
            print("Voice commands disabled: no microphone found")
            list_audio_devices()
            return
        
        print(f"Starting voice recognition on device {self.device_index}...")
        print("Listening for commands: play, pause, stop, volume up/down, tracking on/off")
        
        while self._running and shared.running:
            try:
                # Open audio stream
                with sd.RawInputStream(
                    samplerate=SAMPLE_RATE,
                    blocksize=BLOCK_SIZE,
                    device=self.device_index,
                    dtype='int16',
                    channels=1,
                    callback=self._audio_callback
                ):
                    # Keep stream open while running
                    while self._running and shared.running:
                        time.sleep(0.1)
                        
            except Exception as e:
                print(f"Audio stream error: {e}")
                print("Restarting audio stream in 3 seconds...")
                time.sleep(3)
                
                # Reset recognizer state
                if self.recognizer:
                    self.recognizer = KaldiRecognizer(self.model, SAMPLE_RATE)
        
        print("Voice command thread stopped")
    
    def stop(self):
        """Stop the voice command thread."""
        self._running = False


def start_voice_commands(device_index=None):
    """Start the voice command thread and return it."""
    thread = VoiceCommandThread(device_index=device_index)
    thread.start()
    return thread


# Quick test when run directly
if __name__ == "__main__":
    print("Voice Command Module Test")
    print("-" * 40)
    
    # List devices
    list_audio_devices()
    
    # Test command parsing
    test_phrases = [
        "play some music",
        "play",
        "pause",
        "stop",
        "volume up",
        "volume down",
        "tracking on",
        "tracking off",
        "hello world",  # Should return None
    ]
    
    print("\nCommand parsing test:")
    for phrase in test_phrases:
        result = parse_command(phrase)
        print(f"  '{phrase}' -> {result}")
