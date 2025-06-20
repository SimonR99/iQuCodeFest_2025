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
                "num_missions": 15,
                "allow_double_target": True,
                "allow_triple_target": True,
                "points_per_step": 2,
                "base_points": 5
            }
        num_missions = mission_cfg.get("num_missions", 15)
        allow_double = mission_cfg.get("allow_double_target", True)
        allow_triple = mission_cfg.get("allow_triple_target", True)
        points_per_step = mission_cfg.get("points_per_step", 2)
        base_points = mission_cfg.get("base_points", 5)

        cities = list(self.universities.keys())
        self.mission_deck = []
        attempts = 0
        max_attempts = num_missions * 20  # Increased for quantum feasibility checking
        used_pairs = set()
        
        # Define quantum state pools for different complexities
        single_qubit_states = {
            'computational': ["|0⟩", "|1⟩"],
            'superposition': ["|+⟩", "|-⟩"]
        }
        
        two_qubit_states = {
            'computational': ["|00⟩", "|01⟩", "|10⟩", "|11⟩"],
            'entangled': ["|Bell+⟩", "|Bell-⟩", "|Ψ+⟩", "|Ψ-⟩"]
        }
        
        three_qubit_states = {
            'computational': ["|000⟩", "|001⟩", "|010⟩", "|011⟩", "|100⟩", "|101⟩", "|110⟩", "|111⟩"],
            'multipartite': ["|GHZ⟩", "|W⟩"]
        }
        
        while len(self.mission_deck) < num_missions and attempts < max_attempts:
            attempts += 1
            
            # Special case: Add a guaranteed Bell state mission if we haven't added one yet
            if len(self.mission_deck) == 0:
                # Add the Bell state mission as the first mission
                bell_start_cities = ["Princeton", "GeorgiaTech"]
                bell_target = "U Chicago"
                bell_init_state = "|00⟩"
                bell_target_state = "|00⟩ + |11⟩"
                bell_points = 50
                bell_difficulty = "hard"
                
                try:
                    bell_mission = MissionCard(bell_start_cities, bell_target, bell_init_state, bell_target_state, bell_points, bell_difficulty)
                    self.mission_deck.append(bell_mission)
                    used_pairs.add((tuple(sorted(bell_start_cities)), bell_target, 2))
                    print(f"Generated Bell state mission: {bell_mission}")
                    print(f"  Bell state circuit: Princeton (H) → Carnegie → U Chicago (CNOT)")
                    print(f"  GeorgiaTech (I) → Carnegie → U Chicago (CNOT)")
                    continue
                except ValueError as e:
                    print(f"Failed to create Bell state mission: {e}")
                    continue
            
            # Choose mission complexity (number of qubits)
            complexity_weights = [0.6, 0.3, 0.1]  # 60% single, 30% double, 10% triple
            num_qubits = random.choices([1, 2, 3], weights=complexity_weights)[0]
            
            # Ensure we allow the chosen complexity
            if num_qubits == 2 and not allow_double:
                num_qubits = 1
            elif num_qubits == 3 and not allow_triple:
                num_qubits = min(2 if allow_double else 1, num_qubits)
            
            # Number of start cities must match quantum complexity
            n_start = num_qubits
            
            # Pick unique start cities
            if len(cities) < n_start + 1:  # Need at least n_start + 1 cities (for target)
                continue
            start_cities = random.sample(cities, n_start)
            
            # Pick a target city not in start_cities
            possible_targets = [c for c in cities if c not in start_cities]
            if not possible_targets:
                continue
            target = random.choice(possible_targets)
            
            # Avoid duplicate missions
            key = (tuple(sorted(start_cities)), target, num_qubits)
            if key in used_pairs:
                continue
            
            # Generate quantum states based on complexity
            # Always start with |0⟩ state (|0⟩, |00⟩, |000⟩)
            if num_qubits == 1:
                init_state = "|0⟩"
                # Choose state type for single qubit
                use_superposition = random.random() < 0.4  # 40% chance for superposition
                if use_superposition:
                    target_state = random.choice(single_qubit_states['superposition'])
                    difficulty = "medium"
                else:
                    target_state = random.choice(single_qubit_states['computational'])
                    difficulty = "easy"
            
            elif num_qubits == 2:
                init_state = "|00⟩"
                # Choose state type for two qubits
                use_entanglement = random.random() < 0.5  # 50% chance for entangled targets
                if use_entanglement:
                    target_state = random.choice(two_qubit_states['entangled'])
                    difficulty = "hard"
                else:
                    target_state = random.choice(two_qubit_states['computational'])
                    difficulty = "medium"
            
            else:  # num_qubits == 3
                init_state = "|000⟩"
                # Three qubit missions are always hard
                use_multipartite = random.random() < 0.6  # 60% chance for multipartite states
                if use_multipartite:
                    target_state = random.choice(three_qubit_states['multipartite'])
                else:
                    target_state = random.choice(three_qubit_states['computational'])
                difficulty = "hard"
            
            # Check if this quantum transformation is feasible with available routes
            feasible_paths = self.quantum_simulator.check_route_feasibility(
                start_cities, target, init_state, target_state, self.routes
            )
            
            if not feasible_paths:
                continue  # Skip missions that are impossible to complete
            
            # Pick a random feasible path to base the mission on
            selected_path = random.choice(feasible_paths)
            actual_start_city = selected_path['start_city']
            path_length = len(selected_path['path'])
            
            # For multi-start missions, use only the start city that has a working path
            if num_qubits > 1:
                # For multi-qubit missions, we need paths from ALL start cities to the target
                # This represents routing multiple qubits through the network
                all_paths_feasible = True
                total_path_length = 0
                
                for start_city in start_cities:
                    city_paths = [p for p in feasible_paths if p['start_city'] == start_city]
                    if not city_paths:
                        all_paths_feasible = False
                        break
                    # Use the shortest path for this city
                    shortest_path = min(city_paths, key=lambda p: len(p['path']))
                    total_path_length += len(shortest_path['path'])
                
                if not all_paths_feasible:
                    continue  # Skip missions where not all start cities have feasible paths
                
                # Use all start cities for multi-qubit missions
                mission_start_cities = start_cities
                path_length = total_path_length  # Sum of all paths
            else:
                # For single qubit missions, use the specific working start city
                mission_start_cities = [actual_start_city]
                path_length = len(selected_path['path'])
            
            # Assign points based on difficulty and actual working path length
            difficulty_multiplier = {"easy": 1.0, "medium": 1.5, "hard": 2.0}
            points = int((base_points + points_per_step * path_length) * difficulty_multiplier[difficulty])
            
            # Add mission with validated feasibility
            try:
                mission = MissionCard(mission_start_cities, target, init_state, target_state, points, difficulty)
                self.mission_deck.append(mission)
                used_pairs.add(key)
                print(f"Generated feasible mission: {mission}")
                print(f"  Working path: {actual_start_city} → {target} using gates {[gc[0] for gc in selected_path['gate_combination']]}")
            except ValueError as e:
                # Skip missions that fail validation
                print(f"Skipped invalid mission: {e}")
                continue
        
        random.shuffle(self.mission_deck)
        print(f"Generated {len(self.mission_deck)} feasible quantum missions")

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
        
    def can_claim_route(self, player: Player, route_idx: int, selected_gate: str = None, gate_index: int = None) -> bool:
        if route_idx >= len(self.routes):
            return False
            
        route = self.routes[route_idx]
        claimed_by = route.get('claimed_by', {})
        
        # Handle both old format (single claimed_by) and new format (claimed_by object)
        if not isinstance(claimed_by, dict):
            return claimed_by is None
        
        # Handle both array and single gate formats
        gates = route['gate']
        if isinstance(gates, str):
            gates = [gates]
        
        length = route['length']
        
        # If a specific gate is selected, check only that gate
        if selected_gate:
            if selected_gate not in gates:
                return False
            
            # Check if this specific gate instance is available
            if isinstance(claimed_by, dict):
                gate_claimed = claimed_by.get(selected_gate)
                if isinstance(gate_claimed, list):
                    # Multiple identical gates - check if the specific instance is available
                    if gate_index is not None and gate_index < len(gate_claimed):
                        if gate_claimed[gate_index] is not None:
                            return False
                    else:
                        # No specific index provided, check if any instance is available
                        if all(instance is not None for instance in gate_claimed):
                            return False
                else:
                    # Single gate instance
                    if gate_claimed is not None:
                        return False
            else:
                # Old format - single claimed_by value
                if claimed_by is not None:
                    return False
            
            gate_type = GateType(selected_gate)
            return player.can_claim_route(gate_type, length)
        
        # Check if player can claim at least one unclaimed gate
        for gate in gates:
            gate_claimed = claimed_by.get(gate)
            if isinstance(gate_claimed, list):
                # Multiple identical gates - check if any instance is available
                if any(instance is None for instance in gate_claimed):
                    gate_type = GateType(gate)
                    if player.can_claim_route(gate_type, length):
                        return True
            elif gate_claimed is None:  # Gate is unclaimed
                gate_type = GateType(gate)
                if player.can_claim_route(gate_type, length):
                    return True
        return False
        
    def claim_route(self, player: Player, route_idx: int, selected_gate: str = None, gate_index: int = None) -> bool:
        if not self.can_claim_route(player, route_idx, selected_gate):
            return False
            
        route = self.routes[route_idx]
        claimed_by = route.get('claimed_by', {})
        
        # Handle both array and single gate formats
        gates = route['gate']
        if isinstance(gates, str):
            gates = [gates]
        
        length = route['length']
        
        # If no specific gate is selected, find the first affordable unclaimed one
        if selected_gate is None:
            for gate in gates:
                if isinstance(claimed_by, dict) and claimed_by.get(gate) is None:
                    gate_type = GateType(gate)
                    if player.can_claim_route(gate_type, length):
                        selected_gate = gate
                        break
                elif not isinstance(claimed_by, dict) and claimed_by is None:
                    gate_type = GateType(gate)
                    if player.can_claim_route(gate_type, length):
                        selected_gate = gate
                        break
        
        if selected_gate is None or selected_gate not in gates:
            return False
        
        # If gate_index is provided, verify it's valid and corresponds to the selected gate
        if gate_index is not None:
            if gate_index >= len(gates) or gates[gate_index] != selected_gate:
                print(f"Invalid gate index {gate_index} for gate {selected_gate}")
                return False
        else:
            # If no gate_index provided, use the first occurrence of the gate
            gate_index = gates.index(selected_gate)
            
        gate_type = GateType(selected_gate)
        
        # Create unique route ID that includes the gate index for identical gates
        if gates.count(selected_gate) > 1:
            # If there are multiple identical gates, include the index to make it unique
            route_id = f"{route['from']}-{route['to']}-{selected_gate}-{gate_index}"
        else:
            # Single gate or unique gate, use the standard format
            route_id = f"{route['from']}-{route['to']}-{selected_gate}"
        
        if player.claim_route(gate_type, length, route_id):
            # Update the claimed_by structure for individual gates
            if not isinstance(claimed_by, dict):
                # Initialize new format if using old format
                route['claimed_by'] = {}
                for gate in gates:
                    route['claimed_by'][gate] = None
            
            # For routes with multiple identical gates, we need to track which specific instance was claimed
            if gates.count(selected_gate) > 1:
                # Create a list to track individual gate instances
                if not isinstance(route['claimed_by'], dict) or not isinstance(route['claimed_by'].get(selected_gate), list):
                    route['claimed_by'][selected_gate] = [None] * gates.count(selected_gate)
                
                # Mark the specific gate instance as claimed
                route['claimed_by'][selected_gate][gate_index] = player.player_id
            else:
                # Single gate, use simple assignment
                route['claimed_by'][selected_gate] = player.player_id
            
            # Add route scoring
            self.add_route_scoring(player, length)
            
            # Check for mission completion after claiming a route
            self.check_mission_completion(player)
            
            return True

        return False
        
    def check_mission_completion(self, player: Player) -> bool:
        """Check if any of the player's missions are completed"""
        any_completed = False
        
        for mission in player.missions:
            if mission.completed:
                continue  # Already completed
                
            # For multi-qubit missions, we need paths from ALL start cities to target
            # For single qubit missions, we need a path from the start city to target
            if len(mission.start_cities) > 1:
                # Multi-qubit mission: check ALL start cities
                all_paths_exist = True
                all_path_routes = []
                
                for start_city in mission.start_cities:
                    path_routes = self.get_path_routes(player, start_city, mission.target_city)
                    if not path_routes:
                        all_paths_exist = False
                        break
                    all_path_routes.append(path_routes)
                
                if not all_paths_exist:
                    continue  # Not all paths exist yet
                
                # Use the new multi-qubit simulator for proper quantum validation
                print(f"Validating multi-qubit mission: {mission}")
                print(f"  Start cities: {mission.start_cities}")
                print(f"  Target city: {mission.target_city}")
                print(f"  Initial state: {mission.initial_state}")
                print(f"  Target state: {mission.target_state}")
                
                # Get all routes claimed by the player for this mission
                player_routes_for_mission = []
                for path_routes in all_path_routes:
                    for route in path_routes:
                        if route not in player_routes_for_mission:
                            player_routes_for_mission.append(route)
                
                print(f"  Player routes: {len(player_routes_for_mission)}")
                
                # Simulate the multi-qubit quantum circuit
                success, final_state, gate_sequence = self.quantum_simulator.simulate_multi_qubit_path(
                    mission.start_cities,
                    mission.target_city,
                    mission.initial_state,
                    mission.target_state,
                    player_routes_for_mission
                )
                
                print(f"  Quantum simulation result:")
                print(f"    Success: {success}")
                print(f"    Gate sequence: {' → '.join(gate_sequence)}")
                print(f"    Final state: {final_state.get_state_description()}")
                print(f"    Final probabilities: {final_state.get_probabilities()}")
                
                if success:
                    mission.completed = True
                    player.score += mission.points
                    any_completed = True
                    print(f"🎉 {player.name} completed a multi-qubit mission worth {mission.points} points!")
                    print(f"  Mission: {mission}")
                    continue
                    
            else:
                # Single qubit mission: check the one start city
                start_city = mission.start_cities[0]
                path_routes = self.get_path_routes(player, start_city, mission.target_city)
                print(f"Checking single qubit mission: {start_city} → {mission.target_city}")
                print(f"  Found path routes: {len(path_routes)}")
                if path_routes:
                    # Simulate the quantum circuit
                    route_gates = []
                    for route in path_routes:
                        # Use the gate that was claimed with (should be set in get_path_routes)
                        gate = route.get('claimed_with_gate')
                        if gate is None:
                            print(f"Warning: No claimed_with_gate found for route {route['from']}-{route['to']}")
                            # Fallback: use first gate from array or the gate if it's a string
                            gates = route['gate']
                            if isinstance(gates, list):
                                gate = gates[0]
                            else:
                                gate = gates
                        route_gates.append((gate, route['length']))
                    
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
                claimed_by = route.get('claimed_by', {})
                # Check if player claimed any gate on this route
                player_claimed_gate = None
                if isinstance(claimed_by, dict):
                    for gate, owner in claimed_by.items():
                        if isinstance(owner, list):
                            # Multiple identical gates - check if player claimed any instance
                            for i, instance_owner in enumerate(owner):
                                if instance_owner == player.player_id:
                                    player_claimed_gate = gate
                                    break
                            if player_claimed_gate:
                                break
                        elif owner == player.player_id:
                            # Single gate instance
                            player_claimed_gate = gate
                            break
                elif claimed_by == player.player_id:
                    # Handle old format
                    player_claimed_gate = route['gate']
                
                if player_claimed_gate:
                    next_city = None
                    if route['from'] == current:
                        next_city = route['to']
                    elif route['to'] == current:
                        next_city = route['from']
                        
                    if next_city and next_city not in visited:
                        # Add the gate used to the route info for quantum simulation
                        route_copy = route.copy()
                        route_copy['claimed_with_gate'] = player_claimed_gate
                        new_path = path_routes + [route_copy]
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
            route_points = 0
            for route_id in player.claimed_routes:
                # Parse route ID to get route length
                # Format: "from-to-gate" or "from-to-gate-index"
                parts = route_id.split('-')
                if len(parts) >= 3:
                    # Find the route to get its length
                    from_city = parts[0]
                    to_city = parts[1]
                    gate = parts[2]
                    
                    # Find the route in the routes list
                    for route in self.routes:
                        if (route['from'] == from_city and route['to'] == to_city) or \
                           (route['from'] == to_city and route['to'] == from_city):
                            route_points += route['length']
                            break
            
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