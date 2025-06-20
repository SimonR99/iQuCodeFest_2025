#!/usr/bin/env python3
"""
Test script to validate Bell state generation in the quantum circuit network.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ket_to_ride.quantum.qiskit_circuit_simulator import QiskitCircuitSimulator
from ket_to_ride.game.game_state import GameState

def test_bell_state_generation():
    """Test that the Bell state scenario works correctly."""
    
    print("Testing Bell State Generation")
    print("=" * 50)
    
    # Initialize the quantum simulator
    simulator = QiskitCircuitSimulator()
    
    # Define the Bell state circuit manually
    print("1. Manual Bell State Circuit Test")
    print("-" * 30)
    
    # Create Bell state: |00⟩ → |Bell+⟩ = (|00⟩ + |11⟩)/√2
    # Circuit: H on qubit 0, then CNOT(0,1)
    initial_state = "|00⟩"
    target_state = "|Bell+⟩"
    
    # Manual gate sequence: H on first qubit, then CNOT
    gate_sequence = ["H", "CNOT"]
    
    print(f"Initial state: {initial_state}")
    print(f"Target state: {target_state}")
    print(f"Gate sequence: {' → '.join(gate_sequence)}")
    
    # Simulate the circuit
    success, final_state, _ = simulator.simulate_path(initial_state, [("H", 1), ("CNOT", 1)], target_state)
    
    print(f"Simulation success: {success}")
    print(f"Final state description: {final_state.get_state_description()}")
    print(f"Final probabilities: {final_state.get_probabilities()}")
    print()
    
    # Test the actual map routes
    print("2. Map Route Bell State Test")
    print("-" * 30)
    
    # Initialize game state
    config_path = "config/university_map.json"
    game_state = GameState(config_path)
    
    # Create a Bell state mission
    start_cities = ["Princeton", "GeorgiaTech"]
    target_city = "U Chicago"
    initial_state = "|00⟩"
    target_state = "|Bell+⟩"
    
    print(f"Mission: ({' AND '.join(start_cities)}) {initial_state} → {target_city} {target_state}")
    
    # Check route feasibility
    feasible_paths = game_state.quantum_simulator.check_route_feasibility(
        start_cities, target_city, initial_state, target_state, game_state.routes
    )
    
    print(f"Feasible paths found: {len(feasible_paths)}")
    
    for i, path_info in enumerate(feasible_paths):
        print(f"  Path {i+1}: {path_info['start_city']} → {target_city}")
        print(f"    Route sequence: {[route['from'] + '-' + route['to'] for route in path_info['path']]}")
        print(f"    Gate sequence: {[gc[0] for gc in path_info['gate_combination']]}")
        print(f"    Final state: {path_info['final_state']}")
        print()
    
    # Test specific Bell state circuit
    print("3. Specific Bell State Circuit Validation")
    print("-" * 40)
    
    # The circuit should be:
    # Princeton (qubit 0) → Carnegie (H gate) → U Chicago (CNOT control)
    # GeorgiaTech (qubit 1) → Carnegie (I gate) → U Chicago (CNOT target)
    
    # Simulate this specific path
    princeton_path = [("H", 1)]  # Princeton to Carnegie with H gate
    georgiatech_path = [("I", 1)]  # GeorgiaTech to Carnegie with I gate
    carnegie_path = [("CNOT", 1)]  # Carnegie to U Chicago with CNOT gate
    
    # Combine the paths (simplified - in reality we'd need to track both qubits)
    combined_gates = princeton_path + georgiatech_path + carnegie_path
    
    print(f"Princeton path: {princeton_path}")
    print(f"GeorgiaTech path: {georgiatech_path}")
    print(f"Carnegie path: {carnegie_path}")
    print(f"Combined gates: {combined_gates}")
    
    # Test the combined circuit
    success, final_state, gate_sequence = simulator.simulate_path(
        initial_state, combined_gates, target_state
    )
    
    print(f"Combined circuit success: {success}")
    print(f"Final state: {final_state.get_state_description()}")
    print(f"Gate sequence: {' → '.join(gate_sequence)}")
    print()
    
    # Test individual route simulation
    print("4. Individual Route Simulation")
    print("-" * 35)
    
    # Find the specific routes in the map
    princeton_carnegie_route = None
    georgiatech_carnegie_route = None
    carnegie_chicago_route = None
    
    for route in game_state.routes:
        if route['from'] == 'Princeton' and route['to'] == 'Carnegie':
            princeton_carnegie_route = route
        elif route['from'] == 'Carnegie' and route['to'] == 'Princeton':
            princeton_carnegie_route = route
        elif route['from'] == 'GeorgiaTech' and route['to'] == 'Carnegie':
            georgiatech_carnegie_route = route
        elif route['from'] == 'Carnegie' and route['to'] == 'GeorgiaTech':
            georgiatech_carnegie_route = route
        elif route['from'] == 'Carnegie' and route['to'] == 'U Chicago':
            carnegie_chicago_route = route
        elif route['from'] == 'U Chicago' and route['to'] == 'Carnegie':
            carnegie_chicago_route = route
    
    print("Found routes:")
    if princeton_carnegie_route:
        print(f"  Princeton-Carnegie: {princeton_carnegie_route['gate']}")
    if georgiatech_carnegie_route:
        print(f"  GeorgiaTech-Carnegie: {georgiatech_carnegie_route['gate']}")
    if carnegie_chicago_route:
        print(f"  Carnegie-U Chicago: {carnegie_chicago_route['gate']}")
    
    print("\nTest completed!")

def create_bell_state_mission():
    """Create a specific Bell state mission for testing."""
    
    print("5. Creating Bell State Mission")
    print("-" * 35)
    
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
    
    from ket_to_ride.game.player import MissionCard
    
    # Create the mission
    mission = MissionCard(start_cities, target_city, initial_state, target_state, points, difficulty)
    print(f"Created mission: {mission}")
    
    # Add a test player
    player = game_state.add_player("TestPlayer", (255, 0, 0))
    
    # Give the player some cards
    for _ in range(10):
        cards = game_state.draw_cards(1)
        if cards:
            player.add_cards(cards[0])
    
    print(f"Player hand: {player.hand}")
    
    # Assign the mission to the player
    player.missions = [mission]
    
    # Simulate claiming the required routes
    print("\nSimulating route claiming...")
    
    # Find the routes we need to claim
    princeton_carnegie_route_idx = None
    georgiatech_carnegie_route_idx = None
    carnegie_chicago_route_idx = None
    
    for i, route in enumerate(game_state.routes):
        if (route['from'] == 'Princeton' and route['to'] == 'Carnegie') or \
           (route['from'] == 'Carnegie' and route['to'] == 'Princeton'):
            princeton_carnegie_route_idx = i
        elif (route['from'] == 'GeorgiaTech' and route['to'] == 'Carnegie') or \
             (route['from'] == 'Carnegie' and route['to'] == 'GeorgiaTech'):
            georgiatech_carnegie_route_idx = i
        elif (route['from'] == 'Carnegie' and route['to'] == 'U Chicago') or \
             (route['from'] == 'U Chicago' and route['to'] == 'Carnegie'):
            carnegie_chicago_route_idx = i
    
    print(f"Route indices: Princeton-Carnegie: {princeton_carnegie_route_idx}, "
          f"GeorgiaTech-Carnegie: {georgiatech_carnegie_route_idx}, "
          f"Carnegie-U Chicago: {carnegie_chicago_route_idx}")
    
    # Claim the routes (simplified - in real game this would be done by clicking)
    if princeton_carnegie_route_idx is not None:
        # Claim Princeton-Carnegie with H gate
        success = game_state.claim_route(player, princeton_carnegie_route_idx, "H")
        print(f"Claimed Princeton-Carnegie with H: {success}")
    
    if georgiatech_carnegie_route_idx is not None:
        # Claim GeorgiaTech-Carnegie with I gate
        success = game_state.claim_route(player, georgiatech_carnegie_route_idx, "I")
        print(f"Claimed GeorgiaTech-Carnegie with I: {success}")
    
    if carnegie_chicago_route_idx is not None:
        # Claim Carnegie-U Chicago with CNOT gate
        success = game_state.claim_route(player, carnegie_chicago_route_idx, "CNOT")
        print(f"Claimed Carnegie-U Chicago with CNOT: {success}")
    
    # Check mission completion
    print("\nChecking mission completion...")
    completion_result = game_state.check_mission_completion(player)
    print(f"Mission completion result: {completion_result}")
    
    if mission.completed:
        print(f"🎉 Mission completed! Player score: {player.score}")
    else:
        print(f"❌ Mission not completed yet. Player score: {player.score}")
    
    return mission, player

if __name__ == "__main__":
    test_bell_state_generation()
    print("\n" + "="*60 + "\n")
    create_bell_state_mission() 