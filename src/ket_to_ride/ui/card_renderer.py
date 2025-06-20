import os
import pygame
from typing import Dict, Tuple, Optional


class CardRenderer:
    """Handles rendering of cards with image support and color fallbacks"""
    
    def __init__(self, colors_config: Dict, fonts: Dict[str, pygame.font.Font]):
        """
        Initialize the card renderer
        
        Args:
            colors_config: Configuration dictionary containing gate colors and UI colors
            fonts: Dictionary containing font objects (large_font, font, etc.)
        """
        self.colors = colors_config
        self.fonts = fonts
        
    def draw_card_with_image_support(self, surface: pygame.Surface, card_rect: pygame.Rect, 
                                   gate_type, can_draw: bool = True, text: str = "", subtext: str = "", 
                                   show_text: bool = True) -> None:
        """
        Draw a card with optional image support and colored border
        
        Args:
            surface: Pygame surface to draw on
            card_rect: Rectangle defining card position and size
            gate_type: Type of gate (GateType enum or "DECK")
            can_draw: Whether the card can be drawn (affects appearance)
            text: Main text to display on card
            subtext: Secondary text to display on card
            show_text: Whether to display text on the card
        """
        if gate_type == "DECK":
            self._draw_deck_card(surface, card_rect, can_draw, text, subtext, show_text)
        else:
            self._draw_gate_card(surface, card_rect, gate_type, can_draw, text, subtext, show_text)
    
    def _draw_deck_card(self, surface: pygame.Surface, card_rect: pygame.Rect, 
                       can_draw: bool, text: str, subtext: str, show_text: bool) -> None:
        """Draw a deck card"""
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
        
        # Draw text if provided and enabled
        if show_text:
            self._draw_card_text(surface, card_rect, text, subtext, can_draw)
    
    def _draw_gate_card(self, surface: pygame.Surface, card_rect: pygame.Rect, 
                       gate_type, can_draw: bool, text: str, subtext: str, show_text: bool) -> None:
        """Draw a gate card"""
        # Get gate configuration
        gate_config = self.colors['gate_colors'].get(
            gate_type.value if hasattr(gate_type, 'value') else str(gate_type), {}
        )
        
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
        
        # Draw text if provided and enabled
        if show_text:
            self._draw_card_text(surface, card_rect, text, subtext, can_draw)
    
    def _draw_color_card(self, surface: pygame.Surface, card_rect: pygame.Rect, 
                        gate_config: Dict, can_draw: bool) -> None:
        """Helper to draw a card with color background"""
        color = tuple(gate_config.get('rgb', [150, 150, 150]))
        if not can_draw:
            color = tuple(c // 2 for c in color)
        
        pygame.draw.rect(surface, color, card_rect)
        border_color = (255, 255, 255) if can_draw else (128, 128, 128)
        pygame.draw.rect(surface, border_color, card_rect, 2)
    
    def _draw_card_text(self, surface: pygame.Surface, card_rect: pygame.Rect, 
                       text: str, subtext: str, can_draw: bool) -> None:
        """Draw text on a card"""
        # Draw main text if provided
        if text:
            text_color = (0, 0, 0) if can_draw else (64, 64, 64)
            card_text = self.fonts['large_font'].render(text, True, text_color)
            text_rect = card_text.get_rect(center=(card_rect.centerx, card_rect.centery - 12))
            surface.blit(card_text, text_rect)
            
        # Draw subtext if provided
        if subtext:
            text_color = (0, 0, 0) if can_draw else (64, 64, 64)
            sub_surface = self.fonts['font'].render(subtext, True, text_color)
            sub_rect = sub_surface.get_rect(center=(card_rect.centerx, card_rect.centery + 18))
            surface.blit(sub_surface, sub_rect) 