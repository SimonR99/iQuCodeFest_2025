#!/usr/bin/env python3
"""
Debug script to understand Bell state mission feasibility.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ket_to_ride.quantum.qiskit_circuit_simulator import CircuitSimulator
import json

def debug_bell_state_feasibility():
    """Debug why the Bell state mission is not feasible."""
    
    print("=== Debugging Bell State Feasibility ===")
    print()
    
    # Load the map configuration
    with open("config/university_map.json", 'r') as f:
        config = json.load(f)
    
    routes = config['routes']
    
    print("Available routes:")
    for i, route in enumerate(routes):
        print(f"  {i}: {route['from']} → {route['to']} with gates {route['gate']}")
    print()
    
    # Check specific routes needed for Bell state
    print("Routes needed for Bell state:")
    print("  1. Princeton → Carnegie (need H gate)")
    print("  2. GeorgiaTech → Carnegie (need I gate)")
    print("  3. Carnegie → U Chicago (need CNOT gate)")
    print()
    
    # Find the specific routes
    princeton_carnegie = None
    georgiatech_carnegie = None
    carnegie_chicago = None
    
    for i, route in enumerate(routes):
        if route['from'] == 'Princeton' and route['to'] == 'Carnegie':
            princeton_carnegie = (i, route)
        elif route['from'] == 'Carnegie' and route['to'] == 'Princeton':
            princeton_carnegie = (i, route)
        elif route['from'] == 'GeorgiaTech' and route['to'] == 'Carnegie':
            georgiatech_carnegie = (i, route)
        elif route['from'] == 'Carnegie' and route['to'] == 'GeorgiaTech':
            georgiatech_carnegie = (i, route)
        elif route['from'] == 'Carnegie' and route['to'] == 'U Chicago':
            carnegie_chicago = (i, route)
        elif route['from'] == 'U Chicago' and route['to'] == 'Carnegie':
            carnegie_chicago = (i, route)
    
    print("Found routes:")
    if princeton_carnegie:
        print(f"  Princeton ↔ Carnegie: {princeton_carnegie[1]['gate']}")
    else:
        print("  ✗ Princeton ↔ Carnegie: NOT FOUND")
    
    if georgiatech_carnegie:
        print(f"  GeorgiaTech ↔ Carnegie: {georgiatech_carnegie[1]['gate']}")
    else:
        print("  ✗ GeorgiaTech ↔ Carnegie: NOT FOUND")
    
    if carnegie_chicago:
        print(f"  Carnegie ↔ U Chicago: {carnegie_chicago[1]['gate']}")
    else:
        print("  ✗ Carnegie ↔ U Chicago: NOT FOUND")
    print()
    
    # Test the quantum simulator
    quantum_simulator = CircuitSimulator()
    
    start_cities = ["Princeton", "GeorgiaTech"]
    target_city = "U Chicago"
    initial_state = "|00⟩"
    target_state = "|Bell+⟩"
    
    print("Testing quantum simulator feasibility check...")
    feasible_paths = quantum_simulator.check_route_feasibility(
        start_cities, target_city, initial_state, target_state, routes
    )
    
    if feasible_paths:
        print(f"✓ Found {len(feasible_paths)} feasible paths:")
        for i, path in enumerate(feasible_paths[:3]):
            print(f"  Path {i+1}: {path['start_city']} → {target_city}")
            print(f"    Gates: {[gc[0] for gc in path['gate_combination']]}")
    else:
        print("✗ No feasible paths found")
        
        # Let's test individual paths
        print("\nTesting individual paths:")
        
        # Test Princeton to U Chicago
        princeton_paths = quantum_simulator.check_route_feasibility(
            ["Princeton"], target_city, "|0⟩", "|+⟩", routes
        )
        print(f"  Princeton → U Chicago: {len(princeton_paths)} paths")
        
        # Test GeorgiaTech to U Chicago
        georgiatech_paths = quantum_simulator.check_route_feasibility(
            ["GeorgiaTech"], target_city, "|0⟩", "|0⟩", routes
        )
        print(f"  GeorgiaTech → U Chicago: {len(georgiatech_paths)} paths")
    
    return feasible_paths

if __name__ == "__main__":
    feasible_paths = debug_bell_state_feasibility() 