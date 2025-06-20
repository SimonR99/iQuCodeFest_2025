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
        self.university_sprite = None  # Cache for university node sprite
        self.load_config()
        self.load_rail_images()
        self.load_university_sprite()
        
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
    
    def load_university_sprite(self):
        """Load university node sprite from tilemap"""
        try:
            sprite_path = "assets/nodes/boutons uni vintage.png"
            if os.path.exists(sprite_path):
                # Load the full tilemap
                full_tilemap = pygame.image.load(sprite_path)
                
                # Tilemap is 5 columns x 3 rows
                # User wants row 3, column 2 (1-based), which is row 2, column 1 (0-based)
                tilemap_width = full_tilemap.get_width()
                tilemap_height = full_tilemap.get_height()
                
                sprite_width = tilemap_width // 5  # 5 columns
                sprite_height = tilemap_height // 3  # 3 rows
                
                # Extract the specific sprite (row 2, column 1 in 0-based indexing)
                target_row = 2  # Row 3 (1-based) = Row 2 (0-based)
                target_col = 1  # Column 2 (1-based) = Column 1 (0-based)
                
                sprite_x = target_col * sprite_width
                sprite_y = target_row * sprite_height
                
                # Create a surface for the extracted sprite
                original_sprite = pygame.Surface((sprite_width, sprite_height), pygame.SRCALPHA)
                sprite_rect = pygame.Rect(sprite_x, sprite_y, sprite_width, sprite_height)
                original_sprite.blit(full_tilemap, (0, 0), sprite_rect)
                
                # Scale down the sprite to a more reasonable size
                target_size = 48  # Much smaller size
                self.university_sprite = pygame.transform.scale(original_sprite, (target_size, target_size))
                
                print(f"Loaded university sprite from tilemap: {sprite_width}x{sprite_height} at ({sprite_x}, {sprite_y}), scaled to {target_size}x{target_size}")
            else:
                print(f"University sprite not found: {sprite_path}")
        except Exception as e:
            print(f"Could not load university sprite: {e}")
    
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
        # Handle both array and single gate formats
        gates = route_data['gate']
        if isinstance(gates, str):
            gates = [gates]  # Convert single gate to array
        
        # Determine which gate to display
        display_gate = None
        claimed_with_gate = route_data.get('claimed_with_gate')
        if claimed_with_gate:
            # Show the gate that was used to claim this route
            display_gate = claimed_with_gate
        else:
            # For parallel routes, we receive individual gates; for others, show combined
            if len(gates) == 1:
                display_gate = gates[0]
            else:
                # This should only happen for the main route display (not parallel sub-routes)
                display_gate = "/".join(gates)
        
        length = route_data['length']
        claimed_by = route_data.get('claimed_by')
        
        # Extract the specific claimed player for the current gate
        actual_claimed_by = None
        if claimed_by:
            if isinstance(claimed_by, dict):
                # New format: check if current gate is claimed
                actual_claimed_by = claimed_by.get(display_gate)
            else:
                # Old format: route is claimed by this player
                actual_claimed_by = claimed_by
        
        # Get route color based on claim status
        if actual_claimed_by and player_color:
            color = player_color  # Use player's color for claimed routes
        elif highlighted:
            color = (255, 255, 0)   # Yellow for highlighted routes
        else:
            # For multiple gates, use a blended color or the first gate's color
            if claimed_with_gate:
                color = self.get_gate_color(claimed_with_gate)
            elif len(gates) == 1:
                color = self.get_gate_color(gates[0])
            else:
                # Blend colors for multiple gates or use a neutral color
                color = (150, 150, 150)  # Gray for multiple unclaimed gates
        
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
        self.draw_route_segments(surface, start_pos, end_pos, length, color, display_gate, actual_claimed_by, player_color)
        
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
            # Don't draw labels on individual segments - we'll draw it centered later
            self.draw_train_car(surface, 
                              (segment_start_x, segment_start_y), 
                              (segment_end_x, segment_end_y), 
                              segment_width, color, gate, False, claimed_by, player_color)
            
            # Move to next segment position (including spacing)
            current_x += unit_x * (segment_length + segment_spacing)
            current_y += unit_y * (segment_length + segment_spacing)
        
        # Draw gate label at the true center of the entire route FIRST (before squares)
        if self.font:
            route_center_x = (start_pos[0] + end_pos[0]) / 2
            route_center_y = (start_pos[1] + end_pos[1]) / 2
            
            # Use white text for better visibility on routes
            gate_text = self.font.render(gate, True, (255, 255, 255))
            text_rect = gate_text.get_rect(center=(int(route_center_x), int(route_center_y)))
            
            # Draw text directly without background for cleaner look
            surface.blit(gate_text, text_rect)
        
        # Now draw all the player ownership squares AFTER the text so they're on top
        if claimed_by and player_color:
            # Redraw squares on top of everything using same positioning logic
            dx = end_pos[0] - start_pos[0]
            dy = end_pos[1] - start_pos[1]
            route_length = math.sqrt(dx*dx + dy*dy)
            
            if route_length == 0 or length == 0:
                return
                
            # Unit vector along the route
            unit_x = dx / route_length
            unit_y = dy / route_length
            
            current_x = start_pos[0]
            current_y = start_pos[1]
            
            # Calculate same segment positioning as above
            segment_spacing = 3
            total_spacing = (length - 1) * segment_spacing
            available_length = route_length - total_spacing
            segment_length = available_length / length
            
            if segment_length < 8:
                segment_length = 8
                segment_spacing = max(1, (route_length - length * segment_length) / max(1, length - 1))
            
            # Draw a square on each segment center
            for i in range(length):
                segment_start_x = current_x
                segment_start_y = current_y
                segment_end_x = current_x + unit_x * segment_length
                segment_end_y = current_y + unit_y * segment_length
                
                # Draw the square at this segment's center
                square_center_x = int((segment_start_x + segment_end_x) / 2)
                square_center_y = int((segment_start_y + segment_end_y) / 2)
                
                # Square size for gameplay (smaller than debug size)
                square_size = 12
                square_rect = pygame.Rect(
                    square_center_x - square_size // 2,
                    square_center_y - square_size // 2,
                    square_size,
                    square_size
                )
                
                # Draw visible border
                border_size = 2
                border_rect = pygame.Rect(
                    square_center_x - square_size // 2 - border_size,
                    square_center_y - square_size // 2 - border_size,
                    square_size + 2 * border_size,
                    square_size + 2 * border_size
                )
                
                # Use player color with borders for visibility
                pygame.draw.rect(surface, (255, 255, 255), border_rect)  # White border
                pygame.draw.rect(surface, player_color, square_rect)      # Player color
                pygame.draw.rect(surface, (0, 0, 0), square_rect, 1)     # Black inner border
                
                # Move to next segment position
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
        
        # Note: Player ownership squares are now drawn at the route level for proper layering
        
        # Draw gate label on first segment AFTER the square (so text doesn't cover it)
        if show_label and self.font:
            label_center_x = (start_pos[0] + end_pos[0]) / 2
            label_center_y = (start_pos[1] + end_pos[1]) / 2
            
            # Use white text for better visibility on routes
            gate_text = self.font.render(gate, True, (255, 255, 255))
            text_rect = gate_text.get_rect(center=(int(label_center_x), int(label_center_y)))
            
            # Draw text directly without background for cleaner look
            surface.blit(gate_text, text_rect)
    
    def draw_university(self, surface: pygame.Surface, position: Tuple[int, int], 
                       uni_data: Dict, uni_id: str):
        x, y = position
        
        if self.university_sprite:
            # Use the sprite image
            sprite_width = self.university_sprite.get_width()
            sprite_height = self.university_sprite.get_height()
            
            # Center the sprite on the position
            sprite_x = x - sprite_width // 2
            sprite_y = y - sprite_height // 2
            
            surface.blit(self.university_sprite, (sprite_x, sprite_y))
            
            # Use sprite dimensions for text positioning
            text_y_offset = sprite_height // 2 + 8
        else:
            # Fallback to circle if sprite not loaded
            radius = self.map_settings.get('university_radius', 15)
            color = uni_data.get('color', [100, 100, 100])
            
            # Draw university circle
            pygame.draw.circle(surface, color, (x, y), radius)
            pygame.draw.circle(surface, (255, 255, 255), (x, y), radius, 2)
            
            text_y_offset = radius + 18
        
        # Draw university name
        if self.font:
            name_text = self.font.render(uni_id, True, (255, 255, 255))
            text_rect = name_text.get_rect(center=(x, y + text_y_offset))
            
            # Draw text directly without background for cleaner look
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
        
        # Use routes from game_state if available, otherwise use loaded routes
        routes_to_draw = game_state.routes if game_state else self.routes
        
        # Draw routes first (so they appear behind universities)
        for i, route in enumerate(routes_to_draw):
            from_uni = route['from']
            to_uni = route['to']
            
            if from_uni in scaled_positions and to_uni in scaled_positions:
                start_pos = scaled_positions[from_uni]
                end_pos = scaled_positions[to_uni]
                
                highlighted = (highlighted_route_idx == i)
                # Get player color if route is claimed
                player_color = None
                claimed_by = route.get('claimed_by')
                if claimed_by:
                    if isinstance(claimed_by, dict):
                        # New format: check if any gate is claimed
                        for gate_claimed_by in claimed_by.values():
                            if gate_claimed_by:
                                player_color = self.get_player_color(gate_claimed_by, game_state)
                                break
                    else:
                        # Old format: route is claimed by this player
                        player_color = self.get_player_color(claimed_by, game_state)
                
                # Handle both array and single gate formats for visual display
                gates = route['gate']
                if isinstance(gates, str):
                    gates = [gates]  # Convert single gate to array
                
                # If route has multiple gates, draw them as parallel paths
                if len(gates) > 1:
                    # Draw multiple parallel paths, showing individual claim status
                    offset_distance = 25  # Distance between parallel routes
                    total_width = (len(gates) - 1) * offset_distance
                    start_offset = -total_width / 2
                    
                    for j, gate in enumerate(gates):
                        offset = start_offset + j * offset_distance
                        # Create a temporary route dict for each gate
                        temp_route = route.copy()
                        temp_route['gate'] = gate  # Single gate for this path
                        
                        # Check individual gate claim status
                        claimed_by = route.get('claimed_by', {})
                        if isinstance(claimed_by, dict):
                            temp_route['claimed_by'] = claimed_by.get(gate)
                        else:
                            temp_route['claimed_by'] = claimed_by
                        
                        # Get player color for this specific gate
                        gate_player_color = None
                        if temp_route['claimed_by']:
                            gate_player_color = self.get_player_color(temp_route['claimed_by'], game_state)
                        
                        self.draw_route(surface, start_pos, end_pos, temp_route, int(offset), highlighted, gate_player_color)
                else:
                    # Single path for single-gate routes
                    self.draw_route(surface, start_pos, end_pos, route, 0, highlighted, player_color)
        
        # Draw universities on top of routes
        for uni_id, uni_data in self.universities.items():
            if uni_id in scaled_positions:
                position = scaled_positions[uni_id]
                self.draw_university(surface, position, uni_data, uni_id)
    
    def get_university_at_position(self, map_rect: pygame.Rect, 
                                  mouse_pos: Tuple[int, int]) -> Optional[str]:
        scaled_positions = self.scale_positions(map_rect)
        
        for uni_id, pos in scaled_positions.items():
            if self.university_sprite:
                # Use sprite dimensions for hit detection
                sprite_width = self.university_sprite.get_width()
                sprite_height = self.university_sprite.get_height()
                
                # Check if mouse is within sprite bounds
                sprite_x = pos[0] - sprite_width // 2
                sprite_y = pos[1] - sprite_height // 2
                
                if (sprite_x <= mouse_pos[0] <= sprite_x + sprite_width and
                    sprite_y <= mouse_pos[1] <= sprite_y + sprite_height):
                    return uni_id
            else:
                # Fallback to circular hit detection
                radius = self.map_settings.get('university_radius', 15)
                distance = math.sqrt((mouse_pos[0] - pos[0])**2 + (mouse_pos[1] - pos[1])**2)
                if distance <= radius:
                    return uni_id
        return None
    
    def get_route_at_position(self, map_rect: pygame.Rect, 
                             mouse_pos: Tuple[int, int], game_state=None) -> Optional[Tuple[int, str]]:
        """Find which route and gate (if any) is clicked by the mouse. Returns (route_index, gate) or None"""
        if not self.universities:
            return None
            
        scaled_positions = self.scale_positions(map_rect)
        click_tolerance = 15  # How close to route line to register click
        
        # Use absolute mouse position (don't convert to relative)
        absolute_pos = mouse_pos
        
        # Use routes from game_state if available, otherwise use loaded routes
        routes_to_check = game_state.routes if game_state else self.routes
        
        # Check each route, considering parallel paths for multi-gate routes
        for i, route in enumerate(routes_to_check):
            from_uni = route['from']
            to_uni = route['to']
            
            if from_uni in scaled_positions and to_uni in scaled_positions:
                start_pos = scaled_positions[from_uni]
                end_pos = scaled_positions[to_uni]
                
                # Handle both array and single gate formats
                gates = route['gate']
                if isinstance(gates, str):
                    gates = [gates]
                
                # Check parallel paths for multi-gate routes
                if len(gates) > 1:
                    # Check each parallel path
                    offset_distance = 25
                    total_width = (len(gates) - 1) * offset_distance
                    start_offset = -total_width / 2
                    
                    for j, gate in enumerate(gates):
                        offset = start_offset + j * offset_distance
                        
                        # Calculate offset positions
                        dx = end_pos[0] - start_pos[0]
                        dy = end_pos[1] - start_pos[1]
                        length_route = math.sqrt(dx*dx + dy*dy)
                        if length_route > 0:
                            perp_x = -dy / length_route * offset
                            perp_y = dx / length_route * offset
                            offset_start = (int(start_pos[0] + perp_x), int(start_pos[1] + perp_y))
                            offset_end = (int(end_pos[0] + perp_x), int(end_pos[1] + perp_y))
                            
                            distance = self._point_to_line_distance(absolute_pos, offset_start, offset_end)
                            if distance <= click_tolerance:
                                return (i, gate)
                else:
                    # Single path check
                    distance = self._point_to_line_distance(absolute_pos, start_pos, end_pos)
                    if distance <= click_tolerance:
                        return (i, gates[0])
        
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
    
    def get_player_color(self, player_id: str, game_state) -> Optional[Tuple[int, int, int]]:
        """Get player color by player ID"""
        if game_state and hasattr(game_state, 'players'):
            for player in game_state.players:
                if player.player_id == player_id:
                    return player.color
        return None