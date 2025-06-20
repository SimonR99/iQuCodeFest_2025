import pygame
import sys
import os
import json
from typing import Optional, Tuple
from .map_renderer import MapRenderer
from ..game import GameState, GateType

class GameWindow:
    def __init__(self, width: int = 1400, height: int = 900):
        self.width = width
        self.height = height
        self.min_width = 1000
        self.min_height = 700
        self.screen: Optional[pygame.Surface] = None
        self.clock = pygame.time.Clock()
        self.running = False
        
        # Initialize game state and map renderer
        config_path = os.path.join(os.path.dirname(__file__), '../../..', 'config', 'university_map.json')
        self.map_renderer = MapRenderer(config_path)
        self.game_state = GameState(config_path)
        
        # Selected route for highlighting
        self.selected_route_idx = None
        self.selected_university = None
        self.hovered_route_idx = None
        
        # Available cards for drawing (like Ticket to Ride online)
        self.available_cards = []
        
        # Background image
        self.background_image = None
        self.load_background_image()
        
        # Card drawing state
        self.cards_drawn_this_turn = 0
        self.max_cards_per_turn = 2
        
        # Load colors from configuration
        self.colors = self.load_colors()
        self.BACKGROUND_COLOR = tuple(self.colors['ui_colors']['background']['rgb'])
        self.MAP_COLOR = tuple(self.colors['ui_colors']['map_area']['rgb'])  
        self.CARD_AREA_COLOR = tuple(self.colors['ui_colors']['card_area']['rgb'])
        self.INFO_PANEL_COLOR = tuple(self.colors['ui_colors']['info_panel']['rgb'])
        self.BORDER_COLOR = tuple(self.colors['ui_colors']['border']['rgb'])
        self.TEXT_COLOR = tuple(self.colors['ui_colors']['text']['rgb'])
        self.ACCENT_COLOR = tuple(self.colors['ui_colors']['accent']['rgb'])
        
        # UI Layout - will be updated dynamically
        self.update_layout()
    
    def update_layout(self) -> None:
        # Layout like real Ticket to Ride
        # Left sidebar for player info and scores
        sidebar_width = 250
        
        # Right panel for available cards (like real Ticket to Ride)
        right_panel_width = 200
        
        # Bottom area for player hand (increased size)
        hand_area_height = 160
        
        # Calculate main map area
        map_x = sidebar_width + 10
        map_y = 10
        map_width = self.width - sidebar_width - right_panel_width - 30
        map_height = self.height - hand_area_height - 30
        
        # Define all UI rectangles
        self.sidebar_rect = pygame.Rect(10, 10, sidebar_width, self.height - 20)
        self.map_rect = pygame.Rect(map_x, map_y, map_width, map_height)
        
        # Right panel for available cards
        right_panel_x = map_x + map_width + 10
        self.available_cards_rect = pygame.Rect(right_panel_x, 10, right_panel_width, self.height - 20)
        
        # Bottom area for player hand (aligned with map)
        hand_y = map_y + map_height + 10
        self.hand_area_rect = pygame.Rect(map_x, hand_y, map_width, hand_area_height)
        
    def initialize(self) -> bool:
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("Ket-to-Ride")
        
        # Initialize font (increased sizes for better readability)
        pygame.font.init()
        self.font = pygame.font.Font(None, 28)
        self.title_font = pygame.font.Font(None, 42)
        self.small_font = pygame.font.Font(None, 22)
        self.large_font = pygame.font.Font(None, 32)
        
        # Initialize game with players
        self.setup_game()
        
        # Setup available cards after game state is ready
        self.setup_available_cards()
        
        return True
        
    def load_background_image(self):
        """Load the map background image"""
        try:
            # Try to load the map image
            image_path = os.path.join("assets", "map.jpg")
            if os.path.exists(image_path):
                self.background_image = pygame.image.load(image_path)
                print(f"Loaded background image: {image_path}")
            else:
                print(f"Background image not found: {image_path}")
                self.background_image = None
        except Exception as e:
            print(f"Error loading background image: {e}")
            self.background_image = None
    
    def load_colors(self):
        """Load colors from configuration file"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), '../../..', 'config', 'colors.json')
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading colors: {e}")
            # Fallback colors
            return {
                'gate_colors': {
                    'I': {'rgb': [240, 235, 220]},
                    'X': {'rgb': [200, 120, 100]},
                    'Y': {'rgb': [140, 160, 120]},
                    'Z': {'rgb': [120, 140, 160]},
                    'H': {'rgb': [190, 170, 130]},
                    'CNOT': {'rgb': [160, 120, 140]}
                },
                'ui_colors': {
                    'background': {'rgb': [45, 52, 48]},
                    'map_area': {'rgb': [85, 95, 82]},
                    'card_area': {'rgb': [68, 75, 65]},
                    'info_panel': {'rgb': [58, 65, 55]},
                    'border': {'rgb': [120, 110, 95]},
                    'text': {'rgb': [250, 248, 240]},
                    'accent': {'rgb': [160, 140, 110]}
                }
            }
        
    def setup_game(self):
        # Add default players
        player_colors = [
            (255, 100, 100),  # Red
            (100, 100, 255),  # Blue
            (100, 255, 100),  # Green
            (255, 255, 100),  # Yellow
        ]
        
        player_names = ["Alice", "Bob", "Charlie", "Diana"]
        
        for i, (name, color) in enumerate(zip(player_names[:2], player_colors[:2])):
            self.game_state.add_player(name, color)
            
    def setup_available_cards(self):
        # Set up 5 visible cards for drawing (like Ticket to Ride online)
        self.available_cards = []
        for _ in range(5):
            if self.game_state.deck:
                card = self.game_state.deck.pop()
                self.available_cards.append(card)
        
        # Add deck option
        self.available_cards.append("DECK")  # Special marker for drawing from deck
    
    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_d:  # Draw cards
                    self.handle_draw_cards()
                elif event.key == pygame.K_SPACE:  # Next turn
                    self.end_turn()
                elif event.key == pygame.K_c:  # Claim selected route
                    self.handle_claim_route()
                elif event.key == pygame.K_r:  # Cycle through routes
                    self.cycle_route_selection()
            elif event.type == pygame.VIDEORESIZE:
                self.width = max(event.w, self.min_width)
                self.height = max(event.h, self.min_height)
                self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                self.update_layout()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.handle_mouse_click(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                self.handle_mouse_motion(event.pos)
                    
    def handle_draw_cards(self):
        current_player = self.game_state.get_current_player()
        if current_player and not self.game_state.game_over:
            if self.cards_drawn_this_turn >= self.max_cards_per_turn:
                print("Already drew maximum cards this turn!")
                return
                
            cards_to_draw = min(2 - self.cards_drawn_this_turn, 2)
            cards = self.game_state.draw_cards(cards_to_draw)
            for card in cards:
                current_player.add_cards(card)
            self.cards_drawn_this_turn += cards_to_draw
            
            if self.cards_drawn_this_turn >= self.max_cards_per_turn:
                self.end_turn()
            
    def handle_mouse_motion(self, pos: Tuple[int, int]):
        # Update hovered route for highlighting
        if self.map_rect.collidepoint(pos):
            route_idx = self.map_renderer.get_route_at_position(self.map_rect, pos)
            self.hovered_route_idx = route_idx
        else:
            self.hovered_route_idx = None
            
    def handle_mouse_click(self, pos: Tuple[int, int]):
        # Handle clicking on available cards
        if self.available_cards_rect.collidepoint(pos):
            card_idx = self.get_clicked_available_card(pos)
            if card_idx is not None:
                self.draw_specific_card(card_idx)
                return
        
        # Handle clicking on routes
        if self.map_rect.collidepoint(pos):
            # Check if clicking on a route
            route_idx = self.map_renderer.get_route_at_position(self.map_rect, pos)
            if route_idx is not None:
                route = self.game_state.routes[route_idx]
                if route.get('claimed_by') is None:  # Only select unclaimed routes
                    self.selected_route_idx = route_idx
                    print(f"Selected route: {route['from']} -> {route['to']} ({route['gate']}, {route['length']})")
                return
            
            # Check if clicking on a university
            uni_id = self.map_renderer.get_university_at_position(self.map_rect, pos)
            if uni_id:
                self.selected_university = uni_id
                print(f"Selected university: {uni_id}")
                
        # Handle clicking on selected route to claim it
        if self.selected_route_idx is not None:
            self.handle_claim_route()
            
    def get_clicked_available_card(self, pos: Tuple[int, int]) -> Optional[int]:
        """Determine which available card was clicked (vertical layout)"""
        if not self.available_cards:
            return None
            
        card_height = 60
        card_spacing = 10
        start_x = self.available_cards_rect.x + 10
        start_y = self.available_cards_rect.y + 60
        
        relative_x = pos[0] - start_x
        relative_y = pos[1] - start_y
        
        # Check if within card area horizontally
        card_width = self.available_cards_rect.width - 20
        if relative_x < 0 or relative_x > card_width:
            return None
            
        # Calculate which card was clicked
        for i in range(len(self.available_cards)):
            card_top = i * (card_height + card_spacing)
            card_bottom = card_top + card_height
            
            # Skip if card would be outside the panel
            if start_y + card_bottom > self.available_cards_rect.bottom - 10:
                break
            
            if card_top <= relative_y <= card_bottom:
                return i
                
        return None
        
    def draw_specific_card(self, card_idx: int):
        """Draw a specific card from the available cards (Ticket to Ride rules)"""
        if card_idx >= len(self.available_cards):
            return
            
        current_player = self.game_state.get_current_player()
        if not current_player or self.game_state.game_over:
            return
            
        # Check if player can still draw cards this turn
        if self.cards_drawn_this_turn >= self.max_cards_per_turn:
            print("Already drew maximum cards this turn!")
            return
            
        selected_card = self.available_cards[card_idx]
        
        if selected_card == "DECK":
            # Draw from deck (can draw 2 cards)
            cards_to_draw = min(2 - self.cards_drawn_this_turn, 2)
            cards = self.game_state.draw_cards(cards_to_draw)
            for card in cards:
                current_player.add_cards(card)
            self.cards_drawn_this_turn += cards_to_draw
            print(f"Drew {cards_to_draw} cards from deck")
        else:
            # Take specific visible card (counts as 1 card)
            current_player.add_cards(selected_card)
            self.cards_drawn_this_turn += 1
            
            # Replace with new card from deck
            if self.game_state.deck:
                new_card = self.game_state.deck.pop()
                self.available_cards[card_idx] = new_card
            else:
                # Remove card if deck is empty
                self.available_cards.pop(card_idx)
                
            print(f"Drew card: {selected_card}")
            
        # Check if turn should end
        if self.cards_drawn_this_turn >= self.max_cards_per_turn:
            self.end_turn()
            
    def end_turn(self):
        """End the current player's turn"""
        self.cards_drawn_this_turn = 0
        self.selected_route_idx = None  # Clear selection
        self.game_state.next_turn()
        print(f"Turn ended. Now {self.game_state.get_current_player().name}'s turn")
            
    def cycle_route_selection(self):
        if not self.game_state.routes:
            return
            
        if self.selected_route_idx is None:
            self.selected_route_idx = 0
        else:
            self.selected_route_idx = (self.selected_route_idx + 1) % len(self.game_state.routes)
            
        # Skip already claimed routes
        attempts = 0
        while (attempts < len(self.game_state.routes) and 
               self.game_state.routes[self.selected_route_idx].get('claimed_by') is not None):
            self.selected_route_idx = (self.selected_route_idx + 1) % len(self.game_state.routes)
            attempts += 1
            
        print(f"Selected route {self.selected_route_idx}: {self.game_state.routes[self.selected_route_idx]}")
            
    def handle_claim_route(self):
        if self.selected_route_idx is None:
            print("No route selected!")
            return
            
        current_player = self.game_state.get_current_player()
        if not current_player:
            return
            
        # Can't claim route if already drew cards this turn
        if self.cards_drawn_this_turn > 0:
            print("Cannot claim route after drawing cards!")
            return
            
        if self.game_state.claim_route(current_player, self.selected_route_idx):
            print(f"Route claimed successfully by {current_player.name}!")
            
            # Check for mission completion
            if self.game_state.check_mission_completion(current_player):
                print(f"🎉 {current_player.name} has completed their mission and won!")
                
            self.end_turn()  # End turn after claiming route
        else:
            route = self.game_state.routes[self.selected_route_idx]
            print(f"Cannot claim route! Need {route['length']} {route['gate']} cards")
    
    def draw_map_area(self) -> None:
        # Draw background image in map area if available
        if self.background_image:
            # Scale and crop background image to fit map area
            scaled_bg = pygame.transform.scale(self.background_image, 
                                             (self.map_rect.width, self.map_rect.height))
            self.screen.blit(scaled_bg, self.map_rect.topleft)
            
            # Add subtle overlay to make routes visible
            overlay = pygame.Surface((self.map_rect.width, self.map_rect.height))
            overlay.set_alpha(60)  # Light overlay
            overlay.fill(self.MAP_COLOR)
            self.screen.blit(overlay, self.map_rect.topleft)
        else:
            # Fallback to solid color
            pygame.draw.rect(self.screen, self.MAP_COLOR, self.map_rect)
        
        # Draw border
        pygame.draw.rect(self.screen, self.BORDER_COLOR, self.map_rect, 3)
        
        # Use map renderer to draw the university map with highlighting
        # Show selected route or hovered route
        highlight_route = self.selected_route_idx if self.selected_route_idx is not None else self.hovered_route_idx
        self.map_renderer.draw_map(self.screen, self.map_rect, highlight_route)
    
    def draw_available_cards(self) -> None:
        # Draw available cards area (right panel like Ticket to Ride)
        pygame.draw.rect(self.screen, self.CARD_AREA_COLOR, self.available_cards_rect)
        pygame.draw.rect(self.screen, self.BORDER_COLOR, self.available_cards_rect, 3)
        
        # Add header accent
        header_rect = pygame.Rect(self.available_cards_rect.x + 3, self.available_cards_rect.y + 3,
                                 self.available_cards_rect.width - 6, 40)
        pygame.draw.rect(self.screen, self.ACCENT_COLOR, header_rect)
        
        # Draw title (centered and properly sized)
        title_text = self.font.render("Available Cards", True, self.TEXT_COLOR)
        title_rect = title_text.get_rect(center=(header_rect.centerx, header_rect.centery - 5))
        self.screen.blit(title_text, title_rect)
        
        # Draw card drawing info
        current_player = self.game_state.get_current_player()
        if current_player:
            info_text = f"Cards drawn: {self.cards_drawn_this_turn}/{self.max_cards_per_turn}"
            info_surface = self.small_font.render(info_text, True, self.TEXT_COLOR)
            self.screen.blit(info_surface, (self.available_cards_rect.x + 10, self.available_cards_rect.y + 35))
        
        # Draw available cards vertically
        card_width = self.available_cards_rect.width - 20
        card_height = 60
        card_spacing = 10
        
        gate_colors = {
            GateType.I: tuple(self.colors['gate_colors']['I']['rgb']),
            GateType.X: tuple(self.colors['gate_colors']['X']['rgb']),
            GateType.Y: tuple(self.colors['gate_colors']['Y']['rgb']),
            GateType.Z: tuple(self.colors['gate_colors']['Z']['rgb']),
            GateType.H: tuple(self.colors['gate_colors']['H']['rgb']),
            GateType.CNOT: tuple(self.colors['gate_colors']['CNOT']['rgb']),
            "DECK": (100, 100, 100)
        }
        
        start_x = self.available_cards_rect.x + 10
        start_y = self.available_cards_rect.y + 60
        
        for i, card in enumerate(self.available_cards):
            y = start_y + i * (card_height + card_spacing)
            card_rect = pygame.Rect(start_x, y, card_width, card_height)
            
            # Skip if card would be outside the panel
            if y + card_height > self.available_cards_rect.bottom - 10:
                break
            
            # Get card color
            if card == "DECK":
                color = gate_colors["DECK"]
                text = "DECK"
                subtext = "Draw 2 random"
            else:
                color = gate_colors.get(card, (150, 150, 150))
                text = card.value if hasattr(card, 'value') else str(card)
                subtext = "Take this card"
            
            # Check if card can be drawn
            can_draw = self.cards_drawn_this_turn < self.max_cards_per_turn
            if not can_draw:
                color = tuple(c // 2 for c in color)  # Darken if can't draw
            
            # Draw card
            pygame.draw.rect(self.screen, color, card_rect)
            border_color = (255, 255, 255) if can_draw else (128, 128, 128)
            pygame.draw.rect(self.screen, border_color, card_rect, 2)
            
            # Draw card text
            text_color = (0, 0, 0) if can_draw else (64, 64, 64)
            card_text = self.large_font.render(text, True, text_color)
            text_rect = card_text.get_rect(center=(card_rect.centerx, card_rect.centery - 12))
            self.screen.blit(card_text, text_rect)
            
            # Draw subtext
            sub_surface = self.font.render(subtext, True, text_color)
            sub_rect = sub_surface.get_rect(center=(card_rect.centerx, card_rect.centery + 18))
            self.screen.blit(sub_surface, sub_rect)
            
    def draw_hand_area(self) -> None:
        # Draw player hand area
        pygame.draw.rect(self.screen, self.CARD_AREA_COLOR, self.hand_area_rect)
        pygame.draw.rect(self.screen, self.BORDER_COLOR, self.hand_area_rect, 3)
        
        # Add header accent
        header_rect = pygame.Rect(self.hand_area_rect.x + 3, self.hand_area_rect.y + 3,
                                 self.hand_area_rect.width - 6, 35)
        pygame.draw.rect(self.screen, self.ACCENT_COLOR, header_rect)
        
        current_player = self.game_state.get_current_player()
        if not current_player:
            return
            
        # Draw title (centered and properly sized)
        title = f"{current_player.name}'s Hand"
        title_text = self.font.render(title, True, self.TEXT_COLOR)
        title_rect = title_text.get_rect(center=(header_rect.centerx, header_rect.centery))
        self.screen.blit(title_text, title_rect)
        
        # Draw gate cards as colored rectangles (improved layout)
        card_width = 90
        card_height = 60
        card_spacing = 12
        start_x = self.hand_area_rect.x + 20
        start_y = self.hand_area_rect.y + 50
        
        gate_colors = {
            GateType.I: tuple(self.colors['gate_colors']['I']['rgb']),
            GateType.X: tuple(self.colors['gate_colors']['X']['rgb']),
            GateType.Y: tuple(self.colors['gate_colors']['Y']['rgb']),
            GateType.Z: tuple(self.colors['gate_colors']['Z']['rgb']),
            GateType.H: tuple(self.colors['gate_colors']['H']['rgb']),
            GateType.CNOT: tuple(self.colors['gate_colors']['CNOT']['rgb'])
        }
        
        x_offset = 0
        for gate_type, count in current_player.hand.items():
            if count > 0:
                color = gate_colors.get(gate_type, (150, 150, 150))
                card_rect = pygame.Rect(start_x + x_offset, start_y, card_width, card_height)
                
                # Draw card shadow
                shadow_rect = pygame.Rect(card_rect.x + 2, card_rect.y + 2, card_rect.width, card_rect.height)
                pygame.draw.rect(self.screen, (0, 0, 0, 80), shadow_rect)
                
                # Draw card background
                pygame.draw.rect(self.screen, color, card_rect)
                pygame.draw.rect(self.screen, (255, 255, 255), card_rect, 3)
                
                # Draw gate type and count
                gate_text = self.font.render(gate_type.value, True, (0, 0, 0))
                count_text = self.font.render(f"x{count}", True, (0, 0, 0))
                
                gate_rect = gate_text.get_rect(center=(card_rect.centerx, card_rect.centery - 8))
                count_rect = count_text.get_rect(center=(card_rect.centerx, card_rect.centery + 8))
                
                self.screen.blit(gate_text, gate_rect)
                self.screen.blit(count_text, count_rect)
                
                x_offset += card_width + card_spacing
    
    def draw_sidebar(self) -> None:
        # Draw left sidebar with player info and game status
        pygame.draw.rect(self.screen, self.INFO_PANEL_COLOR, self.sidebar_rect)
        pygame.draw.rect(self.screen, self.BORDER_COLOR, self.sidebar_rect, 3)
        
        # Add title background
        title_rect_bg = pygame.Rect(self.sidebar_rect.x + 3, self.sidebar_rect.y + 3, 
                                   self.sidebar_rect.width - 6, 50)
        pygame.draw.rect(self.screen, self.ACCENT_COLOR, title_rect_bg)
        
        # Draw title (centered and properly sized)
        title_text = self.large_font.render("|ket> to ride", True, self.TEXT_COLOR)
        title_rect = title_text.get_rect(center=(title_rect_bg.centerx, title_rect_bg.centery))
        self.screen.blit(title_text, title_rect)
        
        current_player = self.game_state.get_current_player()
        if not current_player:
            return
        
        # Prepare info lines with current game state
        info_lines = [
            f"Turn: {self.game_state.turn_number}",
            f"Cards in Deck: {len(self.game_state.deck)}",
            "",
        ]
        
        # Current player info
        info_lines.extend([
            f"Current Player:",
            f"➤ {current_player.name}",
            f"Cards: {current_player.get_total_cards()}",
            f"Routes: {len(current_player.claimed_routes)}",
            "",
        ])
        
        # Mission info
        if current_player.mission:
            mission = current_player.mission
            info_lines.extend([
                "Mission:",
                f"{mission.start_city} {mission.initial_state}",
                f"→ {mission.target_city} {mission.target_state}",
                f"Points: {mission.points}",
                "✓ Completed!" if mission.completed else "In Progress",
                "",
            ])
        
        # Turn actions
        info_lines.extend([
            "Turn Actions:",
            f"Cards drawn: {self.cards_drawn_this_turn}/{self.max_cards_per_turn}",
            "",
            "You can either:",
            "• Draw cards (2 max)",
            "• Claim one route",
            "",
            "Controls:",
            "• Click cards to draw",
            "• Click routes to select",
            "• SPACE - End Turn",
            "• ESC - Exit",
            "",
        ])
        
        if self.game_state.game_over:
            info_lines.extend([
                "🎉 GAME OVER! 🎉",
                f"Winner: {self.game_state.winner.name}" if self.game_state.winner else "No Winner",
                "",
            ])
        
        # Draw all players' status
        info_lines.extend([
            "Players:"
        ])
        
        for i, player in enumerate(self.game_state.players):
            marker = "➤ " if player == current_player else "  "
            info_lines.append(f"{marker}{player.name}")
            info_lines.append(f"  {player.get_total_cards()} cards, {len(player.claimed_routes)} routes")
        
        # Selected route info
        if self.selected_route_idx is not None:
            route = self.game_state.routes[self.selected_route_idx]
            info_lines.extend([
                "",
                "Selected Route:",
                f"{route['from']} → {route['to']}",
                f"Gate: {route['gate']} (x{route['length']})",
                f"Need: {route['length']} {route['gate']} cards",
            ])
        
        y_offset = 65
        for line in info_lines:
            if line:
                # Color current player name differently
                color = current_player.color if line.startswith("➤") else self.TEXT_COLOR
                text = self.font.render(line, True, color)
                self.screen.blit(text, (self.sidebar_rect.x + 15, self.sidebar_rect.y + y_offset))
            y_offset += 22
    
    def draw(self) -> None:
        self.screen.fill(self.BACKGROUND_COLOR)
        
        self.draw_sidebar()
        self.draw_map_area()
        self.draw_available_cards()
        self.draw_hand_area()
        
        pygame.display.flip()
    
    def run(self) -> None:
        if not self.initialize():
            return
        
        self.running = True
        
        while self.running:
            self.handle_events()
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

def main():
    game_window = GameWindow()
    game_window.run()

if __name__ == "__main__":
    main()
