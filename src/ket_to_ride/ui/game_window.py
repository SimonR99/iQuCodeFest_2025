import pygame
import sys
import os
import json
import math
import time
from typing import Optional, Tuple, Dict, List
from .map_renderer import MapRenderer
from .animation import CardAnimation, AnimationManager
from .card_renderer import CardRenderer
from ..game import GameState, GateType

class GameWindow:
    def __init__(self, width: int = 1280, height: int = 720, audio_manager=None):
        self.width = width
        self.height = height
        self.min_width = 800
        self.min_height = 600
        self.screen: Optional[pygame.Surface] = None
        self.clock = pygame.time.Clock()
        self.running = False
        
        # Initialize game state and map renderer
        config_path = os.path.join(os.path.dirname(__file__), '../../..', 'config', 'university_map.json')
        self.map_renderer = MapRenderer(config_path)
        self.game_state = GameState(config_path)
        
        # Animation state - now using AnimationManager
        self.animation_manager = AnimationManager()
        
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
        
        # Mission drawing state
        self.mission_selection_active = False
        self.available_missions = []  # Missions drawn for selection
        self.selected_missions = []   # Missions selected by player
        self.mission_back_image = None
        self.load_mission_back_image()
        
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
        
        # Card renderer will be initialized after fonts are created
        self.card_renderer = None
        
        # Audio manager reference
        self.audio_manager = audio_manager
    
    def update_layout(self) -> None:
        # Layout like real Ticket to Ride
        # Left sidebar for player info and scores
        sidebar_width = 250
        
        # Right panel for available cards and mission deck
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
        
        # Right panel split between available cards and mission deck
        right_panel_x = map_x + map_width + 10
        right_panel_height = self.height - 20
        
        # Top part for available gate cards (70% of right panel)
        available_cards_height = int(right_panel_height * 0.7)
        self.available_cards_rect = pygame.Rect(right_panel_x, 10, right_panel_width, available_cards_height)
        
        # Bottom part for mission deck (30% of right panel)
        mission_deck_y = 10 + available_cards_height + 10
        mission_deck_height = right_panel_height - available_cards_height - 10
        self.mission_deck_rect = pygame.Rect(right_panel_x, mission_deck_y, right_panel_width, mission_deck_height)
        
        # Bottom area for player hand (aligned with map)
        hand_y = map_y + map_height + 10
        self.hand_area_rect = pygame.Rect(map_x, hand_y, map_width, hand_area_height)
        
    def initialize(self) -> bool:
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("|ket⟩ to Ride")
        
        # Initialize font
        pygame.font.init()
        font_path = os.path.join("assets", "fonts", "DejaVuSans.ttf")
        
        # Load custom font directly, with smaller sizes.
        self.font = pygame.font.Font(font_path, 22)
        self.title_font = pygame.font.Font(font_path, 34)
        self.small_font = pygame.font.Font(font_path, 18)
        self.large_font = pygame.font.Font(font_path, 26)
        
        # Initialize card renderer with fonts
        fonts = {
            'font': self.font,
            'title_font': self.title_font,
            'small_font': self.small_font,
            'large_font': self.large_font
        }
        self.card_renderer = CardRenderer(self.colors, fonts)
        
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
            
    def load_mission_back_image(self):
        """Load the mission card back image"""
        try:
            image_path = os.path.join("assets", "cards", "destination_back.png")
            if os.path.exists(image_path):
                self.mission_back_image = pygame.image.load(image_path)
                print(f"Loaded mission back image: {image_path}")
            else:
                print(f"Mission back image not found: {image_path}")
                self.mission_back_image = None
        except Exception as e:
            print(f"Error loading mission back image: {e}")
            self.mission_back_image = None
    
    def load_colors(self):
        """Load colors from configuration file"""
        config_path = os.path.join(os.path.dirname(__file__), '../../..', 'config', 'colors.json')
        with open(config_path, 'r') as f:
            return json.load(f)
    
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
                    if self.mission_selection_active:
                        self.cancel_mission_selection()
                    else:
                        self.running = False
                elif event.key == pygame.K_SPACE:  # Next turn
                    if not self.mission_selection_active:
                        self.end_turn()
                elif event.key == pygame.K_c:  # Claim selected route
                    if not self.mission_selection_active:
                        self.handle_claim_route()
                elif event.key == pygame.K_r:  # Cycle through routes
                    if not self.mission_selection_active:
                        self.cycle_route_selection()
                elif event.key == pygame.K_m:  # Draw mission cards
                    if not self.mission_selection_active:
                        self.draw_mission_cards()
                elif event.key == pygame.K_RETURN:  # Confirm mission selection
                    if self.mission_selection_active:
                        self.confirm_mission_selection()
                elif event.key == pygame.K_1:  # Toggle mission 1
                    if self.mission_selection_active:
                        self.toggle_mission_selection(0)
                elif event.key == pygame.K_2:  # Toggle mission 2
                    if self.mission_selection_active:
                        self.toggle_mission_selection(1)
                elif event.key == pygame.K_3:  # Toggle mission 3
                    if self.mission_selection_active:
                        self.toggle_mission_selection(2)
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
        # Handle mission selection if active
        if self.mission_selection_active:
            self.handle_mission_selection_click(pos)
            return
            
        # Handle clicking on mission deck
        if self.mission_deck_rect.collidepoint(pos):
            self.draw_mission_cards()
            return
            
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
            
    def handle_mission_selection_click(self, pos: Tuple[int, int]):
        """Handle clicks during mission selection"""
        # Check if clicking on a mission card in the sidebar
        if self.sidebar_rect.collidepoint(pos):
            mission_idx = self.get_clicked_mission_card(pos)
            if mission_idx is not None:
                self.toggle_mission_selection(mission_idx)
                
    def get_clicked_mission_card(self, pos: Tuple[int, int]) -> Optional[int]:
        """Determine which mission card was clicked during selection"""
        # Mission cards are displayed in the sidebar during selection
        # Calculate based on sidebar layout
        if not self.available_missions:
            return None
            
        # Mission cards start after the title and some info
        start_y = self.sidebar_rect.y + 200  # Adjust based on sidebar content
        card_height = 80
        card_spacing = 10
        
        relative_y = pos[1] - start_y
        if relative_y < 0:
            return None
            
        for i in range(len(self.available_missions)):
            card_top = i * (card_height + card_spacing)
            card_bottom = card_top + card_height
            
            if card_top <= relative_y <= card_bottom:
                return i
                
        return None
        
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
        self.animation_manager.add_card_animation(animation)
        
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
        self.animation_manager.set_deck_animation_start(time.time())
        
        # Create animation
        animation = CardAnimation(start_pos, end_pos, card_type, duration=0.4)
        self.animation_manager.add_new_card_animation(animation)
            
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
            
        route = self.game_state.routes[self.selected_route_idx]
        gate_type = route['gate']
        required_cards = route['length']
        
        if current_player.hand.get(gate_type, 0) >= required_cards:
            # Claim the route
            current_player.claim_route(self.selected_route_idx, required_cards, gate_type)
            route['claimed_by'] = current_player.name
            
            # Play mouse click sound
            if self.audio_manager:
                self.audio_manager.play_sound_effect("mouse_click")
            
            print(f"Claimed route: {route['from']} -> {route['to']}")
            self.selected_route_idx = None
        else:
            print(f"Not enough {gate_type.value} cards! Need {required_cards}, have {current_player.hand.get(gate_type, 0)}")
    
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
        title_text = self.font.render("Gate Cards", True, self.TEXT_COLOR)
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
            if self.animation_manager.is_card_being_animated(i):
                continue
                
            y = start_y + i * (card_height + card_spacing)
            card_rect = pygame.Rect(start_x, y, card_width, card_height)
            
            # Skip if card would be outside the panel
            if y + card_height > self.available_cards_rect.bottom - 10:
                break
            
            # Get card info
            if card == "DECK":
                gate_type = "DECK"
                
                # Add visual effect if deck is being used
                can_draw = self.cards_drawn_this_turn < self.max_cards_per_turn
                if self.animation_manager.deck_animation_start and time.time() - self.animation_manager.deck_animation_start < 0.4:
                    # Add a pulsing effect to the deck
                    pulse = abs(math.sin((time.time() - self.animation_manager.deck_animation_start) * 10)) * 0.3 + 0.7
                    # Temporarily modify the card color for visual feedback
                    original_color = self.colors['gate_colors']['DECK']['rgb']
                    pulse_color = tuple(int(c * pulse) for c in original_color)
                    # Store original color and temporarily change it
                    self.colors['gate_colors']['DECK']['rgb'] = pulse_color
                    self.card_renderer.draw_card_with_image_support(self.screen, card_rect, gate_type, can_draw, "", "", False)
                    # Restore original color
                    self.colors['gate_colors']['DECK']['rgb'] = original_color
                else:
                    self.card_renderer.draw_card_with_image_support(self.screen, card_rect, gate_type, can_draw, "", "", False)
            else:
                gate_type = card
                
                # Check if card can be drawn
                can_draw = self.cards_drawn_this_turn < self.max_cards_per_turn
                
                # Draw card using image support function
                self.card_renderer.draw_card_with_image_support(self.screen, card_rect, gate_type, can_draw, "", "", False)
                
    def draw_mission_deck(self) -> None:
        # Draw mission deck area (bottom of right panel)
        pygame.draw.rect(self.screen, self.CARD_AREA_COLOR, self.mission_deck_rect)
        pygame.draw.rect(self.screen, self.BORDER_COLOR, self.mission_deck_rect, 3)
        
        # Add header accent
        header_rect = pygame.Rect(self.mission_deck_rect.x + 3, self.mission_deck_rect.y + 3,
                                 self.mission_deck_rect.width - 6, 30)
        pygame.draw.rect(self.screen, self.ACCENT_COLOR, header_rect)
        
        # Draw title
        title_text = self.small_font.render("Mission Cards", True, self.TEXT_COLOR)
        title_rect = title_text.get_rect(center=(header_rect.centerx, header_rect.centery))
        self.screen.blit(title_text, title_rect)
        
        # Draw mission deck count
        deck_count_text = f"Deck: {len(self.game_state.mission_deck)}"
        deck_count_surface = self.small_font.render(deck_count_text, True, self.TEXT_COLOR)
        self.screen.blit(deck_count_surface, (self.mission_deck_rect.x + 10, self.mission_deck_rect.y + 35))
        
        # Draw mission deck card (clickable)
        card_width = self.mission_deck_rect.width - 20
        card_height = 80
        card_x = self.mission_deck_rect.x + 10
        card_y = self.mission_deck_rect.y + 55
        
        if len(self.game_state.mission_deck) > 0:
            card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
            
            # Draw card shadow
            shadow_rect = pygame.Rect(card_rect.x + 2, card_rect.y + 2, card_rect.width, card_rect.height)
            pygame.draw.rect(self.screen, (0, 0, 0, 80), shadow_rect)
            
            # Draw mission card back
            if self.mission_back_image:
                # Scale the image to fit the card
                scaled_image = pygame.transform.scale(self.mission_back_image, (card_rect.width, card_rect.height))
                self.screen.blit(scaled_image, card_rect)
            else:
                # Fallback to colored rectangle
                pygame.draw.rect(self.screen, (150, 100, 50), card_rect)
                
            # Draw border
            pygame.draw.rect(self.screen, self.BORDER_COLOR, card_rect, 2)
            
            # Draw "MISSIONS" text
            mission_text = self.small_font.render("MISSIONS", True, self.TEXT_COLOR)
            text_rect = mission_text.get_rect(center=card_rect.center)
            self.screen.blit(mission_text, text_rect)
            
            # Add click hint
            hint_text = "Click to draw"
            hint_surface = self.small_font.render(hint_text, True, self.TEXT_COLOR)
            hint_rect = hint_surface.get_rect(center=(card_rect.centerx, card_rect.bottom - 15))
            self.screen.blit(hint_surface, hint_rect)
        else:
            # Empty deck
            empty_text = "No missions left"
            empty_surface = self.small_font.render(empty_text, True, self.TEXT_COLOR)
            empty_rect = empty_surface.get_rect(center=(self.mission_deck_rect.centerx, card_y + card_height // 2))
            self.screen.blit(empty_surface, empty_rect)
    
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
        count_text_height = 20  # Space for count text below card
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
                
                # Draw card without text
                self.card_renderer.draw_card_with_image_support(self.screen, card_rect, gate_type, True, "", "", False)
                
                # Draw count below the card
                count_text = f"x{count}"
                count_surface = self.small_font.render(count_text, True, self.TEXT_COLOR)
                count_rect = count_surface.get_rect(center=(card_rect.centerx, card_rect.bottom + count_text_height // 2))
                self.screen.blit(count_surface, count_rect)
                
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
        title_text = self.large_font.render("|ket⟩ to Ride", True, self.TEXT_COLOR)
        title_rect_text = title_text.get_rect(center=(title_rect_bg.centerx, title_rect_bg.centery))
        self.screen.blit(title_text, title_rect_text)
        
        current_player = self.game_state.get_current_player()
        if not current_player:
            return
        
        # Handle mission selection interface
        if self.mission_selection_active:
            self.draw_mission_selection_interface()
            return
        
        # Prepare info lines with current game state
        info_lines = [
            f"Turn: {self.game_state.turn_number}",
            f"Gate Cards in Deck: {len(self.game_state.deck)}",
            f"Mission Cards in Deck: {len(self.game_state.mission_deck)}",
            "",
        ]
        
        # Current player info
        info_lines.extend([
            f"Current Player:",
            f"> {current_player.name}",
            f"Gate Cards: {current_player.get_total_cards()}",
            f"Routes: {len(current_player.claimed_routes)}",
            f"Score: {current_player.score}",
            "",
        ])
        
        # Mission info
        if current_player.missions:
            info_lines.extend([
                f"Missions ({len(current_player.missions)}):",
            ])
            for i, mission in enumerate(current_player.missions):
                start_str = " OR ".join(mission.start_cities)
                status = "✓" if mission.completed else "○"
                info_lines.extend([
                    f"{status} {start_str}",
                    f"  {mission.initial_state} → {mission.target_city} {mission.target_state}",
                    f"  Points: {mission.points}",
                    "",
                ])
        else:
            info_lines.extend([
                "No missions yet",
                "Press M to draw missions",
                "",
            ])
        
        # Turn actions
        info_lines.extend([
            "Turn Actions:",
            f"Gate cards drawn: {self.cards_drawn_this_turn}/{self.max_cards_per_turn}",
            "",
            "You can either:",
            "• Draw gate cards (2 max)",
            "• Draw mission cards (M)",
            "• Claim one route",
            "",
            "Controls:",
            "• Click cards to draw",
            "• Click routes to select",
            "• M - Draw Missions",
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
            info_lines.append(f"  Gate Cards: {player.get_total_cards()}, Routes: {len(player.claimed_routes)}")
            info_lines.append(f"  Missions: {len(player.missions)} ({len(player.get_completed_missions())} completed)")
            info_lines.append(f"  Score: {player.score}")
        
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
            
    def draw_mission_selection_interface(self):
        """Draw the mission selection interface in the sidebar"""
        y_offset = 65
        
        # Title
        title_lines = [
            "MISSION SELECTION",
            "Choose missions to keep:",
            f"Selected: {len(self.selected_missions)}/3",
            "Must keep at least 1",
            "",
        ]
        
        for line in title_lines:
            if line:
                text = self.font.render(line, True, self.ACCENT_COLOR)
                self.screen.blit(text, (self.sidebar_rect.x + 15, self.sidebar_rect.y + y_offset))
            y_offset += 22
        
        # Draw mission cards
        card_height = 80
        card_spacing = 10
        card_width = self.sidebar_rect.width - 30
        
        for i, mission in enumerate(self.available_missions):
            card_x = self.sidebar_rect.x + 15
            card_y = self.sidebar_rect.y + y_offset
            card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
            
            # Determine if this mission is selected
            is_selected = mission in self.selected_missions
            
            # Draw card background
            bg_color = self.ACCENT_COLOR if is_selected else self.CARD_AREA_COLOR
            pygame.draw.rect(self.screen, bg_color, card_rect)
            pygame.draw.rect(self.screen, self.BORDER_COLOR, card_rect, 2)
            
            # Draw mission info
            start_str = " OR ".join(mission.start_cities)
            mission_lines = [
                f"{i+1}. {start_str}",
                f"{mission.initial_state} → {mission.target_city} {mission.target_state}",
                f"Points: {mission.points}",
            ]
            
            text_y = card_y + 10
            for line in mission_lines:
                text_color = self.TEXT_COLOR if not is_selected else (255, 255, 255)
                text = self.small_font.render(line, True, text_color)
                self.screen.blit(text, (card_x + 10, text_y))
                text_y += 20
                
            # Draw selection indicator
            if is_selected:
                check_text = "✓ SELECTED"
                check_surface = self.small_font.render(check_text, True, (255, 255, 255))
                check_rect = check_surface.get_rect(right=card_rect.right - 10, bottom=card_rect.bottom - 5)
                self.screen.blit(check_surface, check_rect)
            
            y_offset += card_height + card_spacing
        
        # Draw controls
        y_offset += 20
        control_lines = [
            "",
            "Controls:",
            "• Click cards to select",
            "• 1/2/3 - Toggle missions",
            "• ENTER - Confirm selection",
            "• ESC - Cancel",
        ]
        
        for line in control_lines:
            if line:
                text = self.small_font.render(line, True, self.TEXT_COLOR)
                self.screen.blit(text, (self.sidebar_rect.x + 15, self.sidebar_rect.y + y_offset))
            y_offset += 18
    
    def draw_animated_cards(self):
        """Draw cards that are currently being animated"""
        # Draw cards moving to hand
        for animation in self.animation_manager.card_animations:
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
            self.card_renderer.draw_card_with_image_support(self.screen, card_rect, animation.card_type, True, "", "", False)
            
        # Draw new cards appearing in trade row
        for animation in self.animation_manager.new_card_animations:
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
            self.card_renderer.draw_card_with_image_support(self.screen, card_rect, animation.card_type, True, "", "", False)
    
    def draw(self) -> None:
        self.screen.fill(self.BACKGROUND_COLOR)
        
        self.draw_sidebar()
        self.draw_map_area()
        self.draw_available_cards()
        self.draw_mission_deck()
        self.draw_hand_area()
        self.draw_animated_cards()  # Draw animated cards on top
        
        pygame.display.flip()
    
    def run(self) -> None:
        """Main game loop"""
        if not self.initialize():
            return
        
        self.running = True
        
        while self.running:
            self.handle_events()
            self.update_animations()
            self.draw()
            self.clock.tick(60)
            
        # Don't quit pygame here - let the main menu handle it
        # pygame.quit()

    def update_animations(self):
        """Update and complete animations"""
        # Update card animations (moving to hand)
        completed_animations = []
        for animation in self.animation_manager.card_animations:
            if animation.is_finished():
                completed_animations.append(animation)
                self.complete_card_animation(animation)
        
        # Remove completed animations
        for animation in completed_animations:
            self.animation_manager.card_animations.remove(animation)
            
        # Update new card animations (appearing in trade row)
        completed_new_animations = []
        for animation in self.animation_manager.new_card_animations:
            if animation.is_finished():
                completed_new_animations.append(animation)
                
        # Remove completed new card animations and clear deck animation state
        for animation in completed_new_animations:
            self.animation_manager.new_card_animations.remove(animation)
            self.animation_manager.clear_deck_animation_start()  # Clear deck animation state

    def draw_mission_cards(self):
        """Start mission card drawing process"""
        current_player = self.game_state.get_current_player()
        if not current_player or self.game_state.game_over:
            return
            
        # Can't draw missions if already drew gate cards this turn
        if self.cards_drawn_this_turn > 0:
            print("Cannot draw missions after drawing gate cards!")
            return
            
        # Can't draw missions if not enough in deck
        if not self.game_state.can_draw_missions(current_player):
            print("Not enough mission cards in deck!")
            return
            
        # Draw 3 mission cards for selection
        self.available_missions = self.game_state.draw_mission_cards(3)
        self.selected_missions = []
        self.mission_selection_active = True
        print(f"Drew 3 mission cards for selection. Must keep at least 1.")
        
    def toggle_mission_selection(self, mission_idx: int):
        """Toggle selection of a mission card"""
        if not self.mission_selection_active or mission_idx >= len(self.available_missions):
            return
            
        mission = self.available_missions[mission_idx]
        
        if mission in self.selected_missions:
            self.selected_missions.remove(mission)
            print(f"Deselected mission: {mission}")
        else:
            self.selected_missions.append(mission)
            print(f"Selected mission: {mission}")
            
    def confirm_mission_selection(self):
        """Confirm mission selection and end turn"""
        if not self.mission_selection_active:
            return
            
        # Must keep at least 1 mission
        if len(self.selected_missions) == 0:
            print("Must select at least 1 mission!")
            return
            
        current_player = self.game_state.get_current_player()
        if not current_player:
            return
            
        # Assign selected missions to player
        self.game_state.assign_missions_to_player(current_player, self.selected_missions)
        
        # Return unselected missions to deck
        unselected = [m for m in self.available_missions if m not in self.selected_missions]
        if unselected:
            self.game_state.return_missions_to_deck(unselected)
            
        print(f"Confirmed {len(self.selected_missions)} missions for {current_player.name}")
        
        # Clear mission selection state
        self.mission_selection_active = False
        self.available_missions = []
        self.selected_missions = []
        
        # End turn
        self.end_turn()
        
    def cancel_mission_selection(self):
        """Cancel mission selection and return all cards to deck"""
        if not self.mission_selection_active:
            return
            
        # Return all missions to deck
        self.game_state.return_missions_to_deck(self.available_missions)
        
        print("Cancelled mission selection")
        
        # Clear mission selection state
        self.mission_selection_active = False
        self.available_missions = []
        self.selected_missions = []

def main():
    game_window = GameWindow()
    game_window.run()

if __name__ == "__main__":
    main()
