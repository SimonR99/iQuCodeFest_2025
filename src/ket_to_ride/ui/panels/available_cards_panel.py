import pygame
import math
import time
from typing import Tuple, Optional, Dict, Any, List
from .base_panel import BasePanel
from ...game import GateType

class AvailableCardsPanel(BasePanel):
    """Panel for displaying and selecting available gate cards"""
    
    def __init__(self, rect: pygame.Rect, colors: Dict[str, Any], fonts: Dict[str, pygame.font.Font], card_renderer):
        super().__init__(rect, colors, fonts)
        self.card_renderer = card_renderer
        self.card_area_color = tuple(colors['ui_colors']['card_area']['rgb'])
        
    def draw(self, surface: pygame.Surface, game_state, **kwargs):
        """Draw the available cards panel"""
        available_cards = kwargs.get('available_cards', [])
        cards_drawn_this_turn = kwargs.get('cards_drawn_this_turn', 0)
        max_cards_per_turn = kwargs.get('max_cards_per_turn', 2)
        animation_manager = kwargs.get('animation_manager')
        
        # Draw panel background
        pygame.draw.rect(surface, self.card_area_color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, 3)
        
        # Add header accent
        header_rect = pygame.Rect(self.rect.x + 3, self.rect.y + 3,
                                 self.rect.width - 6, 40)
        pygame.draw.rect(surface, self.accent_color, header_rect)
        
        # Draw title
        title_text = self.fonts['font'].render("Gate Cards", True, self.text_color)
        title_rect = title_text.get_rect(center=(header_rect.centerx, header_rect.centery - 5))
        surface.blit(title_text, title_rect)
        
        # Draw card drawing info
        current_player = game_state.get_current_player()
        if current_player:
            info_text = f"Cards drawn: {cards_drawn_this_turn}/{max_cards_per_turn}"
            info_surface = self.fonts['small_font'].render(info_text, True, self.text_color)
            surface.blit(info_surface, (self.rect.x + 10, self.rect.y + 35))
        
        # Draw available cards
        self._draw_available_cards(surface, available_cards, cards_drawn_this_turn, 
                                 max_cards_per_turn, animation_manager)
    
    def _draw_available_cards(self, surface: pygame.Surface, available_cards: List, 
                            cards_drawn_this_turn: int, max_cards_per_turn: int, animation_manager):
        """Draw the available cards vertically"""
        card_width = self.rect.width - 20
        card_height = 60
        card_spacing = 10
        start_x = self.rect.x + 10
        start_y = self.rect.y + 60
        
        for i, card in enumerate(available_cards):
            # Skip if card is being animated
            if animation_manager and animation_manager.is_card_being_animated(i):
                continue
                
            y = start_y + i * (card_height + card_spacing)
            card_rect = pygame.Rect(start_x, y, card_width, card_height)
            
            # Skip if card would be outside the panel
            if y + card_height > self.rect.bottom - 10:
                break
            
            # Handle deck special case
            if card == "DECK":
                can_draw = cards_drawn_this_turn < max_cards_per_turn
                
                # Add visual effect if deck is being used
                if (animation_manager and animation_manager.deck_animation_start and 
                    time.time() - animation_manager.deck_animation_start < 0.4):
                    pulse = abs(math.sin((time.time() - animation_manager.deck_animation_start) * 10)) * 0.3 + 0.7
                    original_color = self.colors['gate_colors']['DECK']['rgb']
                    pulse_color = tuple(int(c * pulse) for c in original_color)
                    # Temporarily modify color for pulse effect
                    temp_colors = self.colors.copy()
                    temp_colors['gate_colors']['DECK']['rgb'] = pulse_color
                    self.card_renderer.colors = temp_colors
                    self.card_renderer.draw_card_with_image_support(surface, card_rect, "DECK", can_draw, "", "", False)
                    self.card_renderer.colors = self.colors  # Restore
                else:
                    self.card_renderer.draw_card_with_image_support(surface, card_rect, "DECK", can_draw, "", "", False)
            else:
                can_draw = cards_drawn_this_turn < max_cards_per_turn
                self.card_renderer.draw_card_with_image_support(surface, card_rect, card, can_draw, "", "", False)
    
    def _handle_click_internal(self, pos: Tuple[int, int], game_state, **kwargs) -> Optional[str]:
        """Handle clicks on available cards"""
        available_cards = kwargs.get('available_cards', [])
        card_idx = self._get_clicked_card(pos, available_cards)
        if card_idx is not None:
            return f"draw_card:{card_idx}"
        return None
    
    def _get_clicked_card(self, pos: Tuple[int, int], available_cards: List) -> Optional[int]:
        """Determine which available card was clicked"""
        if not available_cards:
            return None
            
        card_height = 60
        card_spacing = 10
        start_x = self.rect.x + 10
        start_y = self.rect.y + 60
        
        relative_x = pos[0] - start_x
        relative_y = pos[1] - start_y
        
        # Check if within card area horizontally
        card_width = self.rect.width - 20
        if relative_x < 0 or relative_x > card_width:
            return None
            
        # Calculate which card was clicked
        for i in range(len(available_cards)):
            card_top = i * (card_height + card_spacing)
            card_bottom = card_top + card_height
            
            # Skip if card would be outside the panel
            if start_y + card_bottom > self.rect.bottom - 10:
                break
            
            if card_top <= relative_y <= card_bottom:
                return i
                
        return None 