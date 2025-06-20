import random
import json
from typing import Dict, List, Optional, Tuple
from .player import Player, GateType, MissionCard
from ..quantum import CircuitSimulator
import os

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
            GateType.Z: 12,
            GateType.H: 12,
            GateType.CNOT: 8  # Fewer CNOT cards as they're more powerful
        }
        
        self.deck = []
        for gate_type, count in gate_counts.items():
            self.deck.extend([gate_type] * count)
            
        random.shuffle(self.deck)
        
    def initialize_missions(self):
        # Load mission generation config
        config_path = os.path.join(os.path.dirname(__file__), '../../..', 'config', 'missions_config.json')
        try:
            with open(config_path, 'r') as f:
                mission_cfg = json.load(f)
        except Exception as e:
            print(f"Error loading missions config: {e}")
            mission_cfg = {
                "num_missions": 10,
                "allow_double_target": True,
                "allow_triple_target": True,
                "points_per_step": 2,
                "base_points": 5
            }
        num_missions = mission_cfg.get("num_missions", 10)
        allow_double = mission_cfg.get("allow_double_target", True)
        allow_triple = mission_cfg.get("allow_triple_target", True)
        points_per_step = mission_cfg.get("points_per_step", 2)
        base_points = mission_cfg.get("base_points", 5)

        cities = list(self.universities.keys())
        self.mission_deck = []
        attempts = 0
        max_attempts = num_missions * 10
        used_pairs = set()
        state_choices = ["|0⟩", "|1⟩"]
        while len(self.mission_deck) < num_missions and attempts < max_attempts:
            attempts += 1
            # Decide number of start cities
            n_start = 1
            if allow_triple and random.random() < 0.2:
                n_start = 3
            elif allow_double and random.random() < 0.3:
                n_start = 2
            # Pick unique start cities
            start_cities = random.sample(cities, n_start)
            # Pick a target city not in start_cities
            possible_targets = [c for c in cities if c not in start_cities]
            if not possible_targets:
                continue
            target = random.choice(possible_targets)
            # Avoid duplicate missions
            key = (tuple(sorted(start_cities)), target)
            if key in used_pairs:
                continue
            # Find shortest path from any start to target
            min_path_len = None
            for start in start_cities:
                path_len = self._shortest_path_length(start, target)
                if path_len is not None:
                    if min_path_len is None or path_len < min_path_len:
                        min_path_len = path_len
            if min_path_len is None:
                continue  # No path exists
            # Assign points
            points = base_points + points_per_step * min_path_len
            # Randomly pick initial and target quantum state
            init_state = random.choice(state_choices)
            target_state = random.choice(state_choices)
            # Add mission
            self.mission_deck.append(MissionCard(start_cities, target, init_state, target_state, points))
            used_pairs.add(key)
        random.shuffle(self.mission_deck)

    def _shortest_path_length(self, start: str, target: str) -> Optional[int]:
        # BFS for shortest path (by number of routes)
        if start == target:
            return 0
        visited = set()
        queue = [(start, 0)]
        while queue:
            current, dist = queue.pop(0)
            if current == target:
                return dist
            if current in visited:
                continue
            visited.add(current)
            for route in self.routes:
                next_city = None
                if route['from'] == current:
                    next_city = route['to']
                elif route['to'] == current:
                    next_city = route['from']
                if next_city and next_city not in visited:
                    queue.append((next_city, dist + 1))
        return None
        
    def add_player(self, name: str, color: Tuple[int, int, int]) -> Player:
        player_id = f"player_{len(self.players) + 1}"
        player = Player(player_id, name, color)
        self.players.append(player)
        
        # Deal initial cards (5 cards)
        for _ in range(5):
            if self.deck:
                card = self.deck.pop()
                player.add_cards(card)
                
        # Don't automatically assign mission - let player draw missions later
        
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
            # Add route scoring
            self.add_route_scoring(player, length)
            return True
            
        return False
        
    def check_mission_completion(self, player: Player) -> bool:
        """Check if any of the player's missions are completed"""
        any_completed = False
        
        for mission in player.missions:
            if mission.completed:
                continue  # Already completed
                
            # Check if player has a path from any start city to target
            for start_city in mission.start_cities:
                path_routes = self.get_path_routes(player, start_city, mission.target_city)
                if path_routes:
                    # Simulate the quantum circuit
                    route_gates = [(route['gate'], route['length']) for route in path_routes]
                    success, final_state, gate_sequence = self.quantum_simulator.simulate_path(
                        mission.initial_state,
                        route_gates,
                        mission.target_state
                    )
                    
                    print(f"Quantum simulation for {player.name}:")
                    print(f"  Path: {start_city} → {mission.target_city}")
                    print(f"  Gate sequence: {' → '.join(gate_sequence)}")
                    print(f"  Initial: {mission.initial_state}, Target: {mission.target_state}")
                    print(f"  Final probabilities: {final_state.get_probabilities()}")
                    print(f"  Success: {success}")
                    
                    if success:
                        mission.completed = True
                        player.score += mission.points
                        any_completed = True
                        print(f"🎉 {player.name} completed a mission worth {mission.points} points!")
                        break  # Break out of start_cities loop for this mission
                        
        # Check if player has completed all their missions (win condition)
        if player.missions and all(mission.completed for mission in player.missions):
            player.has_won = True
            self.winner = player
            self.game_over = True
            print(f"🎉 {player.name} has completed ALL missions and won the game!")
            return True
            
        return any_completed
        
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
            # Check for game end conditions before switching turns
            self.check_game_end_conditions()
            
            if not self.game_over:
                self.current_player_index = (self.current_player_index + 1) % len(self.players)
                if self.current_player_index == 0:
                    self.turn_number += 1
    
    def check_game_end_conditions(self):
        """Check various game end conditions like Ticket to Ride"""
        current_player = self.get_current_player()
        if not current_player:
            return
            
        # 1. Mission completion (primary win condition) - handled in check_mission_completion
            
        # 2. Player has very few cards left (triggers last round)
        if current_player.get_total_cards() <= 2:
            print(f"Last round triggered! {current_player.name} has only {current_player.get_total_cards()} cards left.")
            # TODO: Implement last round logic
            
        # 3. Deck runs out
        if len(self.deck) == 0 and len(self.discard_pile) == 0:
            print("Game ends - no more cards!")
            self.end_game_by_points()
            
        # 4. Player claims 6+ routes (like Ticket to Ride's train pieces)
        if len(current_player.claimed_routes) >= 6:
            print(f"Game ends - {current_player.name} claimed 6+ routes!")
            self.end_game_by_points()
    
    def end_game_by_points(self):
        """End game and determine winner by points"""
        self.game_over = True
        
        # Calculate final scores
        for player in self.players:
            # Points from routes (1 point per route segment)
            route_points = sum(len(route.split('-')) for route in player.claimed_routes)
            
            # Mission points
            mission_points = 0
            for mission in player.missions:
                if mission.completed:
                    mission_points += mission.points
                else:
                    # Penalty for incomplete mission
                    mission_points -= mission.points // 2
                
            player.score = route_points + mission_points
            print(f"{player.name}: {route_points} route points + {mission_points} mission points = {player.score} total")
            
        # Find winner by highest score
        winner = max(self.players, key=lambda p: p.score)
        self.winner = winner
        winner.has_won = True
        print(f"Winner: {winner.name} with {winner.score} points!")
    
    def add_route_scoring(self, player: Player, route_length: int):
        """Add points for claiming a route"""
        # Route scoring like Ticket to Ride: 1=1pt, 2=2pts, 3=4pts, 4=7pts, 5=10pts, 6=15pts
        route_points = {1: 1, 2: 2, 3: 4, 4: 7, 5: 10, 6: 15}.get(route_length, route_length)
        player.score += route_points
                
    def get_game_info(self) -> Dict:
        current_player = self.get_current_player()
        return {
            'turn': self.turn_number,
            'current_player': current_player.name if current_player else "None",
            'game_over': self.game_over,
            'winner': self.winner.name if self.winner else None,
            'deck_size': len(self.deck),
            'mission_deck_size': len(self.mission_deck),
            'players': [
                {
                    'name': p.name,
                    'cards': dict(p.hand),
                    'routes': len(p.claimed_routes),
                    'missions': [str(mission) for mission in p.missions],
                    'completed_missions': len(p.get_completed_missions()),
                    'total_missions': len(p.missions)
                }
                for p in self.players
            ]
        }
        
    def draw_mission_cards(self, count: int = 3) -> List[MissionCard]:
        """Draw mission cards for selection (like Ticket to Ride)"""
        drawn_missions = []
        for _ in range(min(count, len(self.mission_deck))):
            if self.mission_deck:
                drawn_missions.append(self.mission_deck.pop())
        return drawn_missions
        
    def return_missions_to_deck(self, missions: List[MissionCard]):
        """Return unused mission cards to the deck and shuffle"""
        self.mission_deck.extend(missions)
        random.shuffle(self.mission_deck)
        
    def assign_missions_to_player(self, player: Player, missions: List[MissionCard]):
        """Assign selected missions to a player"""
        for mission in missions:
            player.add_mission(mission)
            
    def can_draw_missions(self, player: Player) -> bool:
        """Check if player can draw mission cards (not after drawing gate cards)"""
        # In Ticket to Ride, you can draw missions as an alternative to drawing train cards
        return len(self.mission_deck) >= 3  # Need at least 3 cards to draw