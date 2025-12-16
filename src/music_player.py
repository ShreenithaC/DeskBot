"""
Music player module using VLC.
Runs in a background thread and receives commands from a queue.
"""

import os
import time
from threading import Thread
from queue import Queue, Empty
from difflib import SequenceMatcher

# VLC for playback
try:
    import vlc
    VLC_AVAILABLE = True
except ImportError:
    VLC_AVAILABLE = False
    print("python-vlc not available - run: pip install python-vlc")
    print("Also install VLC: sudo apt-get install vlc")

# Supported audio formats
AUDIO_EXTENSIONS = ('.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac')
MUSIC_FOLDER = "./music"


def index_music_folder(folder=MUSIC_FOLDER):
    """
    Recursively index all audio files in the music folder.
    Returns a list of (filename, full_path) tuples.
    """
    music_files = []
    
    if not os.path.exists(folder):
        print(f"Music folder not found: {folder}")
        print(f"Create it with: mkdir -p {folder}")
        return music_files
    
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(AUDIO_EXTENSIONS):
                full_path = os.path.join(root, file)
                # Store filename without extension for matching
                name_without_ext = os.path.splitext(file)[0]
                music_files.append({
                    'name': name_without_ext,
                    'filename': file,
                    'path': full_path
                })
    
    return music_files


def find_best_match(query, music_files):
    """
    Find the best matching song for a query.
    Uses fuzzy string matching.
    """
    if not music_files:
        return None
    
    if not query:
        # Return first song if no query
        return music_files[0]
    
    query_lower = query.lower()
    best_match = None
    best_score = 0
    
    for song in music_files:
        name_lower = song['name'].lower()
        
        # Check for substring match first
        if query_lower in name_lower:
            score = len(query_lower) / len(name_lower) + 0.5
        else:
            # Use fuzzy matching
            score = SequenceMatcher(None, query_lower, name_lower).ratio()
        
        if score > best_score:
            best_score = score
            best_match = song
    
    # Only return if score is reasonable
    if best_score > 0.3:
        return best_match
    
    return None


class MusicPlayerThread(Thread):
    """Background thread for music playback."""
    
    def __init__(self, command_queue=None):
        super().__init__(daemon=True)
        self.command_queue = command_queue or Queue()
        self._running = True
        
        # VLC player
        self.instance = None
        self.player = None
        self.current_volume = 70  # Default volume 0-100
        
        # Music library
        self.music_files = []
        self.current_song = None
    
    def _init_vlc(self):
        """Initialize VLC instance and player."""
        if not VLC_AVAILABLE:
            print("[Music] VLC not available")
            return False
        
        try:
            # Create VLC instance with no video
            self.instance = vlc.Instance('--no-xlib', '--quiet')
            self.player = self.instance.media_player_new()
            self.player.audio_set_volume(self.current_volume)
            print(f"[Music] VLC initialized, volume: {self.current_volume}%")
            return True
        except Exception as e:
            print(f"[Music] Failed to initialize VLC: {e}")
            return False
    
    def _index_library(self):
        """Index the music folder."""
        self.music_files = index_music_folder(MUSIC_FOLDER)
        print(f"[Music] Indexed {len(self.music_files)} songs in {MUSIC_FOLDER}")
        
        if self.music_files:
            print("[Music] Available songs:")
            for song in self.music_files[:10]:  # Show first 10
                print(f"         - {song['name']}")
            if len(self.music_files) > 10:
                print(f"         ... and {len(self.music_files) - 10} more")
    
    def play(self, query=None):
        """Play a song. If query is empty, resume current. If query provided, search and play."""
        if not VLC_AVAILABLE or not self.player:
            print("[Music] Player not available")
            return
        
        # If no query and something is paused, resume
        if not query and self.current_song:
            state = self.player.get_state()
            if state == vlc.State.Paused:
                self.player.play()
                print(f"[Music] Resumed: {self.current_song['name']}")
                return
        
        # Search for song
        if query:
            song = find_best_match(query, self.music_files)
        elif self.music_files:
            song = self.music_files[0]
        else:
            print("[Music] No songs available")
            return
        
        if not song:
            print(f"[Music] No match found for: {query}")
            return
        
        # Play the song
        try:
            media = self.instance.media_new(song['path'])
            self.player.set_media(media)
            self.player.play()
            self.current_song = song
            print(f"[Music] Playing: {song['name']}")
        except Exception as e:
            print(f"[Music] Playback error: {e}")
    
    def pause(self):
        """Pause playback."""
        if self.player:
            self.player.pause()
            print("[Music] Paused")
    
    def stop(self):
        """Stop playback."""
        if self.player:
            self.player.stop()
            self.current_song = None
            print("[Music] Stopped")
    
    def volume_up(self, step=10):
        """Increase volume."""
        if self.player:
            self.current_volume = min(100, self.current_volume + step)
            self.player.audio_set_volume(self.current_volume)
            print(f"[Music] Volume: {self.current_volume}%")
    
    def volume_down(self, step=10):
        """Decrease volume."""
        if self.player:
            self.current_volume = max(0, self.current_volume - step)
            self.player.audio_set_volume(self.current_volume)
            print(f"[Music] Volume: {self.current_volume}%")
    
    def _process_command(self, command):
        """Process a command dict."""
        action = command.get('action')
        
        if action == 'play':
            query = command.get('query')
            self.play(query)
        elif action == 'pause':
            self.pause()
        elif action == 'stop':
            self.stop()
        elif action == 'volume_up':
            self.volume_up()
        elif action == 'volume_down':
            self.volume_down()
        else:
            print(f"[Music] Unknown action: {action}")
    
    def run(self):
        """Main thread loop."""
        if not self._init_vlc():
            print("[Music] Music player disabled")
            return
        
        self._index_library()
        
        print("[Music] Player ready, waiting for commands...")
        
        while self._running:
            try:
                # Wait for command with timeout
                command = self.command_queue.get(timeout=0.5)
                self._process_command(command)
            except Empty:
                pass
            except Exception as e:
                print(f"[Music] Error: {e}")
        
        # Cleanup
        if self.player:
            self.player.stop()
        print("[Music] Player stopped")
    
    def send_command(self, action, query=None):
        """Helper to send a command to the player."""
        self.command_queue.put({'action': action, 'query': query})
    
    def shutdown(self):
        """Stop the music player thread."""
        self._running = False
        if self.player:
            self.player.stop()


def start_music_player():
    """Start the music player thread and return it."""
    cmd_queue = Queue()
    player = MusicPlayerThread(command_queue=cmd_queue)
    player.start()
    return player, cmd_queue


# Quick test when run directly
if __name__ == "__main__":
    import sys
    
    print("Music Player Test")
    print("-" * 40)
    
    # Index music
    songs = index_music_folder()
    print(f"\nFound {len(songs)} songs")
    
    if '--play' in sys.argv:
        player, cmd_queue = start_music_player()
        time.sleep(1)  # Wait for init
        
        # Play first song or specified
        query = None
        if len(sys.argv) > sys.argv.index('--play') + 1:
            query = sys.argv[sys.argv.index('--play') + 1]
        
        cmd_queue.put({'action': 'play', 'query': query})
        
        try:
            print("\nPlaying... Press Ctrl+C to stop")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            player.shutdown()
