#!/usr/bin/env python3
"""
Direct test of Bell state circuit generation and validation.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ket_to_ride.quantum.qiskit_circuit_simulator import CircuitSimulator
from ket_to_ride.game.player import MissionCard
from ket_to_ride.game.game_state import GameState

def test_bell_state_direct():
    """Test Bell state generation directly."""
    
    print("=== Direct Bell State Test ===")
    print()
    
    # Initialize quantum simulator
    quantum_simulator = CircuitSimulator()
    
    # Test the Bell state circuit directly
    print("Testing Bell state circuit directly...")
    
    # Bell state circuit: H on first qubit, then CNOT
    initial_state = "|00⟩"
    target_state = "|Bell+⟩"
    gate_sequence = ["H", "CNOT"]
    
    print(f"Initial state: {initial_state}")
    print(f"Target state: {target_state}")
    print(f"Gate sequence: {gate_sequence}")
    print()
    
    # Simulate the circuit
    final_state = quantum_simulator.simulate_circuit(initial_state, gate_sequence, 2)
    
    print(f"Final state: {final_state.get_state_description()}")
    print(f"Matches target: {final_state.matches_target(target_state)}")
    print()
    
    # Test with route-based simulation
    print("Testing route-based Bell state simulation...")
    
    # Create a simple route structure for Bell state
    routes = [
        {"from": "Princeton", "to": "Carnegie", "gate": ["H"], "length": 1},
        {"from": "GeorgiaTech", "to": "Carnegie", "gate": ["I"], "length": 1},
        {"from": "Carnegie", "to": "U Chicago", "gate": ["CNOT"], "length": 1}
    ]
    
    # Simulate the path
    success, final_state, gate_sequence = quantum_simulator.simulate_path(
        initial_state, [("H", 1), ("CNOT", 1)], target_state
    )
    
    print(f"Route simulation success: {success}")
    print(f"Final state: {final_state.get_state_description()}")
    print(f"Gate sequence: {gate_sequence}")
    print()
    
    # Test mission creation and validation
    print("Testing mission creation and validation...")
    
    # Create game state
    config_path = "config/university_map.json"
    game_state = GameState(config_path)
    
    # Create Bell state mission
    start_cities = ["Princeton", "GeorgiaTech"]
    target_city = "U Chicago"
    mission = MissionCard(start_cities, target_city, initial_state, target_state, 50, "hard")
    
    print(f"Mission created: {mission}")
    print()
    
    # Add player and assign mission
    player = game_state.add_player("TestPlayer", (255, 0, 0))
    player.missions = [mission]
    
    # Give player cards
    for _ in range(10):
        cards = game_state.draw_cards(1)
        if cards:
            player.add_cards(cards[0])
    
    print(f"Player hand: {player.hand}")
    print()
    
    # Manually claim the required routes for Bell state
    print("Manually claiming Bell state routes...")
    
    # Find and claim Princeton → Carnegie (H gate)
    for i, route in enumerate(game_state.routes):
        if ((route['from'] == 'Princeton' and route['to'] == 'Carnegie') or 
            (route['from'] == 'Carnegie' and route['to'] == 'Princeton')):
            if 'H' in route['gate']:
                if game_state.claim_route(player, i, 'H', 0):
                    print(f"✓ Claimed Princeton ↔ Carnegie with H gate")
                break
    
    # Find and claim GeorgiaTech → Carnegie (I gate)
    for i, route in enumerate(game_state.routes):
        if ((route['from'] == 'GeorgiaTech' and route['to'] == 'Carnegie') or 
            (route['from'] == 'Carnegie' and route['to'] == 'GeorgiaTech')):
            if 'I' in route['gate']:
                if game_state.claim_route(player, i, 'I', 0):
                    print(f"✓ Claimed GeorgiaTech ↔ Carnegie with I gate")
                break
    
    # Find and claim Carnegie → U Chicago (CNOT gate)
    for i, route in enumerate(game_state.routes):
        if ((route['from'] == 'Carnegie' and route['to'] == 'U Chicago') or 
            (route['from'] == 'U Chicago' and route['to'] == 'Carnegie')):
            if 'CNOT' in route['gate']:
                if game_state.claim_route(player, i, 'CNOT', 0):
                    print(f"✓ Claimed Carnegie ↔ U Chicago with CNOT gate")
                break
    
    print()
    print(f"Claimed routes: {player.claimed_routes}")
    print()
    
    # Test mission completion
    print("Testing mission completion...")
    if game_state.check_mission_completion(player):
        print("✓ Mission completed! Bell state achieved!")
        print(f"Player score: {player.score}")
    else:
        print("✗ Mission not completed")
    
    print()
    
    # Test quantum state validation
    print("Testing quantum state validation...")
    final_state = quantum_simulator.simulate_multi_qubit_circuit(
        start_cities, target_city, initial_state, player.claimed_routes, game_state.routes
    )
    
    print(f"Final quantum state: {final_state}")
    
    # Check if it matches Bell state
    bell_states = ["|Bell+⟩", "|Φ+⟩", "(|00⟩ + |11⟩)/√2"]
    is_bell_state = any(bell in str(final_state) for bell in bell_states)
    
    if is_bell_state:
        print("✓ Quantum state matches Bell state!")
    else:
        print("✗ Quantum state does not match Bell state")
    
    return mission

if __name__ == "__main__":
    mission = test_bell_state_direct()
    print("\n=== Bell State Test Complete ===") 