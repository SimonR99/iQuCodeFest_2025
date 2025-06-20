import numpy as np
from typing import List, Tuple, Dict
from enum import Enum

class QuantumState:
    def __init__(self, initial_state: str = "|0⟩"):
        if initial_state == "|0⟩":
            self.state_vector = np.array([1.0, 0.0], dtype=complex)
        elif initial_state == "|1⟩":
            self.state_vector = np.array([0.0, 1.0], dtype=complex)
        else:
            raise ValueError(f"Unsupported initial state: {initial_state}")
    
    def apply_gate(self, gate_matrix: np.ndarray):
        self.state_vector = gate_matrix @ self.state_vector
        
    def measure(self) -> str:
        # Get probabilities
        prob_0 = abs(self.state_vector[0])**2
        prob_1 = abs(self.state_vector[1])**2
        
        # Determine most likely state (for deterministic game mechanics)
        if prob_0 > prob_1:
            return "|0⟩"
        else:
            return "|1⟩"
    
    def get_probabilities(self) -> Tuple[float, float]:
        prob_0 = abs(self.state_vector[0])**2
        prob_1 = abs(self.state_vector[1])**2
        return (prob_0, prob_1)
    
    def matches_target(self, target_state: str, tolerance: float = 0.01) -> bool:
        measurement = self.measure()
        
        # For exact match, check if the dominant state matches target
        if target_state == "|0⟩":
            return abs(self.state_vector[0])**2 > (1.0 - tolerance)
        elif target_state == "|1⟩":
            return abs(self.state_vector[1])**2 > (1.0 - tolerance)
        
        return False

class QuantumGates:
    # Identity gate
    I = np.array([[1, 0], 
                  [0, 1]], dtype=complex)
    
    # Pauli-X gate (NOT gate)
    X = np.array([[0, 1], 
                  [1, 0]], dtype=complex)
    
    # Pauli-Y gate
    Y = np.array([[0, -1j], 
                  [1j, 0]], dtype=complex)
    
    # Pauli-Z gate
    Z = np.array([[1, 0], 
                  [0, -1]], dtype=complex)
    
    # Hadamard gate
    H = np.array([[1, 1], 
                  [1, -1]], dtype=complex) / np.sqrt(2)
    
    # For CNOT, we'll simulate it as a combination of gates in this single-qubit version
    # In a real implementation, this would be a 2-qubit gate
    CNOT = np.array([[1, 0], 
                     [0, 1]], dtype=complex)  # Identity for single qubit

class CircuitSimulator:
    def __init__(self):
        self.gate_matrices = {
            'I': QuantumGates.I,
            'X': QuantumGates.X,
            'Z': QuantumGates.Z,
            'H': QuantumGates.H,
            'CNOT': QuantumGates.CNOT,  # Simplified for single qubit
        }
    
    def simulate_circuit(self, initial_state: str, gate_sequence: List[str]) -> QuantumState:
        """
        Simulate a quantum circuit given an initial state and sequence of gates
        
        Args:
            initial_state: Initial qubit state ("|0⟩" or "|1⟩")
            gate_sequence: List of gate names to apply in order
            
        Returns:
            Final quantum state after applying all gates
        """
        state = QuantumState(initial_state)
        
        for gate_name in gate_sequence:
            if gate_name in self.gate_matrices:
                gate_matrix = self.gate_matrices[gate_name]
                state.apply_gate(gate_matrix)
            else:
                raise ValueError(f"Unknown gate: {gate_name}")
        
        return state
    
    def simulate_path(self, initial_state: str, route_gates: List[Tuple[str, int]], 
                     target_state: str) -> Tuple[bool, QuantumState, List[str]]:
        """
        Simulate a path through the quantum circuit network
        
        Args:
            initial_state: Starting qubit state
            route_gates: List of (gate_type, length) tuples for each route
            target_state: Target qubit state
            
        Returns:
            Tuple of (success, final_state, gate_sequence)
        """
        # Build gate sequence from routes
        gate_sequence = []
        for gate_type, length in route_gates:
            # Apply the gate 'length' times
            gate_sequence.extend([gate_type] * length)
        
        # Simulate the circuit
        final_state = self.simulate_circuit(initial_state, gate_sequence)
        
        # Check if we reached the target
        success = final_state.matches_target(target_state)
        
        return success, final_state, gate_sequence
    
    def get_gate_effect_description(self, gate_name: str) -> str:
        """Get a human-readable description of what each gate does"""
        descriptions = {
            'I': "Identity - no change",
            'X': "Bit flip - |0⟩↔|1⟩", 
            'Z': "Phase flip - |1⟩→-|1⟩",
            'H': "Superposition - creates equal probability",
            'CNOT': "Controlled operation (simplified in single-qubit mode)"
        }
        return descriptions.get(gate_name, "Unknown gate")