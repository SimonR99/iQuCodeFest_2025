#!/usr/bin/env python3
"""
Script to generate a Bell state destination card for validation.
This creates a specific Bell state mission: Princeton and GeorgiaTech to U Chicago.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ket_to_ride.game.game_state import GameState
from ket_to_ride.game.player import MissionCard, GateType
from ket_to_ride.quantum.qiskit_circuit_simulator import CircuitSimulator

def generate_bell_state_mission():
    """Generate a specific Bell state mission for validation."""
    
    print("=== Bell State Mission Generation ===")
    print()
    
    # Initialize game state
    config_path = "config/university_map.json"
    game_state = GameState(config_path)
    
    # Create a Bell state mission manually
    start_cities = ["Princeton", "GeorgiaTech"]
    target_city = "U Chicago"
    initial_state = "|00⟩"
    target_state = "|Bell+⟩"
    points = 50
    difficulty = "hard"
    
    print(f"Creating Bell state mission:")
    print(f"  Start cities: {start_cities}")
    print(f"  Target city: {target_city}")
    print(f"  Initial state: {initial_state}")
    print(f"  Target state: {target_state}")
    print(f"  Points: {points}")
    print(f"  Difficulty: {difficulty}")
    print()
    
    # Create the mission
    mission = MissionCard(start_cities, target_city, initial_state, target_state, points, difficulty)
    print(f"Mission created: {mission}")
    print()
    
    # Add a test player
    player = game_state.add_player("TestPlayer", (255, 0, 0))
    
    # Give the player some cards
    for _ in range(10):
        cards = game_state.draw_cards(1)
        if cards:
            player.add_cards(cards[0])
    
    print(f"Player hand: {player.hand}")
    print()
    
    # Assign the mission to the player
    player.missions = [mission]
    
    # Check if the mission is feasible
    print("Checking mission feasibility...")
    quantum_simulator = CircuitSimulator()
    feasible_paths = quantum_simulator.check_route_feasibility(
        start_cities, target_city, initial_state, target_state, game_state.routes
    )
    
    if feasible_paths:
        print(f"✓ Mission is feasible! Found {len(feasible_paths)} possible paths:")
        for i, path in enumerate(feasible_paths[:3]):  # Show first 3 paths
            print(f"  Path {i+1}: {path['start_city']} → {target_city}")
            print(f"    Gates: {[gc[0] for gc in path['gate_combination']]}")
    else:
        print("✗ Mission is not feasible with current route configuration")
        return None
    
    print()
    
    # Simulate claiming the required routes for the Bell state
    print("Simulating Bell state route claiming...")
    
    # Find the routes we need to claim for the Bell state
    princeton_carnegie_route_idx = None
    georgiatech_carnegie_route_idx = None
    carnegie_chicago_route_idx = None
    
    for i, route in enumerate(game_state.routes):
        if route['from'] == 'Princeton' and route['to'] == 'Carnegie':
            princeton_carnegie_route_idx = i
        elif route['from'] == 'Carnegie' and route['to'] == 'Princeton':
            princeton_carnegie_route_idx = i
        elif route['from'] == 'GeorgiaTech' and route['to'] == 'Carnegie':
            georgiatech_carnegie_route_idx = i
        elif route['from'] == 'Carnegie' and route['to'] == 'GeorgiaTech':
            georgiatech_carnegie_route_idx = i
        elif route['from'] == 'Carnegie' and route['to'] == 'U Chicago':
            carnegie_chicago_route_idx = i
        elif route['from'] == 'U Chicago' and route['to'] == 'Carnegie':
            carnegie_chicago_route_idx = i
    
    print(f"Route indices found:")
    print(f"  Princeton → Carnegie: {princeton_carnegie_route_idx}")
    print(f"  GeorgiaTech → Carnegie: {georgiatech_carnegie_route_idx}")
    print(f"  Carnegie → U Chicago: {carnegie_chicago_route_idx}")
    print()
    
    # Claim the routes
    routes_claimed = []
    
    if princeton_carnegie_route_idx is not None:
        route = game_state.routes[princeton_carnegie_route_idx]
        if 'H' in route['gate']:
            if game_state.claim_route(player, princeton_carnegie_route_idx, 'H', 0):
                routes_claimed.append(f"Princeton → Carnegie (H gate)")
                print(f"✓ Claimed Princeton → Carnegie with H gate")
            else:
                print(f"✗ Failed to claim Princeton → Carnegie with H gate")
    
    if georgiatech_carnegie_route_idx is not None:
        route = game_state.routes[georgiatech_carnegie_route_idx]
        if 'I' in route['gate']:
            if game_state.claim_route(player, georgiatech_carnegie_route_idx, 'I', 0):
                routes_claimed.append(f"GeorgiaTech → Carnegie (I gate)")
                print(f"✓ Claimed GeorgiaTech → Carnegie with I gate")
            else:
                print(f"✗ Failed to claim GeorgiaTech → Carnegie with I gate")
    
    if carnegie_chicago_route_idx is not None:
        route = game_state.routes[carnegie_chicago_route_idx]
        if 'CNOT' in route['gate']:
            if game_state.claim_route(player, carnegie_chicago_route_idx, 'CNOT', 0):
                routes_claimed.append(f"Carnegie → U Chicago (CNOT gate)")
                print(f"✓ Claimed Carnegie → U Chicago with CNOT gate")
            else:
                print(f"✗ Failed to claim Carnegie → U Chicago with CNOT gate")
    
    print()
    print(f"Routes claimed: {len(routes_claimed)}")
    for route in routes_claimed:
        print(f"  - {route}")
    print()
    
    # Check mission completion
    print("Checking mission completion...")
    if game_state.check_mission_completion(player):
        print("✓ Mission completed! Bell state achieved!")
        print(f"Player score: {player.score}")
        print(f"Completed missions: {len(player.get_completed_missions())}")
    else:
        print("✗ Mission not yet completed")
        print(f"Completed missions: {len(player.get_completed_missions())}")
    
    print()
    
    # Validate the quantum state
    print("Validating quantum state...")
    final_state = quantum_simulator.simulate_multi_qubit_path(
        start_cities, target_city, initial_state, target_state, player.claimed_routes
    )
    
    success, final_quantum_state, gate_sequence = final_state
    print(f"Quantum simulation success: {success}")
    print(f"Final quantum state: {final_quantum_state.get_state_description()}")
    print(f"Gate sequence: {gate_sequence}")
    
    # Check if it matches Bell state
    bell_states = ["|Bell+⟩", "|Φ+⟩", "(|00⟩ + |11⟩)/√2"]
    is_bell_state = any(bell in str(final_quantum_state.get_state_description()) for bell in bell_states)
    
    if is_bell_state:
        print("✓ Quantum state matches Bell state!")
    else:
        print("✗ Quantum state does not match Bell state")
    
    return mission

if __name__ == "__main__":
    mission = generate_bell_state_mission()
    if mission:
        print("\n=== Bell State Mission Generated Successfully ===")
        print(f"Mission: {mission}")
    else:
        print("\n=== Failed to Generate Bell State Mission ===") 