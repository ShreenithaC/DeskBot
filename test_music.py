#!/usr/bin/env python3
"""
Test script for music player.
"""

import time
import sys
from src.music_player import start_music_player, index_music_folder

def main():
    print("Music Player Test")
    print("=" * 40)
    
    # Index music first
    songs = index_music_folder()
    if not songs:
        print("\nNo songs found!")
        print("Add music files to ./music folder")
        return
    
    # Start player
    player, cmd_queue = start_music_player()
    time.sleep(1)  # Wait for init
    
    print("\nCommands: play, pause, stop, up, down, quit")
    print("-" * 40)
    
    try:
        while True:
            cmd = input("> ").strip().lower()
            
            if cmd == 'quit' or cmd == 'q':
                break
            elif cmd == 'play':
                cmd_queue.put({'action': 'play', 'query': None})
            elif cmd.startswith('play '):
                query = cmd[5:].strip()
                cmd_queue.put({'action': 'play', 'query': query})
            elif cmd == 'pause':
                cmd_queue.put({'action': 'pause'})
            elif cmd == 'stop':
                cmd_queue.put({'action': 'stop'})
            elif cmd == 'up':
                cmd_queue.put({'action': 'volume_up'})
            elif cmd == 'down':
                cmd_queue.put({'action': 'volume_down'})
            elif cmd == 'list':
                for song in songs:
                    print(f"  - {song['name']}")
            else:
                print("Unknown command")
    
    except KeyboardInterrupt:
        pass
    
    print("\nShutting down...")
    player.shutdown()


if __name__ == "__main__":
    main()
