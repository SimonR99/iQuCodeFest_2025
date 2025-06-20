import pygame
import sys
import os
import json
from typing import Optional, Tuple, Dict
from .map_renderer import MapRenderer
from .animation import AnimationManager
from .card_renderer import CardRenderer
from .panels import MapPanel, AvailableCardsPanel, HandPanel, SidebarPanel, MissionDeckPanel
from ..game import GameState

class GameWindow:
    def __init__(self, width: int = 1280, height: int = 720, audio_manager=None):
        self.width = width
        self.height = height
        self.min_width = 800
        self.min_height = 600
        self.screen: Optional[pygame.Surface] = None
        self.clock = pygame.time.Clock()
        self.running = False
        
        # Initialize core components
        config_path = os.path.join(os.path.dirname(__file__), '../../..', 'config', 'university_map.json')
        self.map_renderer = MapRenderer(config_path)
        self.game_state = GameState(config_path)
        self.animation_manager = AnimationManager()
        
        # Load colors and setup UI
        self.colors = self.load_colors()
        self.fonts = {}
        self.card_renderer = None
        self.panels = {}
        
        # Game state
        self.selected_route_idx = None
        self.hovered_route_idx = None
        self.available_cards = []
        self.cards_drawn_this_turn = 0
        self.max_cards_per_turn = 2
        
        # Mission state
        self.mission_selection_active = False
        self.available_missions = []
        self.selected_missions = []
        
        # Audio manager reference
        self.audio_manager = audio_manager
        
    def load_colors(self):
        """Load colors from configuration file"""
        config_path = os.path.join(os.path.dirname(__file__), '../../..', 'config', 'colors.json')
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def initialize(self) -> bool:
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("|ket⟩ to Ride")
        
        # Initialize fonts
        pygame.font.init()
        font_path = os.path.join("assets", "fonts", "DejaVuSans.ttf")
        self.fonts = {
            'font': pygame.font.Font(font_path, 22),
            'title_font': pygame.font.Font(font_path, 34),
            'small_font': pygame.font.Font(font_path, 18),
            'large_font': pygame.font.Font(font_path, 26)
        }
        
        # Initialize card renderer
        self.card_renderer = CardRenderer(self.colors, self.fonts)
        
        # Setup game and UI
        self.setup_game()
        self.setup_ui()
        self.setup_available_cards()
        
        return True
    
    def setup_game(self):
        """Setup initial game state"""
        player_colors = [(255, 100, 100), (100, 100, 255)]
        player_names = ["Alice", "Bob"]
        
        for name, color in zip(player_names, player_colors):
            self.game_state.add_player(name, color)
    
    def setup_ui(self):
        """Setup UI panels"""
        self.update_layout()
        
        # Create panels
        self.panels['map'] = MapPanel(self.map_rect, self.colors, self.fonts, self.map_renderer)
        self.panels['available_cards'] = AvailableCardsPanel(
            self.available_cards_rect, self.colors, self.fonts, self.card_renderer
        )
        self.panels['hand'] = HandPanel(self.hand_area_rect, self.colors, self.fonts, self.card_renderer)
        self.panels['sidebar'] = SidebarPanel(self.sidebar_rect, self.colors, self.fonts)
        self.panels['mission_deck'] = MissionDeckPanel(self.mission_deck_rect, self.colors, self.fonts)
        
    def update_layout(self):
        """Update UI layout based on current window size"""
        sidebar_width = 250
        right_panel_width = 200
        hand_area_height = 160
        
        map_x = sidebar_width + 10
        map_y = 10
        map_width = self.width - sidebar_width - right_panel_width - 30
        map_height = self.height - hand_area_height - 30
        
        self.sidebar_rect = pygame.Rect(10, 10, sidebar_width, self.height - 20)
        self.map_rect = pygame.Rect(map_x, map_y, map_width, map_height)
        
        right_panel_x = map_x + map_width + 10
        right_panel_height = self.height - 20
        
        # Top part for available gate cards (70% of right panel)
        available_cards_height = int(right_panel_height * 0.7)
        self.available_cards_rect = pygame.Rect(right_panel_x, 10, right_panel_width, available_cards_height)
        
        # Bottom part for mission deck (30% of right panel)
        mission_deck_y = 10 + available_cards_height + 10
        mission_deck_height = right_panel_height - available_cards_height - 10
        self.mission_deck_rect = pygame.Rect(right_panel_x, mission_deck_y, right_panel_width, mission_deck_height)
        
        hand_y = map_y + map_height + 10
        self.hand_area_rect = pygame.Rect(map_x, hand_y, map_width, hand_area_height)
        
        # Update panel rectangles if they exist
        if hasattr(self, 'panels'):
            for panel_name, panel in self.panels.items():
                if panel_name == 'map':
                    panel.update_rect(self.map_rect)
                elif panel_name == 'available_cards':
                    panel.update_rect(self.available_cards_rect)
                elif panel_name == 'hand':
                    panel.update_rect(self.hand_area_rect)
                elif panel_name == 'sidebar':
                    panel.update_rect(self.sidebar_rect)
                elif panel_name == 'mission_deck':
                    panel.update_rect(self.mission_deck_rect)
                    
    def setup_available_cards(self):
        """Setup available cards for drawing"""
        self.available_cards = []
        for _ in range(5):
            if self.game_state.deck:
                self.available_cards.append(self.game_state.deck.pop())
        self.available_cards.append("DECK")
    
    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.handle_keyboard(event.key)
            elif event.type == pygame.VIDEORESIZE:
                self.handle_resize(event.w, event.h)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.handle_mouse_click(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                self.handle_mouse_motion(event.pos)
    
    def handle_keyboard(self, key):
        """Handle keyboard input"""
        if key == pygame.K_ESCAPE:
            if self.mission_selection_active:
                self.cancel_mission_selection()
            else:
                self.running = False
        elif key == pygame.K_SPACE:
            self.end_turn()
        elif key == pygame.K_c:
            self.handle_claim_route()
        elif key == pygame.K_m:
            self.draw_missions()
        elif key == pygame.K_RETURN and self.mission_selection_active:
            self.confirm_mission_selection()
            
    def handle_resize(self, width, height):
        """Handle window resize"""
        self.width = max(width, self.min_width)
        self.height = max(height, self.min_height)
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        self.update_layout()
        
    def handle_mouse_click(self, pos: Tuple[int, int]):
        """Handle mouse clicks by delegating to panels"""
        # Try each panel first (this handles mission selection buttons)
        for panel_name, panel in self.panels.items():
            action = panel.handle_click(pos, self.game_state, 
                                      available_cards=self.available_cards,
                                      cards_drawn_this_turn=self.cards_drawn_this_turn,
                                      max_cards_per_turn=self.max_cards_per_turn,
                                      selected_route_idx=self.selected_route_idx,
                                      mission_selection_active=self.mission_selection_active,
                                      available_missions=self.available_missions,
                                      selected_missions=self.selected_missions)
            if action:
                self.handle_panel_action(action)
                return
        
        # Handle mission card selection clicks if active (only if no panel handled it)
        if self.mission_selection_active:
            self.handle_mission_selection_click(pos)
                
    def handle_mouse_motion(self, pos: Tuple[int, int]):
        """Handle mouse motion for hover effects"""
        # Update hovered route from map panel
        hover_info = self.panels['map'].handle_hover(pos, self.game_state)
        self.hovered_route_idx = hover_info
        
        # Handle sidebar button hover effects
        if self.panels['sidebar'].rect.collidepoint(pos):
            self.panels['sidebar'].handle_mouse_motion(pos)
        
    def handle_panel_action(self, action: str):
        """Handle actions returned by panels"""
        if action.startswith("route_selected:"):
            route_idx = int(action.split(":")[1])
            self.selected_route_idx = route_idx
            print(f"Selected route: {self.game_state.routes[route_idx]}")
        elif action.startswith("draw_card:"):
            card_idx = int(action.split(":")[1])
            self.draw_specific_card(card_idx)
        elif action == "draw_missions":
            self.draw_missions()
        elif action == "claim_route":
            self.handle_claim_route()
        elif action == "end_turn":
            self.end_turn()
        elif action == "confirm_mission_selection":
            self.confirm_mission_selection()
        elif action == "cancel_mission_selection":
            self.cancel_mission_selection()
            
    def draw_specific_card(self, card_idx: int):
        """Handle drawing a specific card with animation"""
        if (card_idx >= len(self.available_cards) or 
            self.cards_drawn_this_turn >= self.max_cards_per_turn):
            return
            
        current_player = self.game_state.get_current_player()
        if not current_player:
            return
            
        selected_card = self.available_cards[card_idx]
        
        if selected_card == "DECK":
            # Draw from deck (immediate, no animation)
            cards_to_draw = min(2 - self.cards_drawn_this_turn, 2)
            cards = self.game_state.draw_cards(cards_to_draw)
            for card in cards:
                current_player.add_cards(card)
            self.cards_drawn_this_turn += cards_to_draw
            print(f"Drew {cards_to_draw} cards from deck: {cards}")
        else:
            # Create animation for moving card to hand
            self.create_card_animation(card_idx, selected_card)
                
        if self.cards_drawn_this_turn >= self.max_cards_per_turn:
            self.end_turn()
    
    def create_card_animation(self, card_idx: int, card_type):
        """Create animation for card moving from available cards to hand"""
        # Calculate start position (card in available cards area)
        card_height = 60
        card_spacing = 10
        start_x = self.available_cards_rect.x + 10
        start_y = self.available_cards_rect.y + 60 + card_idx * (card_height + card_spacing)
        start_pos = (start_x, start_y)
        
        # Calculate end position in hand
        current_player = self.game_state.get_current_player()
        if not current_player:
            return
            
        card_width = 90
        card_spacing_hand = 12
        hand_start_x = self.hand_area_rect.x + 20
        hand_start_y = self.hand_area_rect.y + 50
        
        # Find position for this card type in hand
        target_x = hand_start_x
        target_y = hand_start_y
        
        if current_player.hand.get(card_type, 0) > 0:
            # Find existing pile of this card type
            x_offset = 0
            for gate_type, count in current_player.hand.items():
                if count > 0:
                    if gate_type == card_type:
                        target_x = hand_start_x + x_offset
                        target_y = hand_start_y
                        break
                    x_offset += card_width + card_spacing_hand
        else:
            # Add at end of hand
            x_offset = 0
            for gate_type, count in current_player.hand.items():
                if count > 0:
                    x_offset += card_width + card_spacing_hand
            target_x = hand_start_x + x_offset
            target_y = hand_start_y
        
        end_pos = (target_x, target_y)
        
        # Import CardAnimation here to avoid circular imports
        from .animation import CardAnimation
        
        # Create animation
        animation = CardAnimation(start_pos, end_pos, card_type, duration=0.6)
        self.animation_manager.add_card_animation(animation)
        
        # Store data for completion
        animation.card_idx = card_idx
        animation.card_type = card_type
    
    def complete_card_animation(self, animation):
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
            self.create_new_card_animation(animation.card_idx, new_card)
        else:
            # Remove card if deck is empty
            self.available_cards.pop(animation.card_idx)
            
        print(f"Drew card: {animation.card_type}")
        
        # Check if turn should end
        if self.cards_drawn_this_turn >= self.max_cards_per_turn:
            self.end_turn()
    
    def create_new_card_animation(self, card_idx: int, card_type):
        """Create animation for new card appearing in available cards"""
        import time
        
        # Calculate final position in available cards area
        card_height = 60
        card_spacing = 10
        end_x = self.available_cards_rect.x + 10
        end_y = self.available_cards_rect.y + 60 + card_idx * (card_height + card_spacing)
        end_pos = (end_x, end_y)
        
        # Start from deck position (bottom of available cards)
        deck_idx = len(self.available_cards) - 1
        deck_y = self.available_cards_rect.y + 60 + deck_idx * (card_height + card_spacing)
        start_x = self.available_cards_rect.x + 10
        start_y = deck_y
        start_pos = (start_x, start_y)
        
        # Set deck animation timing
        self.animation_manager.set_deck_animation_start(time.time())
        
        # Import CardAnimation here to avoid circular imports
        from .animation import CardAnimation
        
        # Create animation
        animation = CardAnimation(start_pos, end_pos, card_type, duration=0.4)
        self.animation_manager.add_new_card_animation(animation)
            
    def handle_claim_route(self):
        """Handle route claiming"""
        if self.selected_route_idx is None or self.cards_drawn_this_turn > 0:
            return
            
        current_player = self.game_state.get_current_player()
        if not current_player:
            return
            
        route = self.game_state.routes[self.selected_route_idx]
        gate_type_str = route['gate']
        required_cards = route['length']
        
        # Convert string to GateType enum
        from ..game import GateType
        gate_type = GateType(gate_type_str)
        
        if current_player.hand.get(gate_type, 0) >= required_cards:
            # Create route ID string
            route_id = f"{route['from']}-{route['to']}-{gate_type_str}"
            
            current_player.claim_route(gate_type, required_cards, route_id)
            route['claimed_by'] = current_player.name
            
            if self.audio_manager:
                self.audio_manager.play_sound_effect("mouse_click")
            
            print(f"Claimed route: {route['from']} -> {route['to']}")
            self.selected_route_idx = None
        else:
            print(f"Not enough {gate_type_str} cards!")
    
    def end_turn(self):
        """End current player's turn"""
        self.cards_drawn_this_turn = 0
        self.selected_route_idx = None
        self.game_state.next_turn()
        print(f"Turn ended. Now {self.game_state.get_current_player().name}'s turn")
    
    def draw_missions(self):
        """Draw mission cards for selection"""
        if self.cards_drawn_this_turn > 0:
            print("Cannot draw missions after drawing cards this turn")
            return
            
        if len(self.game_state.mission_deck) == 0:
            print("No missions left in deck")
            return
            
        # Draw 3 mission cards
        self.available_missions = []
        for _ in range(min(3, len(self.game_state.mission_deck))):
            self.available_missions.append(self.game_state.mission_deck.pop())
            
        self.selected_missions = []
        self.mission_selection_active = True
        print("Mission selection started. Choose missions to keep.")
        
    def confirm_mission_selection(self):
        """Confirm selected missions"""
        if len(self.selected_missions) == 0:
            print("Must select at least 1 mission")
            return
            
        current_player = self.game_state.get_current_player()
        if current_player:
            for mission in self.selected_missions:
                current_player.add_mission(mission)
                
            # Return unselected missions to deck
            for mission in self.available_missions:
                if mission not in self.selected_missions:
                    self.game_state.mission_deck.append(mission)
                    
        self.mission_selection_active = False
        self.available_missions = []
        self.selected_missions = []
        print("Mission selection completed")
        
    def cancel_mission_selection(self):
        """Cancel mission selection"""
        # Return all missions to deck
        for mission in self.available_missions:
            self.game_state.mission_deck.append(mission)
            
        self.mission_selection_active = False
        self.available_missions = []
        self.selected_missions = []
        print("Mission selection cancelled")
    
    def handle_mission_selection_click(self, pos: Tuple[int, int]):
        """Handle clicks during mission selection"""
        if not self.mission_selection_active:
            return
            
        # Check if clicking on mission cards in sidebar
        y_offset = 65 + 5 * 22  # After title lines
        card_height = 80
        card_spacing = 10
        card_width = self.sidebar_rect.width - 30
        
        for i, mission in enumerate(self.available_missions):
            card_x = self.sidebar_rect.x + 15
            card_y = self.sidebar_rect.y + y_offset
            card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
            
            if card_rect.collidepoint(pos):
                # Toggle mission selection
                if mission in self.selected_missions:
                    self.selected_missions.remove(mission)
                else:
                    if len(self.selected_missions) < 3:
                        self.selected_missions.append(mission)
                return
                
            y_offset += card_height + card_spacing
    
    def draw(self) -> None:
        background_color = tuple(self.colors['ui_colors']['background']['rgb'])
        self.screen.fill(background_color)
        
        # Draw all panels
        panel_kwargs = {
            'selected_route_idx': self.selected_route_idx,
            'hovered_route_idx': self.hovered_route_idx,
            'available_cards': self.available_cards,
            'cards_drawn_this_turn': self.cards_drawn_this_turn,
            'max_cards_per_turn': self.max_cards_per_turn,
            'animation_manager': self.animation_manager,
            'mission_selection_active': self.mission_selection_active,
            'available_missions': self.available_missions,
            'selected_missions': self.selected_missions
        }
        
        for panel in self.panels.values():
            panel.draw(self.screen, self.game_state, **panel_kwargs)
        
        # Draw animated cards on top
        self.draw_animated_cards()
        
        pygame.display.flip()
    
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
            
        # Draw new cards appearing in available cards area
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
            
        # Update new card animations (appearing in available cards)
        completed_new_animations = []
        for animation in self.animation_manager.new_card_animations:
            if animation.is_finished():
                completed_new_animations.append(animation)
                
        # Remove completed new card animations
        for animation in completed_new_animations:
            self.animation_manager.new_card_animations.remove(animation)
            self.animation_manager.clear_deck_animation_start()
    
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

def main():
    game_window = GameWindow()
    game_window.run()

if __name__ == "__main__":
    main() 