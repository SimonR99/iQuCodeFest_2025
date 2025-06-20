import pygame
import sys
import os
import json
import math
import time
from typing import Optional, Tuple, Dict, List
from .map_renderer import MapRenderer
from ..game import GameState, GateType

class CardAnimation:
    """Handles card movement animations"""
    def __init__(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int], 
                 card_type, duration: float = 0.5, scale_effect: bool = True):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.card_type = card_type
        self.duration = duration
        self.start_time = time.time()
        self.completed = False
        self.scale_effect = scale_effect
        
    def get_current_pos(self) -> Tuple[int, int]:
        """Get the current position of the card based on animation progress"""
        elapsed = time.time() - self.start_time
        progress = min(elapsed / self.duration, 1.0)
        
        # Use smooth easing function
        ease_progress = 1 - (1 - progress) ** 3  # Ease-out cubic
        
        x = self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * ease_progress
        y = self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * ease_progress
        
        return (int(x), int(y))
        
    def get_scale(self) -> float:
        """Get the current scale factor for the card (1.0 = normal size)"""
        if not self.scale_effect:
            return 1.0
            
        elapsed = time.time() - self.start_time
        progress = min(elapsed / self.duration, 1.0)
        
        # Scale up to 1.2x at 50% progress, then back to 1.0
        if progress < 0.5:
            scale_progress = progress * 2  # 0 to 1
            return 1.0 + 0.2 * scale_progress
        else:
            scale_progress = (progress - 0.5) * 2  # 0 to 1
            return 1.2 - 0.2 * scale_progress
        
    def is_finished(self) -> bool:
        """Check if animation is complete"""
        if self.completed:
            return True
        if time.time() - self.start_time >= self.duration:
            self.completed = True
        return self.completed

class GameWindow:
    def __init__(self, width: int = 1280, height: int = 720):
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
        
        # Animation state
        self.card_animations: List[CardAnimation] = []
        self.new_card_animations: List[CardAnimation] = []  # For cards appearing in trade row
        self.deck_animation_start = None  # Track when deck animation starts
        
        # Selected route for highlighting
        self.selected_route_idx = None
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
        
        # Map gate types to colors for drawing
        self.gate_colors = {
            GateType.I: tuple(self.colors['gate_colors']['I']['rgb']),
            GateType.X: tuple(self.colors['gate_colors']['X']['rgb']),
            GateType.Z: tuple(self.colors['gate_colors']['Z']['rgb']),
            GateType.H: tuple(self.colors['gate_colors']['H']['rgb']),
            GateType.CNOT: tuple(self.colors['gate_colors']['CNOT']['rgb']),
        }
    
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
        pygame.display.set_caption("|ket> to ride")
        
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
                    'I': {'rgb': [240, 235, 220], 'image_path': None, 'border_color': [240, 235, 220]},
                    'X': {'rgb': [200, 120, 100], 'image_path': None, 'border_color': [200, 120, 100]},
                    'Y': {'rgb': [140, 160, 120], 'image_path': None, 'border_color': [140, 160, 120]},
                    'Z': {'rgb': [120, 140, 160], 'image_path': None, 'border_color': [120, 140, 160]},
                    'H': {'rgb': [190, 170, 130], 'image_path': None, 'border_color': [190, 170, 130]},
                    'CNOT': {'rgb': [160, 120, 140], 'image_path': None, 'border_color': [160, 120, 140]}
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
    
    def draw_card_with_image_support(self, surface, card_rect, gate_type, can_draw=True, text="", subtext=""):
        """Draw a card with optional image support and colored border"""
        if gate_type == "DECK":
            # Special case for deck - use config colors
            deck_config = self.colors['gate_colors'].get('DECK', {'rgb': [100, 100, 100], 'border_color': [255, 255, 255]})
            color = tuple(deck_config['rgb'])
            if not can_draw:
                color = tuple(c // 2 for c in color)
            
            # Check for deck image
            image_path = deck_config.get('image_path')
            if image_path and os.path.exists(image_path):
                try:
                    card_image = pygame.image.load(image_path)
                    scaled_image = pygame.transform.scale(card_image, (card_rect.width - 4, card_rect.height - 4))
                    image_rect = scaled_image.get_rect(center=card_rect.center)
                    surface.blit(scaled_image, image_rect)
                    border_color = tuple(deck_config.get('border_color', [255, 255, 255]))
                except Exception:
                    pygame.draw.rect(surface, color, card_rect)
                    border_color = tuple(deck_config.get('border_color', [255, 255, 255]))
            else:
                pygame.draw.rect(surface, color, card_rect)
                border_color = tuple(deck_config.get('border_color', [255, 255, 255]))
            
            if not can_draw:
                border_color = tuple(c // 2 for c in border_color)
            pygame.draw.rect(surface, border_color, card_rect, 2)
        else:
            # Get gate configuration
            gate_config = self.colors['gate_colors'].get(gate_type.value if hasattr(gate_type, 'value') else str(gate_type), {})
            
            # Check for image path
            image_path = gate_config.get('image_path')
            if image_path and os.path.exists(image_path):
                try:
                    # Load and scale image to fit card
                    card_image = pygame.image.load(image_path)
                    scaled_image = pygame.transform.scale(card_image, (card_rect.width - 4, card_rect.height - 4))
                    
                    # Draw image
                    image_rect = scaled_image.get_rect(center=card_rect.center)
                    surface.blit(scaled_image, image_rect)
                    
                    # Draw colored border
                    border_color = tuple(gate_config.get('border_color', gate_config.get('rgb', [255, 255, 255])))
                    if not can_draw:
                        border_color = tuple(c // 2 for c in border_color)
                    pygame.draw.rect(surface, border_color, card_rect, 3)
                    
                except Exception as e:
                    print(f"Error loading card image {image_path}: {e}")
                    # Fallback to color
                    self._draw_color_card(surface, card_rect, gate_config, can_draw)
            else:
                # Use color background
                self._draw_color_card(surface, card_rect, gate_config, can_draw)
        
        # Draw text if provided
        if text:
            text_color = (0, 0, 0) if can_draw else (64, 64, 64)
            card_text = self.large_font.render(text, True, text_color)
            text_rect = card_text.get_rect(center=(card_rect.centerx, card_rect.centery - 12))
            surface.blit(card_text, text_rect)
            
        if subtext:
            text_color = (0, 0, 0) if can_draw else (64, 64, 64)
            sub_surface = self.font.render(subtext, True, text_color)
            sub_rect = sub_surface.get_rect(center=(card_rect.centerx, card_rect.centery + 18))
            surface.blit(sub_surface, sub_rect)
    
    def _draw_color_card(self, surface, card_rect, gate_config, can_draw):
        """Helper to draw a card with color background"""
        color = tuple(gate_config.get('rgb', [150, 150, 150]))
        if not can_draw:
            color = tuple(c // 2 for c in color)
        
        pygame.draw.rect(surface, color, card_rect)
        border_color = (255, 255, 255) if can_draw else (128, 128, 128)
        pygame.draw.rect(surface, border_color, card_rect, 2)
        
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
            # Draw from deck (can draw 2 cards) - no animation needed
            cards_to_draw = min(2 - self.cards_drawn_this_turn, 2)
            cards = self.game_state.draw_cards(cards_to_draw)
            for card in cards:
                current_player.add_cards(card)
            self.cards_drawn_this_turn += cards_to_draw
            print(f"Drew {cards_to_draw} cards from deck")
        else:
            # Create animation for taking specific visible card
            self.create_card_animation(card_idx, selected_card)
            return  # Don't process immediately, wait for animation
            
        # Check if turn should end
        if self.cards_drawn_this_turn >= self.max_cards_per_turn:
            self.end_turn()
            
    def create_card_animation(self, card_idx: int, card_type):
        """Create animation for card moving from trade row to hand"""
        # Calculate start position (card in trade row)
        card_height = 60
        card_spacing = 10
        start_x = self.available_cards_rect.x + 10
        start_y = self.available_cards_rect.y + 60 + card_idx * (card_height + card_spacing)
        start_pos = (start_x, start_y)
        
        # Calculate end position based on existing cards in hand
        current_player = self.game_state.get_current_player()
        if not current_player:
            return
            
        # Find where this card type should go in the hand
        card_width = 90
        card_spacing_hand = 12
        hand_start_x = self.hand_area_rect.x + 20
        hand_start_y = self.hand_area_rect.y + 50
        
        # Find position of existing card of same type, or end position
        target_x = hand_start_x
        target_y = hand_start_y
        
        # Check if we have this card type already
        if current_player.hand.get(card_type, 0) > 0:
            # Find the position of the existing card of this type
            x_offset = 0
            for gate_type, count in current_player.hand.items():
                if count > 0:
                    if gate_type == card_type:
                        # Found the existing pile, animate to this position
                        target_x = hand_start_x + x_offset
                        target_y = hand_start_y
                        break
                    x_offset += card_width + card_spacing_hand
        else:
            # No existing pile, add at the end
            x_offset = 0
            for gate_type, count in current_player.hand.items():
                if count > 0:
                    x_offset += card_width + card_spacing_hand
            target_x = hand_start_x + x_offset
            target_y = hand_start_y
        
        end_pos = (target_x, target_y)
        
        # Create animation
        animation = CardAnimation(start_pos, end_pos, card_type, duration=0.6)
        self.card_animations.append(animation)
        
        # Store animation data for completion
        animation.card_idx = card_idx
        animation.card_type = card_type
        
    def complete_card_animation(self, animation: CardAnimation):
        """Complete the card animation and update game state"""
        current_player = self.game_state.get_current_player()
        if not current_player:
            return
            
        # Add card to player's hand
        current_player.add_cards(animation.card_type)
        self.cards_drawn_this_turn += 1
        
        # Replace with new card from deck
        if self.game_state.deck:
            new_card = self.game_state.deck.pop()
            self.available_cards[animation.card_idx] = new_card
            
            # Create animation for new card appearing
            self.create_new_card_animation(animation.card_idx, new_card)
        else:
            # Remove card if deck is empty
            self.available_cards.pop(animation.card_idx)
            
        print(f"Drew card: {animation.card_type}")
        
        # Check if turn should end
        if self.cards_drawn_this_turn >= self.max_cards_per_turn:
            self.end_turn()
            
    def create_new_card_animation(self, card_idx: int, card_type):
        """Create animation for new card appearing in trade row"""
        # Calculate final position in trade row
        card_height = 60
        card_spacing = 10
        end_x = self.available_cards_rect.x + 10
        end_y = self.available_cards_rect.y + 60 + card_idx * (card_height + card_spacing)
        end_pos = (end_x, end_y)
        
        # Start from the deck position (where the DECK card is)
        # Find the DECK card position
        deck_idx = len(self.available_cards) - 1  # DECK is always last
        deck_y = self.available_cards_rect.y + 60 + deck_idx * (card_height + card_spacing)
        start_x = self.available_cards_rect.x + 10
        start_y = deck_y
        start_pos = (start_x, start_y)
        
        # Set deck animation start time for visual effect
        self.deck_animation_start = time.time()
        
        # Create animation
        animation = CardAnimation(start_pos, end_pos, card_type, duration=0.4)
        self.new_card_animations.append(animation)
            
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
            GateType.Z: tuple(self.colors['gate_colors']['Z']['rgb']),
            GateType.H: tuple(self.colors['gate_colors']['H']['rgb']),
            GateType.CNOT: tuple(self.colors['gate_colors']['CNOT']['rgb']),
            "DECK": (100, 100, 100)
        }
        
        start_x = self.available_cards_rect.x + 10
        start_y = self.available_cards_rect.y + 60
        
        for i, card in enumerate(self.available_cards):
            # Skip if card is being animated (moving to hand)
            if any(anim.card_idx == i for anim in self.card_animations):
                continue
                
            y = start_y + i * (card_height + card_spacing)
            card_rect = pygame.Rect(start_x, y, card_width, card_height)
            
            # Skip if card would be outside the panel
            if y + card_height > self.available_cards_rect.bottom - 10:
                break
            
            # Get card info
            if card == "DECK":
                gate_type = "DECK"
                text = "DECK"
                subtext = ""
                
                # Add visual effect if deck is being used
                can_draw = self.cards_drawn_this_turn < self.max_cards_per_turn
                if self.deck_animation_start and time.time() - self.deck_animation_start < 0.4:
                    # Add a pulsing effect to the deck
                    pulse = abs(math.sin((time.time() - self.deck_animation_start) * 10)) * 0.3 + 0.7
                    # Temporarily modify the card color for visual feedback
                    original_color = self.colors['gate_colors']['DECK']['rgb']
                    pulse_color = tuple(int(c * pulse) for c in original_color)
                    # Store original color and temporarily change it
                    self.colors['gate_colors']['DECK']['rgb'] = pulse_color
                    self.draw_card_with_image_support(self.screen, card_rect, gate_type, can_draw, text, subtext)
                    # Restore original color
                    self.colors['gate_colors']['DECK']['rgb'] = original_color
                else:
                    self.draw_card_with_image_support(self.screen, card_rect, gate_type, can_draw, text, subtext)
            else:
                gate_type = card
                text = card.value if hasattr(card, 'value') else str(card)
                subtext = ""
                
                # Check if card can be drawn
                can_draw = self.cards_drawn_this_turn < self.max_cards_per_turn
                
                # Draw card using image support function
                self.draw_card_with_image_support(self.screen, card_rect, gate_type, can_draw, text, subtext)
            
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
            GateType.Z: tuple(self.colors['gate_colors']['Z']['rgb']),
            GateType.H: tuple(self.colors['gate_colors']['H']['rgb']),
            GateType.CNOT: tuple(self.colors['gate_colors']['CNOT']['rgb'])
        }
        
        x_offset = 0
        for gate_type, count in current_player.hand.items():
            if count > 0:
                card_rect = pygame.Rect(start_x + x_offset, start_y, card_width, card_height)
                
                # Draw card shadow
                shadow_rect = pygame.Rect(card_rect.x + 2, card_rect.y + 2, card_rect.width, card_rect.height)
                pygame.draw.rect(self.screen, (0, 0, 0, 80), shadow_rect)
                
                # Draw card using image support
                gate_text = gate_type.value
                count_text = f"x{count}"
                self.draw_card_with_image_support(self.screen, card_rect, gate_type, True, gate_text, count_text)
                
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
            f"> {current_player.name}",
            f"Cards: {current_player.get_total_cards()}",
            f"Routes: {len(current_player.claimed_routes)}",
            f"Score: {current_player.score}",
            "",
        ])
        
        # Mission info
        if current_player.mission:
            mission = current_player.mission
            start_str = " OR ".join(mission.start_cities)
            info_lines.extend([
                "Mission:",
                f"From: {start_str}",
                f"{mission.initial_state} → {mission.target_city} {mission.target_state}",
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
            marker = "> " if player == current_player else "  "
            info_lines.append(f"{marker}{player.name}")
            info_lines.append(f"  Cards: {player.get_total_cards()}, Routes: {len(player.claimed_routes)}, Score: {player.score}")
        
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
                color = current_player.color if line.startswith(">") else self.TEXT_COLOR
                text = self.font.render(line, True, color)
                self.screen.blit(text, (self.sidebar_rect.x + 15, self.sidebar_rect.y + y_offset))
            y_offset += 22
    
    def draw_animated_cards(self):
        """Draw cards that are currently being animated"""
        # Draw cards moving to hand
        for animation in self.card_animations:
            pos = animation.get_current_pos()
            scale = animation.get_scale()
            
            # Calculate scaled card dimensions
            base_width, base_height = 90, 60
            scaled_width = int(base_width * scale)
            scaled_height = int(base_height * scale)
            
            # Center the scaled card on the animation position
            card_rect = pygame.Rect(
                pos[0] - (scaled_width - base_width) // 2,
                pos[1] - (scaled_height - base_height) // 2,
                scaled_width, scaled_height
            )
            
            # Draw card shadow
            shadow_rect = pygame.Rect(card_rect.x + 2, card_rect.y + 2, card_rect.width, card_rect.height)
            shadow_surface = pygame.Surface((card_rect.width, card_rect.height))
            shadow_surface.set_alpha(80)
            shadow_surface.fill((0, 0, 0))
            self.screen.blit(shadow_surface, shadow_rect)
            
            # Draw the animated card
            gate_text = animation.card_type.value if hasattr(animation.card_type, 'value') else str(animation.card_type)
            self.draw_card_with_image_support(self.screen, card_rect, animation.card_type, True, gate_text, "")
            
        # Draw new cards appearing in trade row
        for animation in self.new_card_animations:
            pos = animation.get_current_pos()
            scale = animation.get_scale()
            
            # Calculate scaled card dimensions
            base_width = self.available_cards_rect.width - 20
            base_height = 60
            scaled_width = int(base_width * scale)
            scaled_height = int(base_height * scale)
            
            # Center the scaled card on the animation position
            card_rect = pygame.Rect(
                pos[0] - (scaled_width - base_width) // 2,
                pos[1] - (scaled_height - base_height) // 2,
                scaled_width, scaled_height
            )
            
            # Draw the new card
            gate_text = animation.card_type.value if hasattr(animation.card_type, 'value') else str(animation.card_type)
            self.draw_card_with_image_support(self.screen, card_rect, animation.card_type, True, gate_text, "")
    
    def draw(self) -> None:
        self.screen.fill(self.BACKGROUND_COLOR)
        
        self.draw_sidebar()
        self.draw_map_area()
        self.draw_available_cards()
        self.draw_hand_area()
        self.draw_animated_cards()  # Draw animated cards on top
        
        pygame.display.flip()
    
    def run(self) -> None:
        if not self.initialize():
            return
        
        self.running = True
        
        while self.running:
            self.handle_events()
            self.update_animations()  # Update animations
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

    def update_animations(self):
        """Update and complete animations"""
        # Update card animations (moving to hand)
        completed_animations = []
        for animation in self.card_animations:
            if animation.is_finished():
                completed_animations.append(animation)
                self.complete_card_animation(animation)
        
        # Remove completed animations
        for animation in completed_animations:
            self.card_animations.remove(animation)
            
        # Update new card animations (appearing in trade row)
        completed_new_animations = []
        for animation in self.new_card_animations:
            if animation.is_finished():
                completed_new_animations.append(animation)
                
        # Remove completed new card animations and clear deck animation state
        for animation in completed_new_animations:
            self.new_card_animations.remove(animation)
            self.deck_animation_start = None  # Clear deck animation state

def main():
    game_window = GameWindow()
    game_window.run()

if __name__ == "__main__":
    main()
