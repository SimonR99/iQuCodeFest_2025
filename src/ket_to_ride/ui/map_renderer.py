import pygame
import json
import math
from typing import Dict, List, Tuple, Optional

class MapRenderer:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.universities = {}
        self.routes = []
        self.map_settings = {}
        self.font = None
        self.load_config()
        
    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                self.universities = config.get('universities', {})
                self.routes = config.get('routes', [])
                self.map_settings = config.get('map_settings', {})
        except FileNotFoundError:
            print(f"Config file not found: {self.config_path}")
        except json.JSONDecodeError:
            print(f"Invalid JSON in config file: {self.config_path}")
    
    def initialize_font(self, size: int = None):
        if size is None:
            size = self.map_settings.get('font_size', 12)
        self.font = pygame.font.Font(None, size)
    
    def scale_positions(self, map_rect: pygame.Rect) -> Dict[str, Tuple[int, int]]:
        scaled_positions = {}
        
        if not self.universities:
            return scaled_positions
            
        # Find bounds of university positions
        positions = [uni['position'] for uni in self.universities.values()]
        min_x = min(pos[0] for pos in positions)
        max_x = max(pos[0] for pos in positions)
        min_y = min(pos[1] for pos in positions)
        max_y = max(pos[1] for pos in positions)
        
        # Calculate scaling factors with padding
        padding = 50
        scale_x = (map_rect.width - 2 * padding) / (max_x - min_x) if max_x != min_x else 1
        scale_y = (map_rect.height - 2 * padding) / (max_y - min_y) if max_y != min_y else 1
        scale = min(scale_x, scale_y)
        
        # Calculate offset to center the map
        offset_x = map_rect.x + padding + (map_rect.width - 2 * padding - (max_x - min_x) * scale) // 2
        offset_y = map_rect.y + padding + (map_rect.height - 2 * padding - (max_y - min_y) * scale) // 2
        
        for uni_id, uni_data in self.universities.items():
            x, y = uni_data['position']
            scaled_x = int(offset_x + (x - min_x) * scale)
            scaled_y = int(offset_y + (y - min_y) * scale)
            scaled_positions[uni_id] = (scaled_x, scaled_y)
            
        return scaled_positions
    
    def draw_route(self, surface: pygame.Surface, start_pos: Tuple[int, int], 
                   end_pos: Tuple[int, int], route_data: Dict):
        gate = route_data['gate']
        length = route_data['length']
        claimed_by = route_data.get('claimed_by')
        
        # Get route color based on gate type or claim status
        if claimed_by:
            color = (150, 150, 150)  # Gray for claimed routes
        else:
            color = self.map_settings.get('gate_colors', {}).get(gate, (255, 255, 255))
        
        # Draw route line
        route_width = self.map_settings.get('route_width', 3)
        pygame.draw.line(surface, color, start_pos, end_pos, route_width)
        
        # Calculate midpoint for gate label
        mid_x = (start_pos[0] + end_pos[0]) // 2
        mid_y = (start_pos[1] + end_pos[1]) // 2
        
        # Draw gate label background
        if self.font:
            gate_text = f"{gate}({length})"
            text_surface = self.font.render(gate_text, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(mid_x, mid_y))
            
            # Draw background for better readability
            bg_rect = text_rect.inflate(6, 4)
            pygame.draw.rect(surface, (0, 0, 0, 128), bg_rect)
            pygame.draw.rect(surface, color, bg_rect, 1)
            
            surface.blit(text_surface, text_rect)
    
    def draw_university(self, surface: pygame.Surface, position: Tuple[int, int], 
                       uni_data: Dict, uni_id: str):
        x, y = position
        radius = self.map_settings.get('university_radius', 15)
        color = uni_data.get('color', [100, 100, 100])
        
        # Draw university circle
        pygame.draw.circle(surface, color, (x, y), radius)
        pygame.draw.circle(surface, (255, 255, 255), (x, y), radius, 2)
        
        # Draw university name
        if self.font:
            name_text = self.font.render(uni_id, True, (255, 255, 255))
            text_rect = name_text.get_rect(center=(x, y + radius + 15))
            
            # Draw background for better readability
            bg_rect = text_rect.inflate(4, 2)
            pygame.draw.rect(surface, (0, 0, 0, 128), bg_rect)
            
            surface.blit(name_text, text_rect)
    
    def draw_map(self, surface: pygame.Surface, map_rect: pygame.Rect):
        if not self.font:
            self.initialize_font()
            
        # Clear map area
        bg_color = self.map_settings.get('background_color', [30, 40, 50])
        pygame.draw.rect(surface, bg_color, map_rect)
        pygame.draw.rect(surface, (100, 100, 120), map_rect, 2)
        
        if not self.universities:
            # Draw placeholder text if no universities loaded
            if self.font:
                text = self.font.render("University Map - Loading...", True, (255, 255, 255))
                text_rect = text.get_rect(center=map_rect.center)
                surface.blit(text, text_rect)
            return
        
        # Get scaled positions
        scaled_positions = self.scale_positions(map_rect)
        
        # Draw routes first (so they appear behind universities)
        for route in self.routes:
            from_uni = route['from']
            to_uni = route['to']
            
            if from_uni in scaled_positions and to_uni in scaled_positions:
                start_pos = scaled_positions[from_uni]
                end_pos = scaled_positions[to_uni]
                self.draw_route(surface, start_pos, end_pos, route)
        
        # Draw universities on top of routes
        for uni_id, uni_data in self.universities.items():
            if uni_id in scaled_positions:
                position = scaled_positions[uni_id]
                self.draw_university(surface, position, uni_data, uni_id)
    
    def get_university_at_position(self, map_rect: pygame.Rect, 
                                  mouse_pos: Tuple[int, int]) -> Optional[str]:
        scaled_positions = self.scale_positions(map_rect)
        radius = self.map_settings.get('university_radius', 15)
        
        for uni_id, pos in scaled_positions.items():
            distance = math.sqrt((mouse_pos[0] - pos[0])**2 + (mouse_pos[1] - pos[1])**2)
            if distance <= radius:
                return uni_id
        return None