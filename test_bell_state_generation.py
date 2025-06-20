#!/usr/bin/env python3
"""
Test script to verify Bell state mission generation.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ket_to_ride.game.game_state import GameState

def test_bell_state_generation():
    """Test that Bell state missions are generated."""
    
    print("=== Testing Bell State Mission Generation ===")
    print()
    
    # Initialize game state
    config_path = "config/university_map.json"
    game_state = GameState(config_path)
    
    print(f"Total missions generated: {len(game_state.mission_deck)}")
    print()
    
    # Look for Bell state missions
    bell_missions = []
    for i, mission in enumerate(game_state.mission_deck):
        if mission.target_state == "|00⟩ + |11⟩":
            bell_missions.append((i, mission))
    
    if bell_missions:
        print("✓ Bell state missions found:")
        for idx, mission in bell_missions:
            print(f"  Mission {idx}: {mission}")
            print(f"    Start cities: {mission.start_cities}")
            print(f"    Target city: {mission.target_city}")
            print(f"    Initial state: {mission.initial_state}")
            print(f"    Target state: {mission.target_state}")
            print(f"    Points: {mission.points}")
            print(f"    Difficulty: {mission.difficulty}")
            print()
    else:
        print("✗ No Bell state missions found")
        print()
        print("Available missions:")
        for i, mission in enumerate(game_state.mission_deck[:5]):  # Show first 5
            print(f"  {i}: {mission}")
    
    return len(bell_missions) > 0

if __name__ == "__main__":
    success = test_bell_state_generation()
    if success:
        print("=== Bell State Mission Generation Test PASSED ===")
    else:
        print("=== Bell State Mission Generation Test FAILED ===") 