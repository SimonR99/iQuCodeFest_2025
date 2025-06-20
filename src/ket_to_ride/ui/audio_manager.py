import pygame
import os
from typing import Optional

class AudioManager:
    """Manages background music and sound effects for the game"""
    
    def __init__(self):
        self.music_volume = 0.3  # Default volume (30%)
        self.sfx_volume = 0.5    # Default SFX volume (50%)
        self.current_music: Optional[str] = None
        self.music_enabled = True
        self.sfx_enabled = True
        
        # Initialize pygame mixer
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        
        # Load audio files
        self.audio_path = os.path.join("assets", "audio")
        self.load_audio_files()
        
    def load_audio_files(self):
        """Load all audio files"""
        self.audio_files = {}
        
        # Try to load background music
        music_files = [
            "background_music.mp3",
            "background_music.wav",
            "music.mp3",
            "music.wav"
        ]
        
        for music_file in music_files:
            music_path = os.path.join(self.audio_path, music_file)
            if os.path.exists(music_path):
                self.audio_files["background_music"] = music_path
                print(f"Loaded background music: {music_path}")
                break
        else:
            print("No background music found")
            self.audio_files["background_music"] = None
            
    def play_background_music(self, music_name: str = "background_music", loop: bool = True):
        """Play background music"""
        if not self.music_enabled:
            return
            
        music_path = self.audio_files.get(music_name)
        if music_path and music_path != self.current_music:
            try:
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(self.music_volume)
                if loop:
                    pygame.mixer.music.play(-1)  # -1 means loop indefinitely
                else:
                    pygame.mixer.music.play()
                self.current_music = music_path
                print(f"Playing background music: {music_name}")
            except Exception as e:
                print(f"Error playing background music: {e}")
                
    def stop_background_music(self):
        """Stop background music"""
        pygame.mixer.music.stop()
        self.current_music = None
        
    def pause_background_music(self):
        """Pause background music"""
        pygame.mixer.music.pause()
        
    def unpause_background_music(self):
        """Unpause background music"""
        pygame.mixer.music.unpause()
        
    def set_music_volume(self, volume: float):
        """Set music volume (0.0 to 1.0)"""
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume)
        
    def set_sfx_volume(self, volume: float):
        """Set sound effects volume (0.0 to 1.0)"""
        self.sfx_volume = max(0.0, min(1.0, volume))
        
    def toggle_music(self):
        """Toggle music on/off"""
        self.music_enabled = not self.music_enabled
        if not self.music_enabled:
            self.stop_background_music()
        elif self.current_music:
            self.play_background_music()
            
    def toggle_sfx(self):
        """Toggle sound effects on/off"""
        self.sfx_enabled = not self.sfx_enabled
        
    def cleanup(self):
        """Clean up audio resources"""
        pygame.mixer.quit() 