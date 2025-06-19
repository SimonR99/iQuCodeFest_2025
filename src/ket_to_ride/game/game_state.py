import random
import json
from typing import Dict, List, Optional, Tuple
from .player import Player, GateType, MissionCard
from ..quantum import CircuitSimulator

class GameState:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.universities: Dict = {}
        self.routes: List[Dict] = []
        self.map_settings: Dict = {}
        
        # Game state
        self.players: List[Player] = []
        self.current_player_index = 0
        self.turn_number = 1
        self.game_over = False
        self.winner: Optional[Player] = None
        
        # Card deck
        self.deck: List[GateType] = []
        self.discard_pile: List[GateType] = []
        
        # Mission cards
        self.mission_deck: List[MissionCard] = []
        
        # Quantum simulator
        self.quantum_simulator = CircuitSimulator()
        
        self.load_config()
        self.initialize_deck()
        self.initialize_missions()
        
    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                self.universities = config.get('universities', {})
                self.routes = config.get('routes', [])
                self.map_settings = config.get('map_settings', {})
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading config: {e}")
            
    def initialize_deck(self):
        # Create deck with appropriate distribution of gate cards
        gate_counts = {
            GateType.I: 12,
            GateType.X: 12, 
            GateType.Y: 12,
            GateType.Z: 12,
            GateType.H: 12,
            GateType.CNOT: 8  # Fewer CNOT cards as they're more powerful
        }
        
        self.deck = []
        for gate_type, count in gate_counts.items():
            self.deck.extend([gate_type] * count)
            
        random.shuffle(self.deck)
        
    def initialize_missions(self):
        # Create diverse mission cards
        cities = list(self.universities.keys())
        self.mission_deck = []
        
        # Generate varied missions
        mission_templates = [
            ("MIT", "Oxford", "|0⟩", "|1⟩", 15),
            ("Stanford", "Cambridge", "|0⟩", "|1⟩", 12),
            ("Harvard", "ETH", "|0⟩", "|1⟩", 18),
            ("Berkeley", "Princeton", "|1⟩", "|0⟩", 14),
            ("Caltech", "Chicago", "|0⟩", "|1⟩", 10),
            ("MIT", "Berkeley", "|1⟩", "|1⟩", 8),
            ("Oxford", "Stanford", "|0⟩", "|0⟩", 6),
        ]
        
        for start, target, init_state, target_state, points in mission_templates:
            if start in cities and target in cities:
                self.mission_deck.append(
                    MissionCard(start, target, init_state, target_state, points)
                )
                
        random.shuffle(self.mission_deck)
        
    def add_player(self, name: str, color: Tuple[int, int, int]) -> Player:
        player_id = f"player_{len(self.players) + 1}"
        player = Player(player_id, name, color)
        self.players.append(player)
        
        # Deal initial cards (5 cards)
        for _ in range(5):
            if self.deck:
                card = self.deck.pop()
                player.add_cards(card)
                
        # Deal mission card
        if self.mission_deck:
            player.mission = self.mission_deck.pop()
            
        return player
        
    def get_current_player(self) -> Optional[Player]:
        if not self.players:
            return None
        return self.players[self.current_player_index]
        
    def draw_cards(self, count: int = 2) -> List[GateType]:
        drawn_cards = []
        for _ in range(count):
            if not self.deck and self.discard_pile:
                # Reshuffle discard pile into deck
                self.deck = self.discard_pile.copy()
                self.discard_pile.clear()
                random.shuffle(self.deck)
                
            if self.deck:
                card = self.deck.pop()
                drawn_cards.append(card)
                
        return drawn_cards
        
    def can_claim_route(self, player: Player, route_idx: int) -> bool:
        if route_idx >= len(self.routes):
            return False
            
        route = self.routes[route_idx]
        if route.get('claimed_by') is not None:
            return False
            
        gate_type = GateType(route['gate'])
        length = route['length']
        
        return player.can_claim_route(gate_type, length)
        
    def claim_route(self, player: Player, route_idx: int) -> bool:
        if not self.can_claim_route(player, route_idx):
            return False
            
        route = self.routes[route_idx]
        gate_type = GateType(route['gate'])
        length = route['length']
        route_id = f"{route['from']}-{route['to']}-{route['gate']}"
        
        if player.claim_route(gate_type, length, route_id):
            route['claimed_by'] = player.player_id
            return True
            
        return False
        
    def check_mission_completion(self, player: Player) -> bool:
        if not player.mission or player.mission.completed:
            return False
            
        # Check if player has a path from start to target
        path_routes = self.get_path_routes(player, player.mission.start_city, player.mission.target_city)
        if path_routes:
            # Simulate the quantum circuit
            route_gates = [(route['gate'], route['length']) for route in path_routes]
            success, final_state, gate_sequence = self.quantum_simulator.simulate_path(
                player.mission.initial_state,
                route_gates,
                player.mission.target_state
            )
            
            print(f"Quantum simulation for {player.name}:")
            print(f"  Gate sequence: {' → '.join(gate_sequence)}")
            print(f"  Initial: {player.mission.initial_state}, Target: {player.mission.target_state}")
            print(f"  Final probabilities: {final_state.get_probabilities()}")
            print(f"  Success: {success}")
            
            if success:
                player.mission.completed = True
                player.has_won = True
                self.winner = player
                self.game_over = True
                return True
                
        return False
        
    def has_path(self, player: Player, start: str, target: str) -> bool:
        # Simple BFS to check if player has claimed routes forming a path
        if start == target:
            return True
            
        visited = set()
        queue = [start]
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
                
            visited.add(current)
            
            # Find routes claimed by this player from current city
            for route in self.routes:
                if route.get('claimed_by') == player.player_id:
                    next_city = None
                    if route['from'] == current:
                        next_city = route['to']
                    elif route['to'] == current:
                        next_city = route['from']
                        
                    if next_city and next_city not in visited:
                        if next_city == target:
                            return True
                        queue.append(next_city)
                        
        return False
        
    def get_path_routes(self, player: Player, start: str, target: str) -> List[Dict]:
        """Get the actual routes in a path from start to target for a player"""
        if start == target:
            return []
            
        # Use BFS to find path and return the route objects
        visited = set()
        queue = [(start, [])]  # (current_city, routes_taken)
        
        while queue:
            current, path_routes = queue.pop(0)
            if current in visited:
                continue
                
            visited.add(current)
            
            # Find routes claimed by this player from current city
            for route in self.routes:
                if route.get('claimed_by') == player.player_id:
                    next_city = None
                    if route['from'] == current:
                        next_city = route['to']
                    elif route['to'] == current:
                        next_city = route['from']
                        
                    if next_city and next_city not in visited:
                        new_path = path_routes + [route]
                        if next_city == target:
                            return new_path
                        queue.append((next_city, new_path))
                        
        return []
        
    def next_turn(self):
        if not self.game_over:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            if self.current_player_index == 0:
                self.turn_number += 1
                
    def get_game_info(self) -> Dict:
        current_player = self.get_current_player()
        return {
            'turn': self.turn_number,
            'current_player': current_player.name if current_player else "None",
            'game_over': self.game_over,
            'winner': self.winner.name if self.winner else None,
            'deck_size': len(self.deck),
            'players': [
                {
                    'name': p.name,
                    'cards': dict(p.hand),
                    'routes': len(p.claimed_routes),
                    'mission': str(p.mission) if p.mission else "None"
                }
                for p in self.players
            ]
        }