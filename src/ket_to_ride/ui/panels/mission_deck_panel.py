import pygame
import os
from typing import Tuple, Optional, Dict, Any
from .base_panel import BasePanel

class MissionDeckPanel(BasePanel):
    """Panel for displaying and interacting with the mission deck"""
    
    def __init__(self, rect: pygame.Rect, colors: Dict[str, Any], fonts: Dict[str, pygame.font.Font]):
        super().__init__(rect, colors, fonts)
        self.card_area_color = tuple(colors['ui_colors']['card_area']['rgb'])
        self.mission_back_image = None
        self.load_mission_back_image()
        
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
    
    def _handle_click_internal(self, pos: Tuple[int, int], game_state, **kwargs) -> Optional[str]:
        """Handle clicks on the mission deck"""
        # Check if clicking on the mission deck card
        card_width = self.rect.width - 20
        card_height = 80
        card_x = self.rect.x + 10
        card_y = self.rect.y + 55
        card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
        
        if card_rect.collidepoint(pos) and len(game_state.mission_deck) > 0:
            return "draw_missions"
            
        return None
    
    def draw(self, surface: pygame.Surface, game_state, **kwargs):
        """Draw the mission deck panel"""
        # Draw panel background
        pygame.draw.rect(surface, self.card_area_color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, 3)
        
        # Add header accent
        header_rect = pygame.Rect(self.rect.x + 3, self.rect.y + 3,
                                 self.rect.width - 6, 30)
        pygame.draw.rect(surface, self.accent_color, header_rect)
        
        # Draw title
        title_text = self.fonts['small_font'].render("Mission Cards", True, self.text_color)
        title_rect = title_text.get_rect(center=(header_rect.centerx, header_rect.centery))
        surface.blit(title_text, title_rect)
        
        # Draw mission deck count
        deck_count_text = f"Deck: {len(game_state.mission_deck)}"
        deck_count_surface = self.fonts['small_font'].render(deck_count_text, True, self.text_color)
        surface.blit(deck_count_surface, (self.rect.x + 10, self.rect.y + 35))
        
        # Draw mission deck card (clickable)
        card_width = self.rect.width - 20
        card_height = 80
        card_x = self.rect.x + 10
        card_y = self.rect.y + 55
        
        if len(game_state.mission_deck) > 0:
            card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
            
            # Draw card shadow
            shadow_rect = pygame.Rect(card_rect.x + 2, card_rect.y + 2, card_rect.width, card_rect.height)
            pygame.draw.rect(surface, (0, 0, 0, 80), shadow_rect)
            
            # Draw mission card back
            if self.mission_back_image:
                # Scale the image to fit the card
                scaled_image = pygame.transform.scale(self.mission_back_image, (card_rect.width, card_rect.height))
                surface.blit(scaled_image, card_rect)
            else:
                # Fallback to colored rectangle
                pygame.draw.rect(surface, (150, 100, 50), card_rect)
                
            # Draw border
            pygame.draw.rect(surface, self.border_color, card_rect, 2)
            
            # Draw "MISSIONS" text
            mission_text = self.fonts['small_font'].render("MISSIONS", True, self.text_color)
            text_rect = mission_text.get_rect(center=card_rect.center)
            surface.blit(mission_text, text_rect)
            
            # Add click hint
            hint_text = "Click to draw"
            hint_surface = self.fonts['small_font'].render(hint_text, True, self.text_color)
            hint_rect = hint_surface.get_rect(center=(card_rect.centerx, card_rect.bottom - 15))
            surface.blit(hint_surface, hint_rect)
        else:
            # Empty deck
            empty_text = "No missions left"
            empty_surface = self.fonts['small_font'].render(empty_text, True, self.text_color)
            empty_rect = empty_surface.get_rect(center=(self.rect.centerx, card_y + card_height // 2))
            surface.blit(empty_surface, empty_rect) 