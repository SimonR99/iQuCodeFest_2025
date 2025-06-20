import pygame
from typing import Tuple, Optional, Dict, Any, List
from .base_panel import BasePanel

class SidebarPanel(BasePanel):
    """Panel for displaying game information and controls"""
    
    def __init__(self, rect: pygame.Rect, colors: Dict[str, Any], fonts: Dict[str, pygame.font.Font]):
        super().__init__(rect, colors, fonts)
        self.info_panel_color = tuple(colors['ui_colors']['info_panel']['rgb'])
        
    def draw(self, surface: pygame.Surface, game_state, **kwargs):
        """Draw the sidebar panel with detailed sections like the original"""
        cards_drawn_this_turn = kwargs.get('cards_drawn_this_turn', 0)
        max_cards_per_turn = kwargs.get('max_cards_per_turn', 2)
        selected_route_idx = kwargs.get('selected_route_idx')
        mission_selection_active = kwargs.get('mission_selection_active', False)
        available_missions = kwargs.get('available_missions', [])
        selected_missions = kwargs.get('selected_missions', [])
        
        # Draw panel background
        pygame.draw.rect(surface, self.info_panel_color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, 3)
        
        # Add title background
        title_rect_bg = pygame.Rect(self.rect.x + 3, self.rect.y + 3, 
                                   self.rect.width - 6, 50)
        pygame.draw.rect(surface, self.accent_color, title_rect_bg)
        
        # Draw title (centered and properly sized)
        title_text = self.fonts['large_font'].render("|ket⟩ to Ride", True, self.text_color)
        title_rect_text = title_text.get_rect(center=title_rect_bg.center)
        surface.blit(title_text, title_rect_text)
        
        current_player = game_state.get_current_player()
        if not current_player:
            return
        
        # Handle mission selection interface
        if mission_selection_active:
            self._draw_mission_selection_interface(surface, available_missions, selected_missions)
            return
        
        # Start drawing content below title
        y_offset = 65
        
        # Current Player Section
        y_offset = self._draw_sidebar_section(surface, y_offset, "CURRENT PLAYER", [
            f"{current_player.name}",
            f"Gate Cards: {current_player.get_total_cards()}",
            f"Routes Claimed: {len(current_player.claimed_routes)}",
            f"Current Score: {current_player.score}",
        ], current_player.color)
        y_offset += 20
        
        # Mission Cards Section
        if current_player.missions:
            mission_section_height = self._draw_missions_section(surface, y_offset, current_player)
            y_offset += mission_section_height + 20
        else:
            no_mission_height = self._draw_no_missions_section(surface, y_offset)
            y_offset += no_mission_height + 20
        
        # Turn Actions Section
        turn_actions = [
            f"Cards drawn: {cards_drawn_this_turn}/{max_cards_per_turn}",
            "",
            "Available Actions:",
            "• Draw gate cards (2 max)" if cards_drawn_this_turn < max_cards_per_turn else "• Cards limit reached",
            "• Draw mission cards (M)" if cards_drawn_this_turn == 0 else "• Can't draw missions",
            "• Claim selected route" if selected_route_idx is not None else "• Select a route first",
        ]
        
        turn_section_height = self._draw_sidebar_section(surface, y_offset, "TURN ACTIONS", turn_actions)
        y_offset += turn_section_height + 20
        
        # Selected Route Section
        if selected_route_idx is not None:
            route = game_state.routes[selected_route_idx]
            route_info = [
                f"{route['from']} → {route['to']}",
                f"Gate: {route['gate']} (×{route['length']})",
                f"Cards needed: {route['length']}",
                f"You have: {current_player.hand.get(route['gate'], 0)}",
            ]
            route_section_height = self._draw_sidebar_section(surface, y_offset, "SELECTED ROUTE", route_info)
            y_offset += route_section_height + 20
        
        # Game Status Section (if space allows)
        remaining_space = self.rect.bottom - (self.rect.y + y_offset)
        if remaining_space > 150:
            game_status = [
                f"Turn: {game_state.turn_number}",
                f"Gate deck: {len(game_state.deck)} cards",
                f"Mission deck: {len(game_state.mission_deck)} cards",
            ]
            if game_state.game_over:
                game_status.extend([
                    "",
                    "🎉 GAME OVER! 🎉",
                    f"Winner: {game_state.winner.name}" if game_state.winner else "No Winner",
                ])
            
            game_section_height = self._draw_sidebar_section(surface, y_offset, "GAME STATUS", game_status)
            y_offset += game_section_height + 15
        
        # Controls Section (always show if space allows)
        remaining_space = self.rect.bottom - (self.rect.y + y_offset)
        if remaining_space > 100:
            controls = [
                "M - Draw missions",
                "SPACE - End turn", 
                "C - Claim route",
                "R - Cycle routes",
                "ESC - Exit/Cancel",
            ]
            self._draw_sidebar_section(surface, y_offset, "CONTROLS", controls, (80, 80, 120))
    
    def _draw_sidebar_section(self, surface: pygame.Surface, y_start: int, title: str, content: List[str], title_color=None) -> int:
        """Draw a sidebar section with title and content. Returns the height used."""
        if title_color is None:
            title_color = self.accent_color
            
        section_x = self.rect.x + 10
        section_width = self.rect.width - 20
        
        # Draw section title background
        title_height = 25
        title_rect = pygame.Rect(section_x, self.rect.y + y_start, section_width, title_height)
        pygame.draw.rect(surface, title_color, title_rect)
        pygame.draw.rect(surface, self.border_color, title_rect, 1)
        
        # Draw title text
        title_text = self.fonts['font'].render(title, True, (255, 255, 255))
        title_text_rect = title_text.get_rect(center=title_rect.center)
        surface.blit(title_text, title_text_rect)
        
        # Draw content
        content_y = y_start + title_height + 5
        line_height = 18
        
        for i, line in enumerate(content):
            if line:  # Skip empty lines for spacing
                text_color = self.text_color
                font = self.fonts['small_font']
                
                # Special formatting for certain lines
                if line.startswith("•"):
                    text_color = self.accent_color
                elif "🎉" in line:
                    text_color = (255, 215, 0)  # Gold
                
                text = font.render(line, True, text_color)
                surface.blit(text, (section_x + 5, self.rect.y + content_y))
            content_y += line_height
        
        total_height = title_height + 5 + len(content) * line_height
        return total_height
    
    def _draw_missions_section(self, surface: pygame.Surface, y_start: int, current_player) -> int:
        """Draw the missions section with visual mission cards. Returns height used."""
        if not current_player.missions:
            return 0
            
        section_x = self.rect.x + 10
        section_width = self.rect.width - 20
        
        # Draw section title
        title_height = 25
        title_rect = pygame.Rect(section_x, self.rect.y + y_start, section_width, title_height)
        pygame.draw.rect(surface, self.accent_color, title_rect)
        pygame.draw.rect(surface, self.border_color, title_rect, 1)
        
        completed_count = len(current_player.get_completed_missions())
        total_count = len(current_player.missions)
        title_text = f"MISSIONS ({completed_count}/{total_count} completed)"
        title_surface = self.fonts['font'].render(title_text, True, (255, 255, 255))
        title_text_rect = title_surface.get_rect(center=title_rect.center)
        surface.blit(title_surface, title_text_rect)
        
        # Draw mission cards
        card_y = y_start + title_height + 10
        card_height = 65
        card_spacing = 8
        
        for i, mission in enumerate(current_player.missions):
            card_rect = pygame.Rect(section_x + 5, self.rect.y + card_y, section_width - 10, card_height)
            
            # Determine card appearance based on completion status
            if mission.completed:
                bg_color = (50, 150, 50)  # Green for completed
                border_color = (100, 200, 100)
                text_color = (255, 255, 255)
                status_symbol = "✓"
                status_color = (200, 255, 200)
            else:
                bg_color = (70, 70, 90)  # Dark blue-gray for incomplete
                border_color = self.border_color
                text_color = (220, 220, 220)
                status_symbol = "○"
                status_color = (180, 180, 180)
            
            # Draw card background and border
            pygame.draw.rect(surface, bg_color, card_rect)
            pygame.draw.rect(surface, border_color, card_rect, 2)
            
            # Draw status symbol
            status_text = self.fonts['font'].render(status_symbol, True, status_color)
            status_rect = pygame.Rect(card_rect.x + 5, card_rect.y + 5, 20, 20)
            surface.blit(status_text, status_rect)
            
            # Draw mission details
            start_cities = " OR ".join(mission.start_cities)
            
            # Line 1: Start cities (truncate if too long)
            if len(start_cities) > 20:
                start_cities = start_cities[:17] + "..."
            start_text = self.fonts['small_font'].render(start_cities, True, text_color)
            surface.blit(start_text, (card_rect.x + 30, card_rect.y + 8))
            
            # Line 2: Quantum transformation
            transform_text = f"{mission.initial_state} → {mission.target_city} {mission.target_state}"
            if len(transform_text) > 25:
                # Truncate target city if needed
                short_target = mission.target_city[:8] + "..." if len(mission.target_city) > 8 else mission.target_city
                transform_text = f"{mission.initial_state} → {short_target} {mission.target_state}"
            
            transform_surface = self.fonts['small_font'].render(transform_text, True, text_color)
            surface.blit(transform_surface, (card_rect.x + 30, card_rect.y + 25))
            
            # Line 3: Points
            points_text = f"Points: {mission.points}"
            points_surface = self.fonts['small_font'].render(points_text, True, text_color)
            surface.blit(points_surface, (card_rect.x + 30, card_rect.y + 42))
            
            # Draw points value prominently on the right
            points_value = str(mission.points)
            points_value_surface = self.fonts['font'].render(points_value, True, status_color)
            points_value_rect = points_value_surface.get_rect(right=card_rect.right - 10, centery=card_rect.centery)
            surface.blit(points_value_surface, points_value_rect)
            
            card_y += card_height + card_spacing
        
        total_height = title_height + 10 + len(current_player.missions) * (card_height + card_spacing)
        return total_height
    
    def _draw_no_missions_section(self, surface: pygame.Surface, y_start: int) -> int:
        """Draw the no missions section with helpful instructions. Returns height used."""
        section_x = self.rect.x + 10
        section_width = self.rect.width - 20
        
        # Draw section title
        title_height = 25
        title_rect = pygame.Rect(section_x, self.rect.y + y_start, section_width, title_height)
        pygame.draw.rect(surface, (120, 120, 120), title_rect)  # Gray for no missions
        pygame.draw.rect(surface, self.border_color, title_rect, 1)
        
        title_text = "MISSIONS (0/0)"
        title_surface = self.fonts['font'].render(title_text, True, (255, 255, 255))
        title_text_rect = title_surface.get_rect(center=title_rect.center)
        surface.blit(title_surface, title_text_rect)
        
        # Draw instruction card
        card_height = 80
        card_rect = pygame.Rect(section_x + 5, self.rect.y + y_start + title_height + 10, section_width - 10, card_height)
        
        # Draw dashed border to indicate empty state
        pygame.draw.rect(surface, (60, 60, 60), card_rect)
        
        # Draw dashed border effect
        dash_length = 8
        gap_length = 4
        total_length = dash_length + gap_length
        
        # Top and bottom borders
        for x in range(card_rect.left, card_rect.right, total_length):
            if x + dash_length <= card_rect.right:
                pygame.draw.line(surface, self.border_color, (x, card_rect.top), (x + dash_length, card_rect.top), 2)
                pygame.draw.line(surface, self.border_color, (x, card_rect.bottom), (x + dash_length, card_rect.bottom), 2)
        
        # Left and right borders
        for y in range(card_rect.top, card_rect.bottom, total_length):
            if y + dash_length <= card_rect.bottom:
                pygame.draw.line(surface, self.border_color, (card_rect.left, y), (card_rect.left, y + dash_length), 2)
                pygame.draw.line(surface, self.border_color, (card_rect.right, y), (card_rect.right, y + dash_length), 2)
        
        # Draw instruction text
        instruction_lines = [
            "No missions yet!",
            "",
            "Press M to draw mission cards",
            "or click the mission deck",
        ]
        
        text_y = card_rect.y + 15
        for line in instruction_lines:
            if line:
                color = self.accent_color if "Press M" in line or "click" in line else (180, 180, 180)
                font = self.fonts['small_font'] if line != "No missions yet!" else self.fonts['font']
                text = font.render(line, True, color)
                text_rect = text.get_rect(centerx=card_rect.centerx, y=text_y)
                surface.blit(text, text_rect)
            text_y += 16
        
        total_height = title_height + 10 + card_height
        return total_height
    
    def _draw_mission_selection_interface(self, surface: pygame.Surface, available_missions, selected_missions):
        """Draw the mission selection interface in the sidebar"""
        y_offset = 65
        
        # Title
        title_lines = [
            "MISSION SELECTION",
            "Choose missions to keep:",
            f"Selected: {len(selected_missions)}/3",
            "Must keep at least 1",
            "",
        ]
        
        for line in title_lines:
            if line:
                text = self.fonts['font'].render(line, True, self.accent_color)
                surface.blit(text, (self.rect.x + 15, self.rect.y + y_offset))
            y_offset += 22
        
        # Draw mission cards
        card_height = 80
        card_spacing = 10
        card_width = self.rect.width - 30
        
        for i, mission in enumerate(available_missions):
            card_x = self.rect.x + 15
            card_y = self.rect.y + y_offset
            card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
            
            # Determine if this mission is selected
            is_selected = mission in selected_missions
            
            # Draw card background
            bg_color = self.accent_color if is_selected else tuple(self.colors['ui_colors']['card_area']['rgb'])
            pygame.draw.rect(surface, bg_color, card_rect)
            pygame.draw.rect(surface, self.border_color, card_rect, 2)
            
            # Draw mission info
            start_str = " OR ".join(mission.start_cities)
            mission_lines = [
                f"{i+1}. {start_str}",
                f"{mission.initial_state} → {mission.target_city} {mission.target_state}",
                f"Points: {mission.points}",
            ]
            
            text_y = card_y + 10
            for line in mission_lines:
                text_color = self.text_color if not is_selected else (255, 255, 255)
                text = self.fonts['small_font'].render(line, True, text_color)
                surface.blit(text, (card_x + 10, text_y))
                text_y += 20
            
            y_offset += card_height + card_spacing
        
        # Draw control instructions
        y_offset += 10
        instructions = [
            "Click cards to select/deselect",
            "Press ENTER to confirm",
            "Press ESC to cancel"
        ]
        
        for instruction in instructions:
            text = self.fonts['small_font'].render(instruction, True, self.accent_color)
            surface.blit(text, (self.rect.x + 15, self.rect.y + y_offset))
            y_offset += 18 