#!/usr/bin/env python3
"""
Generate simple sound effects for the game
"""

import pygame
import numpy as np
import os
from scipy.io import wavfile

def generate_sine_wave(frequency, duration, sample_rate=44100):
    """Generate a sine wave at given frequency for given duration"""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = np.sin(2 * np.pi * frequency * t)
    return (wave * 32767).astype(np.int16)

def generate_sound_effect(filename, frequency, duration, volume=0.5):
    """Generate a sound effect and save it"""
    wave = generate_sine_wave(frequency, duration)
    wave = (wave * volume).astype(np.int16)
    
    # Ensure audio directory exists
    os.makedirs("assets/audio", exist_ok=True)
    
    # Save as WAV file using scipy
    wavfile.write(f"assets/audio/{filename}", 44100, wave)
    print(f"Generated {filename}")

def main():
    pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
    
    # Generate sound effects
    generate_sound_effect("button_click.wav", 800, 0.1, 0.3)  # High click sound
    generate_sound_effect("card_draw.wav", 600, 0.2, 0.4)     # Card flip sound
    generate_sound_effect("route_claim.wav", 400, 0.3, 0.5)   # Success sound
    generate_sound_effect("game_start.wav", 200, 0.5, 0.6)    # Game start sound
    
    # Generate background music (simple loop)
    # Create a simple melody
    frequencies = [262, 330, 392, 523, 392, 330]  # C major scale
    duration = 0.3
    sample_rate = 44100
    
    # Combine multiple notes for background music
    total_duration = len(frequencies) * duration
    t = np.linspace(0, total_duration, int(sample_rate * total_duration), False)
    wave = np.zeros_like(t)
    
    for i, freq in enumerate(frequencies):
        start_time = i * duration
        end_time = (i + 1) * duration
        start_sample = int(start_time * sample_rate)
        end_sample = int(end_time * sample_rate)
        
        note_t = t[start_sample:end_sample] - start_time
        note_wave = np.sin(2 * np.pi * freq * note_t)
        
        # Add fade in/out to avoid clicks
        fade_samples = int(0.01 * sample_rate)  # 10ms fade
        if fade_samples > 0:
            fade_in = np.linspace(0, 1, fade_samples)
            fade_out = np.linspace(1, 0, fade_samples)
            
            note_wave[:fade_samples] *= fade_in
            note_wave[-fade_samples:] *= fade_out
        
        wave[start_sample:end_sample] += note_wave
    
    # Normalize and convert to int16
    wave = (wave * 0.3 * 32767).astype(np.int16)
    
    # Save background music
    wavfile.write("assets/audio/background_music.wav", sample_rate, wave)
    print("Generated background_music.wav")
    
    pygame.mixer.quit()
    print("Audio generation complete!")

if __name__ == "__main__":
    main() 