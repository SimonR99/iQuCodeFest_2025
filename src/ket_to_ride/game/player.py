from typing import Dict, List, Optional, Tuple
from enum import Enum

class GateType(Enum):
    I = "I"
    X = "X"
    Z = "Z"
    H = "H"
    CNOT = "CNOT"

class Player:
    def __init__(self, player_id: str, name: str, color: Tuple[int, int, int]):
        self.player_id = player_id
        self.name = name
        self.color = color
        
        # Gate cards in hand
        self.hand: Dict[GateType, int] = {
            GateType.I: 0,
            GateType.X: 0,
            GateType.Z: 0,
            GateType.H: 0,
            GateType.CNOT: 0
        }
        
        # Mission cards - now supporting multiple missions
        self.missions: List['MissionCard'] = []
        
        # Claimed routes
        self.claimed_routes: List[str] = []
        
        # Score tracking
        self.score = 0
        self.has_won = False
        
    def add_cards(self, gate_type: GateType, count: int = 1):
        self.hand[gate_type] += count
        
    def add_mission(self, mission: 'MissionCard'):
        """Add a mission card to the player's missions"""
        self.missions.append(mission)
        
    def remove_mission(self, mission: 'MissionCard'):
        """Remove a mission card from the player's missions"""
        if mission in self.missions:
            self.missions.remove(mission)
        
    def can_claim_route(self, gate_type: GateType, length: int) -> bool:
        return self.hand[gate_type] >= length
        
    def claim_route(self, gate_type: GateType, length: int, route_id: str) -> bool:
        if not self.can_claim_route(gate_type, length):
            return False
            
        self.hand[gate_type] -= length
        self.claimed_routes.append(route_id)
        return True
        
    def get_total_cards(self) -> int:
        return sum(self.hand.values())
        
    def get_completed_missions(self) -> List['MissionCard']:
        """Get list of completed missions"""
        return [mission for mission in self.missions if mission.completed]
        
    def get_incomplete_missions(self) -> List['MissionCard']:
        """Get list of incomplete missions"""
        return [mission for mission in self.missions if not mission.completed]
        
    def __str__(self):
        return f"Player {self.name} (Cards: {self.get_total_cards()}, Routes: {len(self.claimed_routes)}, Missions: {len(self.missions)})"

class MissionCard:
    def __init__(self, start_cities: List[str], target_city: str, 
                 initial_state: str, target_state: str, points: int = 10, difficulty: str = "easy"):
        # Support 1-3 start cities (like Ticket to Ride)
        self.start_cities = start_cities if isinstance(start_cities, list) else [start_cities]
        self.target_city = target_city
        self.initial_state = initial_state  # "|0⟩", "|00⟩", "|+⟩", "|Bell+⟩", etc.
        self.target_state = target_state    # "|0⟩", "|00⟩", "|+⟩", "|Bell+⟩", etc.
        self.points = points
        self.difficulty = difficulty  # "easy", "medium", "hard"
        self.completed = False
        
        # Determine number of qubits from states
        self.num_qubits = max(self._count_qubits(initial_state), self._count_qubits(target_state))
        
        # Validate that number of start cities matches quantum complexity
        self._validate_quantum_complexity()
    
    def _count_qubits(self, state_str: str) -> int:
        """Count number of qubits in a quantum state string"""
        state_str = state_str.strip()
        
        # Single qubit states
        if state_str in ["|0⟩", "|1⟩", "|+⟩", "|-⟩"]:
            return 1
        
        # Two qubit states
        elif state_str in ["|00⟩", "|01⟩", "|10⟩", "|11⟩", "|Bell+⟩", "|Bell-⟩", "|Φ+⟩", "|Φ-⟩", "|Ψ+⟩", "|Ψ-⟩"]:
            return 2
        
        # Three qubit states
        elif state_str in ["|000⟩", "|001⟩", "|010⟩", "|011⟩", "|100⟩", "|101⟩", "|110⟩", "|111⟩", "|GHZ⟩", "|W⟩"]:
            return 3
        
        # Default to single qubit
        else:
            return 1
    
    def _validate_quantum_complexity(self):
        """Validate that the number of start cities matches the quantum complexity"""
        required_start_cities = self.num_qubits
        
        if len(self.start_cities) < required_start_cities:
            raise ValueError(f"Mission requires {required_start_cities} start cities for {self.num_qubits}-qubit target state, but only {len(self.start_cities)} provided")
    
    def get_complexity_description(self) -> str:
        """Get a description of the mission's quantum complexity"""
        if self.num_qubits == 1:
            return "Single qubit transformation"
        elif self.num_qubits == 2:
            return "Two-qubit entanglement"
        elif self.num_qubits == 3:
            return "Three-qubit multipartite state"
        else:
            return f"{self.num_qubits}-qubit quantum state"
    
    def is_superposition_target(self) -> bool:
        """Check if the target state is a superposition"""
        superposition_states = ["|+⟩", "|-⟩", "|Bell+⟩", "|Bell-⟩", "|Φ+⟩", "|Φ-⟩", "|Ψ+⟩", "|Ψ-⟩", "|GHZ⟩", "|W⟩"]
        return self.target_state in superposition_states
        
    def __str__(self):
        start_str = " OR ".join(self.start_cities)
        complexity = f"({self.get_complexity_description()})"
        return f"({start_str}) {self.initial_state} → {self.target_city} {self.target_state} {complexity} ({self.points}pts)"