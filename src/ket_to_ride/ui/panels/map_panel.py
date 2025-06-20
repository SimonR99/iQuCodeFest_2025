import pygame
import os
from typing import Tuple, Optional, Dict, Any
from .base_panel import BasePanel

class MapPanel(BasePanel):
    """Panel for displaying the game map with routes and universities"""
    
    def __init__(self, rect: pygame.Rect, colors: Dict[str, Any], fonts: Dict[str, pygame.font.Font], map_renderer):
        super().__init__(rect, colors, fonts)
        self.map_renderer = map_renderer
        self.background_image = None
        self.map_color = tuple(colors['ui_colors']['map_area']['rgb'])
        self.load_background_image()
        
    def load_background_image(self):
        """Load the map background image"""
        try:
            image_path = os.path.join("assets", "map.jpg")
            if os.path.exists(image_path):
                self.background_image = pygame.image.load(image_path)
            else:
                self.background_image = None
        except Exception as e:
            print(f"Error loading background image: {e}")
            self.background_image = None
            
    def draw(self, surface: pygame.Surface, game_state, **kwargs):
        """Draw the map panel"""
        selected_route_idx = kwargs.get('selected_route_idx')
        selected_gate = kwargs.get('selected_gate')
        selected_gate_index = kwargs.get('selected_gate_index')
        hovered_route_idx = kwargs.get('hovered_route_idx')
        
        # Draw background image in map area if available
        if self.background_image:
            scaled_bg = pygame.transform.scale(self.background_image, 
                                             (self.rect.width, self.rect.height))
            surface.blit(scaled_bg, self.rect.topleft)
            
            # Add subtle overlay to make routes visible
            overlay = pygame.Surface((self.rect.width, self.rect.height))
            overlay.set_alpha(60)
            overlay.fill(self.map_color)
            surface.blit(overlay, self.rect.topleft)
        else:
            pygame.draw.rect(surface, self.map_color, self.rect)
        
        # Draw border
        pygame.draw.rect(surface, self.border_color, self.rect, 3)
        
        # Show selected route or hovered route for highlighting
        # If we have a selected route with a specific gate, use that; otherwise fall back to hover
        if selected_route_idx is not None:
            highlight_route = selected_route_idx
            highlight_gate = selected_gate
            highlight_gate_index = selected_gate_index
        else:
            highlight_route = hovered_route_idx
            highlight_gate = None  # Hover doesn't specify a specific gate
            highlight_gate_index = None
            
        self.map_renderer.draw_map(surface, self.rect, highlight_route, highlight_gate, game_state, highlight_gate_index)
        
    def _handle_click_internal(self, pos: Tuple[int, int], game_state, **kwargs) -> Optional[str]:
        """Handle clicks on the map"""
        route_result = self.map_renderer.get_route_at_position(self.rect, pos, game_state)
        if route_result is not None:
            route_idx, selected_gate, gate_index = route_result
            route = game_state.routes[route_idx]
            
            # Check if this specific gate is claimable
            claimed_by = route.get('claimed_by', {})
            if isinstance(claimed_by, dict):
                # New format: check if this specific gate instance is unclaimed
                gate_claimed_by = claimed_by.get(selected_gate)
                if isinstance(gate_claimed_by, list):
                    # Multiple identical gates - check the specific instance
                    if gate_index < len(gate_claimed_by) and gate_claimed_by[gate_index] is None:
                        return f"route_selected:{route_idx}:{selected_gate}:{gate_index}"
                else:
                    # Single gate instance
                    if gate_claimed_by is None:
                        return f"route_selected:{route_idx}:{selected_gate}:{gate_index}"
            else:
                # Old format: check if route is unclaimed
                if claimed_by is None:
                    return f"route_selected:{route_idx}:{selected_gate}:{gate_index}"
        return None
        
    def _handle_hover_internal(self, pos: Tuple[int, int], game_state, **kwargs) -> Optional[Any]:
        """Handle hover on the map"""
        route_result = self.map_renderer.get_route_at_position(self.rect, pos, game_state)
        if route_result is not None:
            route_idx, selected_gate, gate_index = route_result
            return route_idx  # For now, just return the route index for hover highlighting
        return None 