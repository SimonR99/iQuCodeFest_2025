#!/usr/bin/env python3
"""
Create a Bell state destination card for validation.
This script creates a Bell state mission that can be used to test the game mechanics.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ket_to_ride.game.player import MissionCard
from ket_to_ride.game.game_state import GameState
from ket_to_ride.quantum.qiskit_circuit_simulator import CircuitSimulator

def create_bell_state_card():
    """Create a Bell state destination card for validation."""
    
    print("=== Bell State Destination Card Generator ===")
    print()
    
    # Create the Bell state mission
    start_cities = ["Princeton", "GeorgiaTech"]
    target_city = "U Chicago"
    initial_state = "|00⟩"
    target_state = "|Bell+⟩"
    points = 50
    difficulty = "hard"
    
    print("Creating Bell State Mission:")
    print(f"  Start cities: {start_cities}")
    print(f"  Target city: {target_city}")
    print(f"  Initial state: {initial_state}")
    print(f"  Target state: {target_state}")
    print(f"  Points: {points}")
    print(f"  Difficulty: {difficulty}")
    print()
    
    # Create the mission card
    mission = MissionCard(start_cities, target_city, initial_state, target_state, points, difficulty)
    print(f"✓ Mission card created: {mission}")
    print()
    
    # Validate the quantum circuit
    print("Validating quantum circuit...")
    quantum_simulator = CircuitSimulator()
    
    # Test the Bell state circuit: H on first qubit, then CNOT
    gate_sequence = ["H", "CNOT"]
    final_state = quantum_simulator.simulate_circuit(initial_state, gate_sequence, 2)
    
    print(f"  Initial state: {initial_state}")
    print(f"  Gate sequence: {gate_sequence}")
    print(f"  Final state: {final_state.get_state_description()}")
    print(f"  Matches target: {final_state.matches_target(target_state)}")
    print()
    
    # Show the required routes for this mission
    print("Required routes for Bell state:")
    print("  1. Princeton → Carnegie: H gate (creates superposition)")
    print("  2. GeorgiaTech → Carnegie: I gate (identity, no change)")
    print("  3. Carnegie → U Chicago: CNOT gate (creates entanglement)")
    print()
    
    # Show the quantum circuit diagram
    print("Quantum Circuit Diagram:")
    print("  Qubit 0 (Princeton): |0⟩ ──H───●───")
    print("                                │")
    print("  Qubit 1 (GeorgiaTech): |0⟩ ──┼───X───")
    print("                                │")
    print("  Result: |Bell+⟩ = (|00⟩ + |11⟩)/√2")
    print()
    
    # Test with game state
    print("Testing with game state...")
    config_path = "config/university_map.json"
    game_state = GameState(config_path)
    
    # Add a test player
    player = game_state.add_player("TestPlayer", (255, 0, 0))
    
    # Give the player some cards
    for _ in range(10):
        cards = game_state.draw_cards(1)
        if cards:
            player.add_cards(cards[0])
    
    print(f"  Player hand: {player.hand}")
    
    # Assign the mission to the player
    player.missions = [mission]
    print(f"  Mission assigned to player")
    print()
    
    # Show how to complete the mission
    print("To complete this Bell state mission:")
    print("  1. Claim Princeton → Carnegie route with H gate")
    print("  2. Claim GeorgiaTech → Carnegie route with I gate") 
    print("  3. Claim Carnegie → U Chicago route with CNOT gate")
    print("  4. The mission will be automatically validated")
    print()
    
    # Show the expected quantum state
    print("Expected quantum state after completion:")
    print("  |Bell+⟩ = (|00⟩ + |11⟩)/√2")
    print("  This is a maximally entangled two-qubit state")
    print("  Measurement probabilities: 50% |00⟩, 50% |11⟩")
    print()
    
    print("=== Bell State Card Ready for Validation ===")
    print(f"Mission: {mission}")
    
    return mission

if __name__ == "__main__":
    mission = create_bell_state_card() 