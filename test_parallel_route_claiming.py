#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ket_to_ride.game.game_state import GameState
from src.ket_to_ride.game.player import Player
from src.ket_to_ride.game import GateType

def test_parallel_route_claiming():
    """Test that parallel routes with identical gates can be claimed individually"""
    print("Testing parallel route claiming with identical gates...")
    
    # Create game state
    config_path = "config/university_map.json"
    game_state = GameState(config_path)
    
    # Add a player
    player = game_state.add_player("TestPlayer", (255, 0, 0))
    
    # Give player some cards
    for _ in range(20):  # Draw more cards
        cards = game_state.draw_cards(1)
        if cards:
            player.add_cards(cards[0])
    
    # Also give some specific cards to ensure we have enough
    player.add_cards(GateType.CNOT, 5)  # Add CNOT cards specifically
    player.add_cards(GateType.X, 5)     # Add X cards specifically
    player.add_cards(GateType.Z, 5)     # Add Z cards specifically
    
    print(f"Player hand: {player.hand}")
    print()
    
    # Find a route with multiple identical gates (like ["X", "X"])
    parallel_route_idx = None
    for i, route in enumerate(game_state.routes):
        gates = route['gate']
        if isinstance(gates, list) and len(gates) > 1:
            # Check if there are multiple identical gates
            if gates.count(gates[0]) > 1:
                parallel_route_idx = i
                print(f"Found parallel route: {route['from']} → {route['to']} with gates: {gates}")
                break
    
    if parallel_route_idx is None:
        print("No parallel route with identical gates found!")
        return False
    
    route = game_state.routes[parallel_route_idx]
    gates = route['gate']
    identical_gate = gates[0]  # All gates are the same
    
    print(f"Testing route: {route['from']} → {route['to']}")
    print(f"Gates: {gates}")
    print(f"Identical gate: {identical_gate}")
    print()
    
    # Test claiming the first gate instance
    print("Claiming first gate instance...")
    if game_state.can_claim_route(player, parallel_route_idx, identical_gate, 0):
        if game_state.claim_route(player, parallel_route_idx, identical_gate, 0):
            print("✓ Successfully claimed first gate instance")
            print(f"Route claimed_by: {route['claimed_by']}")
        else:
            print("✗ Failed to claim first gate instance")
            return False
    else:
        print("✗ Cannot claim first gate instance")
        return False
    
    print()
    
    # Test that the second gate instance is still available
    print("Checking if second gate instance is still available...")
    if game_state.can_claim_route(player, parallel_route_idx, identical_gate, 1):
        print("✓ Second gate instance is still available")
    else:
        print("✗ Second gate instance is not available")
        return False
    
    # Test claiming the second gate instance
    print("Claiming second gate instance...")
    if game_state.claim_route(player, parallel_route_idx, identical_gate, 1):
        print("✓ Successfully claimed second gate instance")
        print(f"Route claimed_by: {route['claimed_by']}")
    else:
        print("✗ Failed to claim second gate instance")
        return False
    
    print()
    
    # Test that no more gate instances are available
    print("Checking if any more gate instances are available...")
    if game_state.can_claim_route(player, parallel_route_idx, identical_gate):
        print("✗ More gate instances are still available")
        return False
    else:
        print("✓ No more gate instances are available")
    
    print()
    print("✓ All tests passed! Parallel route claiming works correctly.")
    return True

if __name__ == "__main__":
    success = test_parallel_route_claiming()
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n❌ Test failed!")
        sys.exit(1) 