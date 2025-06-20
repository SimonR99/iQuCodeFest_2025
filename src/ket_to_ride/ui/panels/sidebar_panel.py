import pygame
from typing import Tuple, Optional, Dict, Any, List
from .base_panel import BasePanel

class SidebarPanel(BasePanel):
    """Panel for displaying game information and controls"""
    
    def __init__(self, rect: pygame.Rect, colors: Dict[str, Any], fonts: Dict[str, pygame.font.Font]):
        super().__init__(rect, colors, fonts)
        self.info_panel_color = tuple(colors['ui_colors']['info_panel']['rgb'])
        self.action_buttons = []  # List of (rect, action, enabled) tuples
        self.hovered_button = None
        
        # Scrolling state
        self.scroll_offset = 0
        self.max_scroll = 0
        self.content_height = 0
        self.scrollbar_width = 12
        self.scrollbar_dragging = False
        self.scrollbar_drag_start = 0
        self.scroll_start_offset = 0
        
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
        
        # Add title background (fixed at top, not scrollable)
        title_rect_bg = pygame.Rect(self.rect.x + 3, self.rect.y + 3, 
                                   self.rect.width - 6 - self.scrollbar_width, 50)
        pygame.draw.rect(surface, self.accent_color, title_rect_bg)
        
        # Draw title (centered and properly sized)
        title_text = self.fonts['large_font'].render("Game Info", True, self.text_color)
        title_rect_text = title_text.get_rect(center=title_rect_bg.center)
        surface.blit(title_text, title_rect_text)
        
        # Create scrollable content area (below title)
        content_rect = pygame.Rect(self.rect.x + 3, self.rect.y + 56, 
                                  self.rect.width - 6 - self.scrollbar_width, 
                                  self.rect.height - 59)
        
        # Create a surface for scrollable content
        if content_rect.height > 0:
            content_surface = pygame.Surface((content_rect.width, max(content_rect.height, 2000)), pygame.SRCALPHA)
            content_surface.fill((0, 0, 0, 0))  # Transparent
            
            # Draw content on the scrollable surface
            self._draw_scrollable_content(content_surface, game_state, cards_drawn_this_turn, 
                                        max_cards_per_turn, selected_route_idx, 
                                        mission_selection_active, available_missions, selected_missions)
            
            # Blit the visible portion to the main surface
            visible_rect = pygame.Rect(0, self.scroll_offset, content_rect.width, content_rect.height)
            surface.blit(content_surface, content_rect, visible_rect)
            
            # Draw scrollbar if needed
            self._draw_scrollbar(surface, content_rect)
        
        current_player = game_state.get_current_player()
        if not current_player:
            return
    
    def _draw_scrollable_content(self, surface: pygame.Surface, game_state, cards_drawn_this_turn, 
                               max_cards_per_turn, selected_route_idx, mission_selection_active, 
                               available_missions, selected_missions):
        """Draw all scrollable content on the provided surface"""
        current_player = game_state.get_current_player()
        if not current_player:
            return
        
        # Handle mission selection interface
        if mission_selection_active:
            self._draw_mission_selection_interface_scrollable(surface, available_missions, selected_missions)
            return
        
        # Start drawing content from top of scrollable area
        y_offset = 10
        
        # Current Player Section
        y_offset = self._draw_sidebar_section_scrollable(surface, y_offset, "CURRENT PLAYER", [
            f"{current_player.name}",
            f"Gate Cards: {current_player.get_total_cards()}",
            f"Routes Claimed: {len(current_player.claimed_routes)}",
            f"Current Score: {current_player.score}",
        ], current_player.color)
        y_offset += 20
        
        # Mission Cards Section
        if current_player.missions:
            mission_section_height = self._draw_missions_section_scrollable(surface, y_offset, current_player)
            y_offset += mission_section_height + 20
        else:
            no_mission_height = self._draw_no_missions_section_scrollable(surface, y_offset)
            y_offset += no_mission_height + 20
        
        # Turn Actions Section with buttons
        self.action_buttons = []  # Reset buttons
        turn_section_height = self._draw_turn_actions_section_scrollable(surface, y_offset, current_player, 
                                                            cards_drawn_this_turn, max_cards_per_turn, 
                                                            selected_route_idx, mission_selection_active)
        y_offset += turn_section_height + 20
        
        # Selected Route Section
        if selected_route_idx is not None:
            route = game_state.routes[selected_route_idx]
            
            # Handle both array and single gate formats
            gates = route['gate']
            if isinstance(gates, str):
                gates = [gates]
            
            # Check claimed status with new format
            claimed_by = route.get('claimed_by', {})
            if isinstance(claimed_by, dict):
                # New format: check individual gate claims
                claimed_gates = []
                unclaimed_gates = []
                
                for gate in gates:
                    if claimed_by.get(gate) is not None:
                        claimed_gates.append(gate)
                    else:
                        unclaimed_gates.append(gate)
                
                if len(gates) == 1:
                    # Single gate route
                    if claimed_gates:
                        gate_display = f"{gates[0]} (CLAIMED by {claimed_by[gates[0]]})"
                        cards_info = "Gate already claimed"
                    else:
                        gate_display = f"{gates[0]} (×{route['length']})"
                        cards_info = f"You have: {current_player.hand.get(gates[0], 0)}"
                else:
                    # Multi-gate route
                    if unclaimed_gates:
                        if claimed_gates:
                            # Some gates claimed, some not
                            gate_display = f"Available: {'/'.join(unclaimed_gates)} (×{route['length']})"
                            gate_display += f" | Claimed: {'/'.join(claimed_gates)}"
                        else:
                            # No gates claimed yet
                            gate_display = f"Options: {'/'.join(unclaimed_gates)} (×{route['length']})"
                        
                        # Show cards for unclaimed gate options
                        card_counts = [f"{gate}: {current_player.hand.get(gate, 0)}" for gate in unclaimed_gates]
                        cards_info = f"You have: {', '.join(card_counts)}"
                    else:
                        # All gates claimed
                        gate_display = f"All claimed: {'/'.join(claimed_gates)}"
                        cards_info = "All gates on this route are claimed"
            else:
                # Old format compatibility
                if claimed_by is not None:
                    gate_display = f"{gates[0]} (CLAIMED by {claimed_by})"
                    cards_info = "Route already claimed"
                else:
                    if len(gates) == 1:
                        gate_display = f"{gates[0]} (×{route['length']})"
                        cards_info = f"You have: {current_player.hand.get(gates[0], 0)}"
                    else:
                        gate_display = f"Options: {'/'.join(gates)} (×{route['length']})"
                        card_counts = [f"{gate}: {current_player.hand.get(gate, 0)}" for gate in gates]
                        cards_info = f"You have: {', '.join(card_counts)}"
            
            route_info = [
                f"{route['from']} → {route['to']}",
                f"Gate: {gate_display}",
                f"Cards needed: {route['length']}",
                cards_info,
            ]
            route_section_height = self._draw_sidebar_section_scrollable(surface, y_offset, "SELECTED ROUTE", route_info)
            y_offset += route_section_height + 20
        
        # Game Status Section (always show in scrollable view)
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
        
        game_section_height = self._draw_sidebar_section_scrollable(surface, y_offset, "GAME STATUS", game_status)
        y_offset += game_section_height + 15
        
        # Controls Section (always show in scrollable view)
        controls = [
            "M - Draw missions",
            "SPACE - End turn", 
            "C - Claim route",
            "R - Cycle routes",
            "ESC - Exit/Cancel",
        ]
        self._draw_sidebar_section_scrollable(surface, y_offset, "CONTROLS", controls, (80, 80, 120))
        y_offset += self._get_section_height("CONTROLS", controls) + 20
        
        # Store content height for scrollbar calculations
        self.content_height = y_offset
        content_rect_height = self.rect.height - 59
        self.max_scroll = max(0, self.content_height - content_rect_height)
    
    def _draw_sidebar_section_scrollable(self, surface: pygame.Surface, y_start: int, title: str, content: List[str], title_color=None) -> int:
        """Draw a sidebar section with title and content on scrollable surface. Returns the height used."""
        if title_color is None:
            title_color = self.accent_color
            
        section_x = 10
        section_width = surface.get_width() - 20
        
        # Draw section title background
        title_height = 25
        title_rect = pygame.Rect(section_x, y_start, section_width, title_height)
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
                surface.blit(text, (section_x + 5, content_y))
            content_y += line_height
        
        total_height = title_height + 5 + len(content) * line_height
        return total_height

    def _draw_missions_section_scrollable(self, surface: pygame.Surface, y_start: int, current_player) -> int:
        """Draw the missions section with visual mission cards on scrollable surface. Returns height used."""
        if not current_player.missions:
            return 0
            
        section_x = 10
        section_width = surface.get_width() - 20
        
        # Draw section title
        title_height = 25
        title_rect = pygame.Rect(section_x, y_start, section_width, title_height)
        pygame.draw.rect(surface, self.accent_color, title_rect)
        pygame.draw.rect(surface, self.border_color, title_rect, 1)
        
        completed_count = len(current_player.get_completed_missions())
        total_count = len(current_player.missions)
        title_text = f"MISSIONS ({completed_count}/{total_count})"
        title_surface = self.fonts['font'].render(title_text, True, (255, 255, 255))
        title_text_rect = title_surface.get_rect(center=title_rect.center)
        surface.blit(title_surface, title_text_rect)
        
        # Draw mission cards
        card_y = y_start + title_height + 10
        card_height = 65
        card_spacing = 8
        
        for i, mission in enumerate(current_player.missions):
            card_rect = pygame.Rect(section_x + 5, card_y, section_width - 10, card_height)
            
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

    def _draw_no_missions_section_scrollable(self, surface: pygame.Surface, y_start: int) -> int:
        """Draw the no missions section with helpful instructions on scrollable surface. Returns height used."""
        section_x = 10
        section_width = surface.get_width() - 20
        
        # Draw section title
        title_height = 25
        title_rect = pygame.Rect(section_x, y_start, section_width, title_height)
        pygame.draw.rect(surface, (120, 120, 120), title_rect)  # Gray for no missions
        pygame.draw.rect(surface, self.border_color, title_rect, 1)
        
        title_text = "MISSIONS (0/0)"
        title_surface = self.fonts['font'].render(title_text, True, (255, 255, 255))
        title_text_rect = title_surface.get_rect(center=title_rect.center)
        surface.blit(title_surface, title_text_rect)
        
        # Draw instruction card
        card_height = 80
        card_rect = pygame.Rect(section_x + 5, y_start + title_height + 10, section_width - 10, card_height)
        
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

    def _draw_mission_selection_interface_scrollable(self, surface: pygame.Surface, available_missions, selected_missions):
        """Draw the mission selection interface on scrollable surface"""
        y_offset = 10
        
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
                surface.blit(text, (15, y_offset))
            y_offset += 22
        
        # Draw mission cards
        card_height = 80
        card_spacing = 10
        card_width = surface.get_width() - 30
        
        for i, mission in enumerate(available_missions):
            card_x = 15
            card_y = y_offset
            card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
            
            # Determine if this mission is selected
            is_selected = mission in selected_missions
            
            # Draw card background
            bg_color = self.accent_color if is_selected else tuple(self.colors['ui_colors']['card_area']['rgb'])
            pygame.draw.rect(surface, bg_color, card_rect)
            pygame.draw.rect(surface, self.border_color, card_rect, 2)
            
            # Draw mission content (similar to regular mission cards)
            text_color = (255, 255, 255) if is_selected else (200, 200, 200)
            
            # Start cities
            start_cities = " OR ".join(mission.start_cities)
            if len(start_cities) > 22:
                start_cities = start_cities[:19] + "..."
            start_text = self.fonts['small_font'].render(start_cities, True, text_color)
            surface.blit(start_text, (card_x + 10, card_y + 10))
            
            # Quantum transformation
            transform_text = f"{mission.initial_state} → {mission.target_city} {mission.target_state}"
            if len(transform_text) > 30:
                short_target = mission.target_city[:10] + "..." if len(mission.target_city) > 10 else mission.target_city
                transform_text = f"{mission.initial_state} → {short_target} {mission.target_state}"
            
            transform_surface = self.fonts['small_font'].render(transform_text, True, text_color)
            surface.blit(transform_surface, (card_x + 10, card_y + 30))
            
            # Points
            points_text = f"Points: {mission.points}"
            points_surface = self.fonts['small_font'].render(points_text, True, text_color)
            surface.blit(points_surface, (card_x + 10, card_y + 50))
            
            # Selection indicator
            if is_selected:
                indicator = self.fonts['font'].render("✓", True, (255, 255, 255))
                surface.blit(indicator, (card_rect.right - 25, card_y + 5))
            
            y_offset += card_height + card_spacing
        
        # Draw action buttons
        button_y = y_offset + 20
        button_width = 80
        button_height = 30
        button_spacing = 20
        
        # Confirm button
        confirm_rect = pygame.Rect(15, button_y, button_width, button_height)
        can_confirm = len(selected_missions) >= 1
        confirm_color = self.accent_color if can_confirm else (80, 80, 80)
        pygame.draw.rect(surface, confirm_color, confirm_rect)
        pygame.draw.rect(surface, self.border_color, confirm_rect, 2)
        
        confirm_text = self.fonts['small_font'].render("Confirm", True, (255, 255, 255))
        confirm_text_rect = confirm_text.get_rect(center=confirm_rect.center)
        surface.blit(confirm_text, confirm_text_rect)
        
        # Cancel button
        cancel_rect = pygame.Rect(15 + button_width + button_spacing, button_y, button_width, button_height)
        pygame.draw.rect(surface, (120, 60, 60), cancel_rect)
        pygame.draw.rect(surface, self.border_color, cancel_rect, 2)
        
        cancel_text = self.fonts['small_font'].render("Cancel", True, (255, 255, 255))
        cancel_text_rect = cancel_text.get_rect(center=cancel_rect.center)
        surface.blit(cancel_text, cancel_text_rect)
        
        # Store button rects for click handling (adjusted for scroll)
        self.action_buttons = [
            (pygame.Rect(confirm_rect.x + self.rect.x + 3, confirm_rect.y + self.rect.y + 56 - self.scroll_offset, 
                        confirm_rect.width, confirm_rect.height), "confirm_mission_selection", can_confirm),
            (pygame.Rect(cancel_rect.x + self.rect.x + 3, cancel_rect.y + self.rect.y + 56 - self.scroll_offset, 
                        cancel_rect.width, cancel_rect.height), "cancel_mission_selection", True)
        ]

    def _draw_turn_actions_section_scrollable(self, surface: pygame.Surface, y_start: int, current_player, 
                                            cards_drawn_this_turn: int, max_cards_per_turn: int, 
                                            selected_route_idx: Optional[int], mission_selection_active: bool) -> int:
        """Draw the turn actions section with interactive buttons on scrollable surface. Returns height used."""
        section_x = 10
        section_width = surface.get_width() - 20
        
        # Draw section title
        title_height = 25
        title_rect = pygame.Rect(section_x, y_start, section_width, title_height)
        pygame.draw.rect(surface, self.accent_color, title_rect)
        pygame.draw.rect(surface, self.border_color, title_rect, 1)
        
        title_text = "TURN ACTIONS"
        title_surface = self.fonts['font'].render(title_text, True, (255, 255, 255))
        title_text_rect = title_surface.get_rect(center=title_rect.center)
        surface.blit(title_surface, title_text_rect)
        
        # Button configuration
        button_height = 35
        button_spacing = 8
        button_margin = 10
        
        current_y = y_start + title_height + 15
        
        # Mission draw button
        can_draw_missions = len(current_player.missions) < 5
        mission_button_rect = pygame.Rect(section_x + button_margin, current_y, 
                                        section_width - 2 * button_margin, button_height)
        
        mission_color = self.accent_color if can_draw_missions else (80, 80, 80)
        pygame.draw.rect(surface, mission_color, mission_button_rect)
        pygame.draw.rect(surface, self.border_color, mission_button_rect, 2)
        
        mission_text = "Draw Mission Cards"
        if not can_draw_missions:
            mission_text += " (Max 5)"
        
        mission_surface = self.fonts['small_font'].render(mission_text, True, (255, 255, 255))
        mission_text_rect = mission_surface.get_rect(center=mission_button_rect.center)
        surface.blit(mission_surface, mission_text_rect)
        
        current_y += button_height + button_spacing
        
        # Route claim button
        can_claim = selected_route_idx is not None
        claim_button_rect = pygame.Rect(section_x + button_margin, current_y, 
                                      section_width - 2 * button_margin, button_height)
        
        claim_color = self.accent_color if can_claim else (80, 80, 80)
        pygame.draw.rect(surface, claim_color, claim_button_rect)
        pygame.draw.rect(surface, self.border_color, claim_button_rect, 2)
        
        claim_text = "Claim Selected Route" if can_claim else "Select Route First"
        claim_surface = self.fonts['small_font'].render(claim_text, True, (255, 255, 255))
        claim_text_rect = claim_surface.get_rect(center=claim_button_rect.center)
        surface.blit(claim_surface, claim_text_rect)
        
        current_y += button_height + button_spacing
        
        # End turn button
        end_turn_button_rect = pygame.Rect(section_x + button_margin, current_y, 
                                         section_width - 2 * button_margin, button_height)
        
        pygame.draw.rect(surface, (100, 120, 100), end_turn_button_rect)
        pygame.draw.rect(surface, self.border_color, end_turn_button_rect, 2)
        
        end_turn_surface = self.fonts['small_font'].render("End Turn", True, (255, 255, 255))
        end_turn_text_rect = end_turn_surface.get_rect(center=end_turn_button_rect.center)
        surface.blit(end_turn_surface, end_turn_text_rect)
        
        current_y += button_height + 15
        
        # Store button rects for click handling (adjusted for panel position and scroll)
        self.action_buttons.extend([
            (pygame.Rect(mission_button_rect.x + self.rect.x + 3, mission_button_rect.y + self.rect.y + 56 - self.scroll_offset, 
                        mission_button_rect.width, mission_button_rect.height), "draw_missions", can_draw_missions),
            (pygame.Rect(claim_button_rect.x + self.rect.x + 3, claim_button_rect.y + self.rect.y + 56 - self.scroll_offset, 
                        claim_button_rect.width, claim_button_rect.height), "claim_route", can_claim),
            (pygame.Rect(end_turn_button_rect.x + self.rect.x + 3, end_turn_button_rect.y + self.rect.y + 56 - self.scroll_offset, 
                        end_turn_button_rect.width, end_turn_button_rect.height), "end_turn", True)
        ])
        
        total_height = title_height + 15 + 3 * button_height + 2 * button_spacing + 15
        return total_height

    def _get_section_height(self, title: str, content: List[str]) -> int:
        """Calculate the height of a section without drawing it"""
        title_height = 25
        content_height = 5 + len(content) * 18
        return title_height + content_height

    def _draw_scrollbar(self, surface: pygame.Surface, content_rect: pygame.Rect):
        """Draw scrollbar if content is scrollable"""
        if self.max_scroll <= 0:
            return
        
        # Scrollbar track
        scrollbar_rect = pygame.Rect(content_rect.right, content_rect.top, 
                                   self.scrollbar_width, content_rect.height)
        pygame.draw.rect(surface, (60, 60, 60), scrollbar_rect)
        pygame.draw.rect(surface, self.border_color, scrollbar_rect, 1)
        
        # Scrollbar thumb
        thumb_height = max(20, int(content_rect.height * content_rect.height / self.content_height))
        thumb_y = content_rect.top + int(self.scroll_offset * (content_rect.height - thumb_height) / self.max_scroll)
        
        thumb_rect = pygame.Rect(scrollbar_rect.x + 2, thumb_y, 
                               scrollbar_rect.width - 4, thumb_height)
        pygame.draw.rect(surface, (120, 120, 120), thumb_rect)
        pygame.draw.rect(surface, (160, 160, 160), thumb_rect, 1)

    def handle_scroll(self, scroll_direction: int):
        """Handle scroll wheel input"""
        scroll_amount = 30  # pixels per scroll step
        if scroll_direction > 0:  # Scroll up
            self.scroll_offset = max(0, self.scroll_offset - scroll_amount)
        elif scroll_direction < 0:  # Scroll down
            self.scroll_offset = min(self.max_scroll, self.scroll_offset + scroll_amount)

    def handle_scrollbar_click(self, pos: Tuple[int, int]) -> bool:
        """Handle clicks on the scrollbar. Returns True if handled."""
        if self.max_scroll <= 0:
            return False
        
        content_rect = pygame.Rect(self.rect.x + 3, self.rect.y + 56, 
                                  self.rect.width - 6 - self.scrollbar_width, 
                                  self.rect.height - 59)
        
        scrollbar_rect = pygame.Rect(content_rect.right, content_rect.top, 
                                   self.scrollbar_width, content_rect.height)
        
        if not scrollbar_rect.collidepoint(pos):
            return False
        
        # Calculate thumb position and size
        thumb_height = max(20, int(content_rect.height * content_rect.height / self.content_height))
        thumb_y = content_rect.top + int(self.scroll_offset * (content_rect.height - thumb_height) / self.max_scroll)
        thumb_rect = pygame.Rect(scrollbar_rect.x + 2, thumb_y, 
                               scrollbar_rect.width - 4, thumb_height)
        
        if thumb_rect.collidepoint(pos):
            # Start dragging the thumb
            self.scrollbar_dragging = True
            self.scrollbar_drag_start = pos[1]
            self.scroll_start_offset = self.scroll_offset
        else:
            # Click on track - jump to position
            track_click_ratio = (pos[1] - content_rect.top) / content_rect.height
            self.scroll_offset = int(track_click_ratio * self.max_scroll)
            self.scroll_offset = max(0, min(self.max_scroll, self.scroll_offset))
        
        return True

    def handle_scrollbar_drag(self, pos: Tuple[int, int]):
        """Handle dragging the scrollbar thumb"""
        if not self.scrollbar_dragging:
            return
        
        content_rect = pygame.Rect(self.rect.x + 3, self.rect.y + 56, 
                                  self.rect.width - 6 - self.scrollbar_width, 
                                  self.rect.height - 59)
        
        drag_delta = pos[1] - self.scrollbar_drag_start
        thumb_height = max(20, int(content_rect.height * content_rect.height / self.content_height))
        scroll_range = content_rect.height - thumb_height
        
        if scroll_range > 0:
            scroll_delta = int(drag_delta * self.max_scroll / scroll_range)
            self.scroll_offset = self.scroll_start_offset + scroll_delta
            self.scroll_offset = max(0, min(self.max_scroll, self.scroll_offset))

    def stop_scrollbar_drag(self):
        """Stop scrollbar dragging"""
        self.scrollbar_dragging = False

    def _handle_click_internal(self, pos: Tuple[int, int], game_state, **kwargs) -> Optional[str]:
        """Handle clicks on action buttons and scrollbar"""
        # First check if it's a scrollbar click
        if self.handle_scrollbar_click(pos):
            return None
        
        # Check action buttons
        for button_rect, action, enabled in self.action_buttons:
            if enabled and button_rect.collidepoint(pos):
                return action
        
        return None
    
    def handle_mouse_motion(self, pos: Tuple[int, int]):
        """Handle mouse motion for button hover effects and scrollbar dragging"""
        # Handle scrollbar dragging
        if self.scrollbar_dragging:
            self.handle_scrollbar_drag(pos)
        
        # Handle button hover effects
        self.hovered_button = None
        for button_rect, action, enabled in self.action_buttons:
            if enabled and button_rect.collidepoint(pos):
                self.hovered_button = action
                break 