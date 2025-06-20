import pygame
from typing import Tuple, Optional, Dict, Any
from abc import ABC, abstractmethod

class BasePanel(ABC):
    """Base class for all UI panels"""
    
    def __init__(self, rect: pygame.Rect, colors: Dict[str, Any], fonts: Dict[str, pygame.font.Font]):
        self.rect = rect
        self.colors = colors
        self.fonts = fonts
        
        # Common colors
        self.background_color = tuple(colors['ui_colors']['background']['rgb'])
        self.border_color = tuple(colors['ui_colors']['border']['rgb'])
        self.text_color = tuple(colors['ui_colors']['text']['rgb'])
        self.accent_color = tuple(colors['ui_colors']['accent']['rgb'])
        
    def update_rect(self, rect: pygame.Rect):
        """Update the panel's rectangle (for resizing)"""
        self.rect = rect
        
    @abstractmethod
    def draw(self, surface: pygame.Surface, game_state, **kwargs):
        """Draw the panel on the surface"""
        pass
        
    def handle_click(self, pos: Tuple[int, int], game_state, **kwargs) -> Optional[str]:
        """Handle mouse clicks. Returns action string if any."""
        if not self.rect.collidepoint(pos):
            return None
        return self._handle_click_internal(pos, game_state, **kwargs)
        
    def _handle_click_internal(self, pos: Tuple[int, int], game_state, **kwargs) -> Optional[str]:
        """Internal click handling - override in subclasses"""
        return None
        
    def handle_hover(self, pos: Tuple[int, int], game_state, **kwargs) -> Optional[Any]:
        """Handle mouse hover. Returns hover info if any."""
        if not self.rect.collidepoint(pos):
            return None
        return self._handle_hover_internal(pos, game_state, **kwargs)
        
    def _handle_hover_internal(self, pos: Tuple[int, int], game_state, **kwargs) -> Optional[Any]:
        """Internal hover handling - override in subclasses"""
        return None 