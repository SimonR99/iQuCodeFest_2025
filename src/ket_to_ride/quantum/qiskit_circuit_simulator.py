import numpy as np
from typing import List, Tuple, Dict, Union
import random
import itertools

from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
from qiskit_aer import AerSimulator
from qiskit.quantum_info import Statevector
import math


class QiskitQuantumState:
    def __init__(self, initial_state: str = "|0⟩", num_qubits: int = 1):
        """
        Initialize quantum state using Qiskit supporting 1, 2, or 3 qubits.
        
        Args:
            initial_state: String representation like "|0⟩", "|1⟩", "|00⟩", "|+⟩", "|Bell+⟩", etc.
            num_qubits: Number of qubits (1, 2, or 3)
        """
        self.num_qubits = num_qubits
        self.circuit = QuantumCircuit(num_qubits)
        
        # Prepare the initial state
        self._prepare_initial_state(initial_state)
        
    def _prepare_initial_state(self, state_str: str):
        """Prepare the initial state using Qiskit gates"""
        state_str = state_str.strip()
        
        # Single qubit states
        if self.num_qubits == 1:
            if state_str == "|0⟩":
                # Already initialized to |0⟩
                pass
            elif state_str == "|1⟩":
                self.circuit.x(0)
            elif state_str == "|+⟩":  # (|0⟩ + |1⟩)/√2
                self.circuit.h(0)
            elif state_str == "|-⟩":  # (|0⟩ - |1⟩)/√2
                self.circuit.x(0)
                self.circuit.h(0)
        
        # Two qubit states
        elif self.num_qubits == 2:
            if state_str == "|00⟩":
                # Already initialized to |00⟩
                pass
            elif state_str == "|01⟩":
                self.circuit.x(0)  # Qubit 0 is rightmost in Qiskit
            elif state_str == "|10⟩":
                self.circuit.x(1)  # Qubit 1 is leftmost in Qiskit
            elif state_str == "|11⟩":
                self.circuit.x(0)
                self.circuit.x(1)
            elif state_str == "|Bell+⟩" or state_str == "|Φ+⟩":  # (|00⟩ + |11⟩)/√2
                self.circuit.h(0)
                self.circuit.cx(0, 1)
            elif state_str == "|Bell-⟩" or state_str == "|Φ-⟩":  # (|00⟩ - |11⟩)/√2
                self.circuit.h(0)
                self.circuit.cx(0, 1)
                self.circuit.z(0)
            elif state_str == "|Ψ+⟩":  # (|01⟩ + |10⟩)/√2
                self.circuit.x(0)  # Start with |01⟩
                self.circuit.h(1)
                self.circuit.cx(1, 0)
            elif state_str == "|Ψ-⟩":  # (|01⟩ - |10⟩)/√2
                self.circuit.x(0)  # Start with |01⟩
                self.circuit.h(1)
                self.circuit.cx(1, 0)
                self.circuit.z(1)
        
        # Three qubit states
        elif self.num_qubits == 3:
            if state_str == "|000⟩":
                # Already initialized to |000⟩
                pass
            elif state_str == "|001⟩":
                self.circuit.x(0)  # Rightmost qubit
            elif state_str == "|010⟩":
                self.circuit.x(1)  # Middle qubit
            elif state_str == "|011⟩":
                self.circuit.x(0)  # Rightmost qubit
                self.circuit.x(1)  # Middle qubit
            elif state_str == "|100⟩":
                self.circuit.x(2)  # Leftmost qubit
            elif state_str == "|101⟩":
                self.circuit.x(0)  # Rightmost qubit
                self.circuit.x(2)  # Leftmost qubit
            elif state_str == "|110⟩":
                self.circuit.x(1)  # Middle qubit
                self.circuit.x(2)  # Leftmost qubit
            elif state_str == "|111⟩":
                self.circuit.x(0)  # Rightmost qubit
                self.circuit.x(1)  # Middle qubit
                self.circuit.x(2)  # Leftmost qubit
            elif state_str == "|GHZ⟩":  # (|000⟩ + |111⟩)/√2
                self.circuit.h(2)  # Start with leftmost qubit
                self.circuit.cx(2, 1)
                self.circuit.cx(2, 0)
            elif state_str == "|W⟩":  # (|001⟩ + |010⟩ + |100⟩)/√3
                # Create W state using controlled rotations
                self.circuit.ry(2 * np.arccos(np.sqrt(2/3)), 0)
                self.circuit.ch(0, 1)
                self.circuit.ccx(0, 1, 2)
                self.circuit.cx(0, 1)
        else:
            raise ValueError(f"Unsupported quantum state: {state_str} for {self.num_qubits} qubits")
    
    def apply_gate(self, gate_name: str):
        """Apply a quantum gate to the circuit"""
        if gate_name == 'I':
            # Identity gate - apply to first qubit (though it does nothing)
            self.circuit.id(0)
        elif gate_name == 'X':
            # X gate on first qubit
            self.circuit.x(0)
        elif gate_name == 'Z':
            # Z gate on first qubit
            self.circuit.z(0)
        elif gate_name == 'H':
            # Hadamard gate on first qubit
            self.circuit.h(0)
        elif gate_name == 'CNOT':
            if self.num_qubits == 1:
                # CNOT acts as Identity in single qubit context
                self.circuit.id(0)
            elif self.num_qubits >= 2:
                # Standard CNOT gate (control=0, target=1)
                self.circuit.cx(0, 1)
        else:
            raise ValueError(f"Unknown gate: {gate_name}")
    
    def get_statevector(self) -> Statevector:
        """Get the current statevector using Qiskit"""
        return Statevector.from_instruction(self.circuit)
    
    def measure(self) -> str:
        """Measure the quantum state and return the most probable computational basis state"""
        statevector = self.get_statevector()
        probabilities = statevector.probabilities()
        max_idx = np.argmax(probabilities)
        
        # Convert index to binary string
        if self.num_qubits == 1:
            return "|0⟩" if max_idx == 0 else "|1⟩"
        elif self.num_qubits == 2:
            states = ["|00⟩", "|01⟩", "|10⟩", "|11⟩"]
            return states[max_idx]
        elif self.num_qubits == 3:
            states = ["|000⟩", "|001⟩", "|010⟩", "|011⟩", "|100⟩", "|101⟩", "|110⟩", "|111⟩"]
            return states[max_idx]
    
    def get_probabilities(self) -> List[float]:
        """Get probability distribution over computational basis states"""
        statevector = self.get_statevector()
        return statevector.probabilities().tolist()
    
    def matches_target(self, target_state: str, tolerance: float = 0.01) -> bool:
        """Check if current state matches target state within tolerance"""
        try:
            # Create target state circuit
            target_quantum_state = QiskitQuantumState(target_state, self.num_qubits)
            target_statevector = target_quantum_state.get_statevector()
            current_statevector = self.get_statevector()
            
            # Calculate fidelity between states using numpy
            fidelity = abs(np.conj(target_statevector.data) @ current_statevector.data) ** 2
            
            return fidelity > (1.0 - tolerance)
        except ValueError:
            # If target state is not parseable, fall back to measurement comparison
            measurement = self.measure()
            return measurement == target_state
    
    def get_state_description(self) -> str:
        """Get a human-readable description of the current state"""
        statevector = self.get_statevector()
        probabilities = statevector.probabilities()
        state_data = statevector.data
        
        significant_states = []
        
        if self.num_qubits == 1:
            basis_states = ["|0⟩", "|1⟩"]
        elif self.num_qubits == 2:
            basis_states = ["|00⟩", "|01⟩", "|10⟩", "|11⟩"]
        elif self.num_qubits == 3:
            basis_states = ["|000⟩", "|001⟩", "|010⟩", "|011⟩", "|100⟩", "|101⟩", "|110⟩", "|111⟩"]
        
        for i, prob in enumerate(probabilities):
            if prob > 0.01:  # Only show states with >1% probability
                coefficient = state_data[i]
                amplitude = abs(coefficient)
                phase = np.angle(coefficient)
                
                if abs(phase) < 0.1:  # Real positive
                    significant_states.append(f"{amplitude:.3f}{basis_states[i]}")
                elif abs(phase - np.pi) < 0.1:  # Real negative
                    significant_states.append(f"-{amplitude:.3f}{basis_states[i]}")
                else:  # Complex
                    significant_states.append(f"{amplitude:.3f}e^(i{phase:.2f}){basis_states[i]}")
        
        return " + ".join(significant_states) if significant_states else "0"


class QiskitCircuitSimulator:
    def __init__(self):
        # Initialize the Aer simulator
        self.simulator = AerSimulator()
    
    def simulate_circuit(self, initial_state: str, gate_sequence: List[str], num_qubits: int = None) -> QiskitQuantumState:
        """
        Simulate a quantum circuit given an initial state and sequence of gates
        
        Args:
            initial_state: Initial qubit state ("|0⟩", "|00⟩", "|+⟩", "|Bell+⟩", etc.)
            gate_sequence: List of gate names to apply in order
            num_qubits: Number of qubits (inferred from initial_state if not provided)
            
        Returns:
            Final quantum state after applying all gates
        """
        # Infer number of qubits from initial state if not provided
        if num_qubits is None:
            num_qubits = self._infer_num_qubits(initial_state)
        
        state = QiskitQuantumState(initial_state, num_qubits)
        
        for gate_name in gate_sequence:
            state.apply_gate(gate_name)
        
        return state
    
    def _infer_num_qubits(self, state_str: str) -> int:
        """Infer number of qubits from state string"""
        state_str = state_str.strip()
        
        # Single qubit states
        if state_str in ["|0⟩", "|1⟩", "|+⟩", "|-⟩"]:
            return 1
        
        # Two qubit states
        elif state_str in ["|00⟩", "|01⟩", "|10⟩", "|11⟩", "|Bell+⟩", "|Bell-⟩", "|Φ+⟩", "|Φ-⟩", "|Ψ+⟩", "|Ψ-⟩", "|00⟩ + |11⟩"]:
            return 2
        
        # Three qubit states
        elif state_str in ["|000⟩", "|001⟩", "|010⟩", "|011⟩", "|100⟩", "|101⟩", "|110⟩", "|111⟩", "|GHZ⟩", "|W⟩"]:
            return 3
        
        # Default to single qubit
        else:
            return 1
    
    def simulate_path(self, initial_state: str, route_gates: List[Tuple[str, int]], 
                     target_state: str) -> Tuple[bool, QiskitQuantumState, List[str]]:
        """
        Simulate a path through the quantum circuit network
        
        Args:
            initial_state: Starting qubit state
            route_gates: List of (gate_type, length) tuples for each route
            target_state: Target qubit state
            
        Returns:
            Tuple of (success, final_state, gate_sequence)
        """
        # Infer number of qubits from initial and target states
        initial_qubits = self._infer_num_qubits(initial_state)
        target_qubits = self._infer_num_qubits(target_state)
        
        # Use the maximum number of qubits needed
        num_qubits = max(initial_qubits, target_qubits)
        
        # Build gate sequence from routes
        gate_sequence = []
        for gate_type, length in route_gates:
            # Apply the gate 'length' times
            gate_sequence.extend([gate_type] * length)
        
        # Simulate the circuit
        final_state = self.simulate_circuit(initial_state, gate_sequence, num_qubits)
        
        # Check if we reached the target
        success = final_state.matches_target(target_state)
        
        return success, final_state, gate_sequence
    
    def check_route_feasibility(self, start_cities: List[str], target_city: str, 
                               initial_state: str, target_state: str, 
                               available_routes: List[Dict]) -> List[Dict]:
        """
        Check if there are feasible paths from start cities to target that can achieve the quantum transformation.
        
        Args:
            start_cities: List of possible starting cities
            target_city: Target destination city
            initial_state: Initial quantum state
            target_state: Target quantum state
            available_routes: List of all available routes in the game
            
        Returns:
            List of feasible route combinations that can achieve the transformation
        """
        feasible_paths = []
        
        # For multi-qubit missions, we need to ensure ALL start cities have feasible paths
        # For single qubit missions, we only need one feasible path
        if len(start_cities) > 1:
            # Multi-qubit mission: check that ALL start cities have feasible paths
            all_cities_feasible = True
            city_feasible_paths = {}
            
            for start_city in start_cities:
                city_paths = self._find_all_paths(start_city, target_city, available_routes)
                city_feasible = False
                
                for path in city_paths:
                    # Test all possible gate combinations for this path
                    gate_choices = []
                    for route in path:
                        gates = route['gate'] if isinstance(route['gate'], list) else [route['gate']]
                        gate_choices.append([(gate, route['length']) for gate in gates])
                    
                    if gate_choices:
                        for gate_combination in itertools.product(*gate_choices):
                            try:
                                # For multi-qubit paths, we need to simulate the combined effect
                                # This is simplified - in reality, we'd need to track both qubits
                                success, final_state, gate_sequence = self.simulate_path(
                                    initial_state, list(gate_combination), target_state
                                )
                                
                                if success:
                                    city_feasible = True
                                    city_feasible_paths[start_city] = {
                                        'start_city': start_city,
                                        'path': path,
                                        'gate_combination': gate_combination,
                                        'gate_sequence': gate_sequence,
                                        'final_state': final_state.get_state_description()
                                    }
                                    break
                            except Exception as e:
                                continue
                
                if not city_feasible:
                    all_cities_feasible = False
                    break
            
            # Only return feasible paths if ALL cities have feasible paths
            if all_cities_feasible:
                feasible_paths = list(city_feasible_paths.values())
        else:
            # Single qubit mission: check each start city individually
            for start_city in start_cities:
                paths = self._find_all_paths(start_city, target_city, available_routes)
                
                for path in paths:
                    # For each path, we need to test all possible gate combinations
                    # since each route can have multiple gate options
                    gate_choices = []
                    for route in path:
                        gates = route['gate'] if isinstance(route['gate'], list) else [route['gate']]
                        gate_choices.append([(gate, route['length']) for gate in gates])
                    
                    # Generate all possible gate combinations for this path
                    if gate_choices:
                        for gate_combination in itertools.product(*gate_choices):
                            # Test if this specific gate combination can achieve the transformation
                            try:
                                success, final_state, gate_sequence = self.simulate_path(
                                    initial_state, list(gate_combination), target_state
                                )
                                
                                if success:
                                    feasible_paths.append({
                                        'start_city': start_city,
                                        'path': path,
                                        'gate_combination': gate_combination,
                                        'gate_sequence': gate_sequence,
                                        'final_state': final_state.get_state_description()
                                    })
                                    # For efficiency, only keep one working combination per path
                                    break
                            except Exception as e:
                                # Skip gate combinations that cause simulation errors
                                continue
        
        return feasible_paths
    
    def _find_all_paths(self, start: str, target: str, routes: List[Dict], 
                       max_depth: int = 6) -> List[List[Dict]]:
        """Find all paths from start to target city within max_depth"""
        if start == target:
            return [[]]
        
        paths = []
        visited = set()
        
        def dfs(current_city: str, current_path: List[Dict], depth: int):
            if depth > max_depth:
                return
            
            if current_city == target and current_path:
                paths.append(current_path.copy())
                return
            
            if current_city in visited:
                return
            
            visited.add(current_city)
            
            # Find all routes from current city
            for route in routes:
                next_city = None
                if route['from'] == current_city:
                    next_city = route['to']
                elif route['to'] == current_city:
                    next_city = route['from']
                
                if next_city and next_city not in visited:
                    current_path.append(route)
                    dfs(next_city, current_path, depth + 1)
                    current_path.pop()
            
            visited.remove(current_city)
        
        dfs(start, [], 0)
        return paths
    
    def get_gate_effect_description(self, gate_name: str) -> str:
        """Get a human-readable description of what each gate does"""
        descriptions = {
            'I': "Identity - no change",
            'X': "Bit flip - |0⟩↔|1⟩", 
            'Z': "Phase flip - |1⟩→-|1⟩",
            'H': "Superposition - creates equal probability",
            'CNOT': "Controlled operation (acts as Identity on single qubits)"
        }
        return descriptions.get(gate_name, "Unknown gate")

    def simulate_multi_qubit_path(self, start_cities: List[str], target_city: str, 
                                 initial_state: str, target_state: str,
                                 player_routes: List[Dict]) -> Tuple[bool, QiskitQuantumState, List[str]]:
        """
        Simulate a multi-qubit path where multiple qubits travel through the network.
        For each step where multiple qubits pass through the same city/route with multiple gates, try all permutations of gate assignments.
        Mark as success if any permutation leads to the correct quantum state.
        """
        import itertools
        num_qubits = len(start_cities)
        # For now, only handle the Bell state scenario as a proof of concept
        # Find all gates in the player_routes
        gate_options = []
        for route in player_routes:
            gates = route['gate'] if isinstance(route['gate'], list) else [route['gate']]
            gate_options.append(gates)
        # Generate all possible assignments of gates to qubits (permutations for each route)
        all_gate_combinations = list(itertools.product(*gate_options))
        for gate_combo in all_gate_combinations:
            # Build the gate sequence for this permutation
            gate_sequence = []
            for gate in gate_combo:
                gate_sequence.append(gate)
            # Simulate the circuit
            state = QiskitQuantumState(initial_state, num_qubits)
            for gate in gate_sequence:
                state.apply_gate(gate)
            # Check if we reached the target state
            if state.matches_target(target_state):
                return True, state, gate_sequence
        # If none of the permutations worked, return failure
        return False, QiskitQuantumState(initial_state, num_qubits), []


class QuantumGates:
    """Compatibility class for the old gate interface - now uses Qiskit internally"""
    
    @staticmethod
    def get_gate_matrix(gate_name: str, num_qubits: int, target_qubit: int = 0, control_qubit: int = None) -> np.ndarray:
        """
        Get the matrix for a quantum gate applied to a multi-qubit system.
        For compatibility with old interface - converts to Qiskit circuit and extracts matrix.
        """
        # Create a simple circuit to get the gate matrix
        from qiskit.quantum_info import Operator
        
        circuit = QuantumCircuit(num_qubits)
        
        if gate_name == 'I':
            circuit.id(target_qubit)
        elif gate_name == 'X':
            circuit.x(target_qubit)
        elif gate_name == 'Z':
            circuit.z(target_qubit)
        elif gate_name == 'H':
            circuit.h(target_qubit)
        elif gate_name == 'CNOT':
            if num_qubits == 1:
                # CNOT acts as identity in single qubit context
                circuit.id(0)
            elif num_qubits >= 2:
                # Standard CNOT gate (control=0, target=1)
                circuit.cx(0, 1)
        else:
            raise ValueError(f"Unknown gate: {gate_name}")
        
        # Get the unitary matrix from the circuit
        operator = Operator(circuit)
        return operator.data
    
    @staticmethod
    def _get_single_qubit_gate(gate_name: str) -> np.ndarray:
        """Get matrix for single qubit gates"""
        if gate_name == 'I':
            return np.eye(2, dtype=complex)
        elif gate_name == 'X':
            return np.array([[0, 1], [1, 0]], dtype=complex)
        elif gate_name == 'Z':
            return np.array([[1, 0], [0, -1]], dtype=complex)
        elif gate_name == 'H':
            return np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
        elif gate_name == 'CNOT':
            # CNOT acts as Identity in single qubit context
            return np.eye(2, dtype=complex)
        else:
            raise ValueError(f"Unknown gate: {gate_name}")


# Compatibility aliases for the old interface
CircuitSimulator = QiskitCircuitSimulator
QuantumState = QiskitQuantumState 