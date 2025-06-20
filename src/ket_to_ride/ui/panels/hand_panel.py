import pygame
from typing import Tuple, Optional, Dict, Any
from .base_panel import BasePanel
from ...game import GateType

class HandPanel(BasePanel):
    """Panel for displaying the player's hand"""
    
    def __init__(self, rect: pygame.Rect, colors: Dict[str, Any], fonts: Dict[str, pygame.font.Font], card_renderer):
        super().__init__(rect, colors, fonts)
        self.card_renderer = card_renderer
        self.card_area_color = tuple(colors['ui_colors']['card_area']['rgb'])
        
    def draw(self, surface: pygame.Surface, game_state, **kwargs):
        """Draw the hand panel"""
        current_player = game_state.get_current_player()
        if not current_player:
            return
            
        # Draw panel background
        pygame.draw.rect(surface, self.card_area_color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, 3)
        
        # Header
        header_rect = pygame.Rect(self.rect.x + 3, self.rect.y + 3,
                                 self.rect.width - 6, 35)
        pygame.draw.rect(surface, self.accent_color, header_rect)
        
        title = f"{current_player.name}'s Hand"
        title_text = self.fonts['font'].render(title, True, self.text_color)
        title_rect = title_text.get_rect(center=header_rect.center)
        surface.blit(title_text, title_rect)
        
        # Draw hand cards
        x = self.rect.x + 20
        y = self.rect.y + 50
        
        for gate_type, count in current_player.hand.items():
            if count > 0:
                card_rect = pygame.Rect(x, y, 90, 60)
                self.card_renderer.draw_card_with_image_support(
                    surface, card_rect, gate_type, True, "", "", False
                )
                
                # Draw count
                count_text = f"x{count}"
                count_surface = self.fonts['small_font'].render(count_text, True, self.text_color)
                count_rect = count_surface.get_rect(center=(card_rect.centerx, card_rect.bottom + 10))
                surface.blit(count_surface, count_rect)
                
                x += 102 