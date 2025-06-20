import pygame
import json
import math
import os
from typing import Dict, List, Tuple, Optional

class MapRenderer:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.universities = {}
        self.routes = []
        self.map_settings = {}
        self.font = None
        self.rail_images = {}  # Cache for rail images
        self.colors_config = None
        self.load_config()
        self.load_rail_images()
        
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
    
    def load_rail_images(self):
        """Load rail images and colors from colors config"""
        try:
            colors_path = os.path.join(os.path.dirname(self.config_path), 'colors.json')
            with open(colors_path, 'r') as f:
                self.colors_config = json.load(f)
                
            # Load rail images
            rail_images_config = self.colors_config.get('rail_images', {})
            for gate_type, config in rail_images_config.items():
                image_path = config.get('image_path')
                if image_path and os.path.exists(image_path):
                    try:
                        self.rail_images[gate_type] = pygame.image.load(image_path)
                    except Exception as e:
                        print(f"Could not load rail image {image_path}: {e}")
        except Exception as e:
            print(f"Could not load rail images config: {e}")
    
    def initialize_font(self, size: int = None):
        if size is None:
            size = self.map_settings.get('font_size', 20)  # Increased from 12
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
                   end_pos: Tuple[int, int], route_data: Dict, offset: int = 0, highlighted: bool = False, player_color: Optional[Tuple[int, int, int]] = None):
        gate = route_data['gate']
        length = route_data['length']
        claimed_by = route_data.get('claimed_by')
        
        # Get route color based on claim status
        if claimed_by and player_color:
            color = player_color  # Use player's color for claimed routes
        elif highlighted:
            color = (255, 255, 0)   # Yellow for highlighted routes
        else:
            color = self.get_gate_color(gate)
        
        # Calculate perpendicular offset for parallel routes
        if offset != 0:
            dx = end_pos[0] - start_pos[0]
            dy = end_pos[1] - start_pos[1]
            length_route = math.sqrt(dx*dx + dy*dy)
            if length_route > 0:
                # Perpendicular vector
                perp_x = -dy / length_route * offset
                perp_y = dx / length_route * offset
                start_pos = (int(start_pos[0] + perp_x), int(start_pos[1] + perp_y))
                end_pos = (int(end_pos[0] + perp_x), int(end_pos[1] + perp_y))
        
        # Draw route as individual train car segments (like Ticket to Ride)
        self.draw_route_segments(surface, start_pos, end_pos, length, color, gate, claimed_by, player_color)
        
    def draw_route_segments(self, surface: pygame.Surface, start_pos: Tuple[int, int], 
                           end_pos: Tuple[int, int], length: int, color: Tuple[int, int, int], gate: str, 
                           claimed_by: Optional[str] = None, player_color: Optional[Tuple[int, int, int]] = None):
        """Draw route as individual train car segments covering the full route distance"""
        # Calculate route direction and length
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        route_length = math.sqrt(dx*dx + dy*dy)
        
        if route_length == 0 or length == 0:
            return
            
        # Unit vector along the route
        unit_x = dx / route_length
        unit_y = dy / route_length
        
        # Calculate segment dimensions to cover the entire route
        # Each segment gets an equal portion of the total route length
        segment_spacing = 3  # Small gap between segments
        total_spacing = (length - 1) * segment_spacing
        available_length = route_length - total_spacing
        
        # Each segment gets equal length from available space
        segment_length = available_length / length
        
        # Minimum segment length for visibility
        if segment_length < 8:
            segment_length = 8
            segment_spacing = max(1, (route_length - length * segment_length) / max(1, length - 1))
        
        # Segment width (perpendicular to route)
        segment_width = 14
        
        # Start from the beginning of the route
        current_x = start_pos[0]
        current_y = start_pos[1]
        
        # Draw each train car segment
        for i in range(length):
            # Calculate segment position
            segment_start_x = current_x
            segment_start_y = current_y
            segment_end_x = current_x + unit_x * segment_length
            segment_end_y = current_y + unit_y * segment_length
            
            # Draw train car as rounded rectangle
            # Show label only on first segment, but ownership circles on all segments
            self.draw_train_car(surface, 
                              (segment_start_x, segment_start_y), 
                              (segment_end_x, segment_end_y), 
                              segment_width, color, gate, i == 0, claimed_by, player_color)
            
            # Move to next segment position (including spacing)
            current_x += unit_x * (segment_length + segment_spacing)
            current_y += unit_y * (segment_length + segment_spacing)
    
    def draw_train_car(self, surface: pygame.Surface, start_pos: Tuple[float, float], 
                       end_pos: Tuple[float, float], width: float, color: Tuple[int, int, int], 
                       gate: str, show_label: bool = False, claimed_by: Optional[str] = None, 
                       player_color: Optional[Tuple[int, int, int]] = None):
        """Draw an individual train car segment with optional image"""
        # Calculate perpendicular vector for width
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        length = math.sqrt(dx*dx + dy*dy)
        
        if length == 0:
            return
            
        # Unit perpendicular vector
        perp_x = -dy / length * width / 2
        perp_y = dx / length * width / 2
        
        # Calculate the four corners of the train car
        corners = [
            (int(start_pos[0] + perp_x), int(start_pos[1] + perp_y)),
            (int(start_pos[0] - perp_x), int(start_pos[1] - perp_y)),
            (int(end_pos[0] - perp_x), int(end_pos[1] - perp_y)),
            (int(end_pos[0] + perp_x), int(end_pos[1] + perp_y))
        ]
        
        # Check if we have a rail image for this gate type
        rail_image = self.rail_images.get(gate)
        if rail_image:
            try:
                # Make sure image has per-pixel alpha
                rail_image = rail_image.convert_alpha()
                
                # Scale image to fit the train car
                car_rect = pygame.Rect(
                    min(corner[0] for corner in corners),
                    min(corner[1] for corner in corners),
                    int(length), int(width)
                )
                scaled_image = pygame.transform.scale(rail_image, (car_rect.width, car_rect.height))
                
                # Rotate image to align with route direction
                angle = math.degrees(math.atan2(dy, dx))
                
                # Create a transparent surface for rotation to avoid black background
                temp_surface = pygame.Surface((car_rect.width * 2, car_rect.height * 2), pygame.SRCALPHA)
                temp_rect = scaled_image.get_rect(center=temp_surface.get_rect().center)
                temp_surface.blit(scaled_image, temp_rect)
                
                # Rotate with proper alpha handling
                rotated_image = pygame.transform.rotate(temp_surface, -angle)
                
                # Blit the rotated image
                center_x = (start_pos[0] + end_pos[0]) / 2
                center_y = (start_pos[1] + end_pos[1]) / 2
                image_rect = rotated_image.get_rect(center=(int(center_x), int(center_y)))
                surface.blit(rotated_image, image_rect)
                
                # Draw colored border around the original train car shape
                pygame.draw.polygon(surface, color, corners, 2)
            except Exception as e:
                print(f"Error drawing rail image for {gate}: {e}")
                # Fallback to color
                pygame.draw.polygon(surface, color, corners)
                pygame.draw.polygon(surface, (255, 255, 255), corners, 2)
        else:
            # Draw with solid color (fallback)
            pygame.draw.polygon(surface, color, corners)
            pygame.draw.polygon(surface, (255, 255, 255), corners, 2)
        
        # Draw gate label on first segment
        if show_label and self.font:
            label_center_x = (start_pos[0] + end_pos[0]) / 2
            label_center_y = (start_pos[1] + end_pos[1]) / 2
            
            # Use larger font for better visibility
            gate_text = self.font.render(gate, True, (0, 0, 0))
            text_rect = gate_text.get_rect(center=(int(label_center_x), int(label_center_y)))
            
            # Draw background for better readability
            bg_rect = text_rect.inflate(4, 2)
            pygame.draw.rect(surface, (255, 255, 255, 200), bg_rect)
            
            surface.blit(gate_text, text_rect)
        
        # Draw player ownership circle if route is claimed (ALWAYS on top)
        if claimed_by and player_color:
            circle_center_x = int((start_pos[0] + end_pos[0]) / 2)
            circle_center_y = int((start_pos[1] + end_pos[1]) / 2)
            
            # Draw player color circle with border - make it larger and more visible
            circle_radius = 12
            # Draw outer white border first for better visibility
            pygame.draw.circle(surface, (255, 255, 255), (circle_center_x, circle_center_y), circle_radius + 2)
            pygame.draw.circle(surface, player_color, (circle_center_x, circle_center_y), circle_radius)
            pygame.draw.circle(surface, (0, 0, 0), (circle_center_x, circle_center_y), circle_radius, 2)
    
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
            text_rect = name_text.get_rect(center=(x, y + radius + 18))
            
            # Draw background for better readability
            bg_rect = text_rect.inflate(6, 4)
            pygame.draw.rect(surface, (0, 0, 0, 180), bg_rect)
            
            surface.blit(name_text, text_rect)
    
    def draw_map(self, surface: pygame.Surface, map_rect: pygame.Rect, highlighted_route_idx: Optional[int] = None, game_state=None):
        if not self.font:
            self.initialize_font()
            
        # Note: Background is now handled by the game window
        
        if not self.universities:
            # Draw placeholder text if no universities loaded
            if self.font:
                text = self.font.render("University Map - Loading...", True, (255, 255, 255))
                text_rect = text.get_rect(center=map_rect.center)
                surface.blit(text, text_rect)
            return
        
        # Get scaled positions
        scaled_positions = self.scale_positions(map_rect)
        
        # Group routes by city pairs to handle parallel routes
        route_groups = {}
        route_to_index = {}  # Map route to original index
        for i, route in enumerate(self.routes):
            from_uni = route['from']
            to_uni = route['to']
            
            # Create a consistent key regardless of direction
            key = tuple(sorted([from_uni, to_uni]))
            if key not in route_groups:
                route_groups[key] = []
            route_groups[key].append(route)
            route_to_index[id(route)] = i
        
        # Draw routes first (so they appear behind universities)
        for (uni1, uni2), routes_group in route_groups.items():
            if uni1 in scaled_positions and uni2 in scaled_positions:
                start_pos = scaled_positions[uni1]
                end_pos = scaled_positions[uni2]
                
                # If there's only one route, draw normally
                if len(routes_group) == 1:
                    route = routes_group[0]
                    route_idx = route_to_index[id(route)]
                    highlighted = (highlighted_route_idx == route_idx)
                    # Get player color if route is claimed
                    player_color = None
                    if route.get('claimed_by'):
                        player_color = self.get_player_color(route['claimed_by'], game_state)
                    # Make sure we draw in the correct direction
                    if route['from'] != uni1:
                        start_pos, end_pos = end_pos, start_pos
                    self.draw_route(surface, start_pos, end_pos, route, 0, highlighted, player_color)
                else:
                    # Multiple routes - draw them parallel
                    offset_distance = 25  # Distance between parallel routes (increased for visibility)
                    total_width = (len(routes_group) - 1) * offset_distance
                    start_offset = -total_width / 2
                    
                    for i, route in enumerate(routes_group):
                        route_idx = route_to_index[id(route)]
                        highlighted = (highlighted_route_idx == route_idx)
                        # Get player color if route is claimed
                        player_color = None
                        if route.get('claimed_by'):
                            player_color = self.get_player_color(route['claimed_by'], game_state)
                        offset = start_offset + i * offset_distance
                        # Make sure we draw in the correct direction
                        route_start, route_end = start_pos, end_pos
                        if route['from'] != uni1:
                            route_start, route_end = route_end, route_start
                        self.draw_route(surface, route_start, route_end, route, int(offset), highlighted, player_color)
        
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
    
    def get_route_at_position(self, map_rect: pygame.Rect, 
                             mouse_pos: Tuple[int, int]) -> Optional[int]:
        """Find which route (if any) is clicked by the mouse"""
        if not self.universities:
            return None
            
        scaled_positions = self.scale_positions(map_rect)
        click_tolerance = 15  # How close to route line to register click
        
        # Use absolute mouse position (don't convert to relative)
        absolute_pos = mouse_pos
        
        # Group routes by city pairs to handle parallel routes (same as in draw_map)
        route_groups = {}
        route_to_index = {}
        for i, route in enumerate(self.routes):
            from_uni = route['from']
            to_uni = route['to']
            
            # Create a consistent key regardless of direction
            key = tuple(sorted([from_uni, to_uni]))
            if key not in route_groups:
                route_groups[key] = []
            route_groups[key].append(route)
            route_to_index[id(route)] = i
        
        # Check each route group
        for (uni1, uni2), routes_group in route_groups.items():
            if uni1 in scaled_positions and uni2 in scaled_positions:
                base_start_pos = scaled_positions[uni1]
                base_end_pos = scaled_positions[uni2]
                
                # If there's only one route, test normally
                if len(routes_group) == 1:
                    route = routes_group[0]
                    # Adjust for route direction
                    start_pos, end_pos = base_start_pos, base_end_pos
                    if route['from'] != uni1:
                        start_pos, end_pos = end_pos, start_pos
                    
                    distance = self._point_to_line_distance(absolute_pos, start_pos, end_pos)
                    if distance <= click_tolerance:
                        return route_to_index[id(route)]
                else:
                    # Multiple routes - test each with its offset
                    offset_distance = 25
                    total_width = (len(routes_group) - 1) * offset_distance
                    start_offset = -total_width / 2
                    
                    for i, route in enumerate(routes_group):
                        offset = start_offset + i * offset_distance
                        
                        # Calculate offset positions
                        route_start, route_end = base_start_pos, base_end_pos
                        if route['from'] != uni1:
                            route_start, route_end = route_end, route_start
                        
                        # Apply perpendicular offset
                        dx = route_end[0] - route_start[0]
                        dy = route_end[1] - route_start[1]
                        length_route = math.sqrt(dx*dx + dy*dy)
                        if length_route > 0:
                            perp_x = -dy / length_route * offset
                            perp_y = dx / length_route * offset
                            offset_start = (int(route_start[0] + perp_x), int(route_start[1] + perp_y))
                            offset_end = (int(route_end[0] + perp_x), int(route_end[1] + perp_y))
                            
                            distance = self._point_to_line_distance(absolute_pos, offset_start, offset_end)
                            if distance <= click_tolerance:
                                return route_to_index[id(route)]
        
        return None
    
    def _point_to_line_distance(self, point: Tuple[int, int], 
                               line_start: Tuple[int, int], 
                               line_end: Tuple[int, int]) -> float:
        """Calculate minimum distance from a point to a line segment"""
        px, py = point
        x1, y1 = line_start
        x2, y2 = line_end
        
        # Vector from line start to end
        dx = x2 - x1
        dy = y2 - y1
        
        if dx == 0 and dy == 0:
            # Line is actually a point
            return math.sqrt((px - x1)**2 + (py - y1)**2)
        
        # Parameter t that represents position along line segment
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
        
        # Closest point on line segment
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        # Distance from point to closest point on line
        return math.sqrt((px - closest_x)**2 + (py - closest_y)**2)
    
    def get_gate_color(self, gate: str) -> Tuple[int, int, int]:
        """Get the color for a gate type from colors.json"""
        if self.colors_config and 'gate_colors' in self.colors_config:
            gate_config = self.colors_config['gate_colors'].get(gate, {})
            rgb = gate_config.get('rgb', [255, 255, 255])  # Default to white
            return tuple(rgb)
        else:
            # Fallback to map_settings if colors.json not available
            return tuple(self.map_settings.get('gate_colors', {}).get(gate, [255, 255, 255]))
    
    def get_player_color(self, player_name: str, game_state) -> Optional[Tuple[int, int, int]]:
        """Get player color by player name"""
        if game_state and hasattr(game_state, 'players'):
            for player in game_state.players:
                if player.name == player_name:
                    return player.color
        return None