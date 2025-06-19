from typing import Dict, List, Optional, Tuple
from enum import Enum

class GateType(Enum):
    I = "I"
    X = "X"
    Y = "Y"
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
            GateType.Y: 0,
            GateType.Z: 0,
            GateType.H: 0,
            GateType.CNOT: 0
        }
        
        # Mission card
        self.mission: Optional['MissionCard'] = None
        
        # Claimed routes
        self.claimed_routes: List[str] = []
        
        # Score tracking
        self.score = 0
        self.has_won = False
        
    def add_cards(self, gate_type: GateType, count: int = 1):
        self.hand[gate_type] += count
        
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
        
    def __str__(self):
        return f"Player {self.name} (Cards: {self.get_total_cards()}, Routes: {len(self.claimed_routes)})"

class MissionCard:
    def __init__(self, start_city: str, target_city: str, 
                 initial_state: str, target_state: str, points: int = 10):
        self.start_city = start_city
        self.target_city = target_city
        self.initial_state = initial_state  # "|0⟩" or "|1⟩"
        self.target_state = target_state    # "|0⟩" or "|1⟩"
        self.points = points
        self.completed = False
        
    def __str__(self):
        return f"{self.start_city} {self.initial_state} → {self.target_city} {self.target_state} ({self.points}pts)"