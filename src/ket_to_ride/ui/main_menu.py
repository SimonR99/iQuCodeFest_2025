import pygame
import sys
import os
from typing import Optional
from .game_window import GameWindow

class MainMenu:
    def __init__(self, width: int = 1280, height: int = 720):
        self.width = width
        self.height = height
        self.screen: Optional[pygame.Surface] = None
        self.clock = pygame.time.Clock()
        self.running = False
        
        # Colors (earth tones matching topographic map)
        self.BACKGROUND_COLOR = (45, 52, 48)        # Dark forest green
        self.TITLE_COLOR = (250, 248, 240)          # Warm white
        self.BUTTON_COLOR = (68, 75, 65)            # Darker sage
        self.BUTTON_HOVER_COLOR = (85, 95, 82)      # Muted sage green
        self.BUTTON_TEXT_COLOR = (250, 248, 240)    # Warm white
        self.BUTTON_DISABLED_COLOR = (55, 60, 52)   # Very dark green
        self.BUTTON_DISABLED_TEXT_COLOR = (120, 110, 95)  # Muted brown
        
        # Menu state
        self.selected_button = 0
        self.buttons = [
            {"text": "Local Game", "enabled": True, "action": "local"},
            {"text": "Online Game", "enabled": False, "action": "online"},
            {"text": "Settings", "enabled": False, "action": "settings"},
            {"text": "Exit", "enabled": True, "action": "exit"}
        ]
        
        # Background image
        self.background_image = None
        self.load_background_image()
        
    def initialize(self) -> bool:
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("|ket> to ride - Main Menu")
        
        # Initialize fonts
        pygame.font.init()
        self.title_font = pygame.font.Font(None, 76)
        self.subtitle_font = pygame.font.Font(None, 36)
        self.button_font = pygame.font.Font(None, 42)
        self.small_font = pygame.font.Font(None, 24)
        
        return True
        
    def load_background_image(self):
        """Load the topographic map background image"""
        try:
            # Try to load the map image
            image_path = os.path.join("assets", "map.jpg")
            if os.path.exists(image_path):
                self.background_image = pygame.image.load(image_path)
                print(f"Loaded background image: {image_path}")
            else:
                print(f"Background image not found: {image_path}")
                self.background_image = None
        except Exception as e:
            print(f"Error loading background image: {e}")
            self.background_image = None
        
    def handle_events(self) -> Optional[str]:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "exit"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "exit"
                elif event.key == pygame.K_UP:
                    self.selected_button = (self.selected_button - 1) % len(self.buttons)
                elif event.key == pygame.K_DOWN:
                    self.selected_button = (self.selected_button + 1) % len(self.buttons)
                elif event.key == pygame.K_RETURN:
                    if self.buttons[self.selected_button]["enabled"]:
                        return self.buttons[self.selected_button]["action"]
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    return self.handle_mouse_click(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                self.handle_mouse_hover(event.pos)
                
        return None
        
    def handle_mouse_click(self, pos) -> Optional[str]:
        button_width = 300
        button_height = 60
        button_spacing = 20
        start_y = self.height // 2 - 20
        
        for i, button in enumerate(self.buttons):
            button_x = self.width // 2 - button_width // 2
            button_y = start_y + i * (button_height + button_spacing)
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            
            if button_rect.collidepoint(pos) and button["enabled"]:
                return button["action"]
                
        return None
        
    def handle_mouse_hover(self, pos):
        button_width = 300
        button_height = 60
        button_spacing = 20
        start_y = self.height // 2 - 80
        
        self.selected_button = -1  # No selection by default
        
        for i, button in enumerate(self.buttons):
            button_x = self.width // 2 - button_width // 2
            button_y = start_y + i * (button_height + button_spacing)
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            
            if button_rect.collidepoint(pos):
                self.selected_button = i
                break
                
    def draw(self):
        # Draw background image if available, otherwise fill with color
        if self.background_image:
            # Scale background image to fit screen
            scaled_bg = pygame.transform.scale(self.background_image, (self.width, self.height))
            self.screen.blit(scaled_bg, (0, 0))
            
            # Add semi-transparent overlay to make text readable
            overlay = pygame.Surface((self.width, self.height))
            overlay.set_alpha(120)  # Semi-transparent
            overlay.fill(self.BACKGROUND_COLOR)
            self.screen.blit(overlay, (0, 0))
        else:
            self.screen.fill(self.BACKGROUND_COLOR)
        
        # Draw title
        title_text = self.title_font.render("|ket> to ride", True, self.TITLE_COLOR)
        title_rect = title_text.get_rect(center=(self.width // 2, self.height // 5))
        self.screen.blit(title_text, title_rect)
        
        # Draw subtitle
        subtitle_text = self.subtitle_font.render("Quantum Train Adventure", True, self.TITLE_COLOR)
        subtitle_rect = subtitle_text.get_rect(center=(self.width // 2, self.height // 5 + 80))
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Draw buttons
        button_width = 300
        button_height = 60
        button_spacing = 20
        start_y = self.height // 2 - 80
        
        for i, button in enumerate(self.buttons):
            button_x = self.width // 2 - button_width // 2
            button_y = start_y + i * (button_height + button_spacing)
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            
            # Choose button color
            if not button["enabled"]:
                color = self.BUTTON_DISABLED_COLOR
                text_color = self.BUTTON_DISABLED_TEXT_COLOR
            elif i == self.selected_button:
                color = self.BUTTON_HOVER_COLOR
                text_color = self.BUTTON_TEXT_COLOR
            else:
                color = self.BUTTON_COLOR
                text_color = self.BUTTON_TEXT_COLOR
            
            # Draw button
            pygame.draw.rect(self.screen, color, button_rect)
            pygame.draw.rect(self.screen, (100, 100, 100), button_rect, 2)
            
            # Draw button text
            button_text = self.button_font.render(button["text"], True, text_color)
            text_rect = button_text.get_rect(center=button_rect.center)
            self.screen.blit(button_text, text_rect)
            
            # Draw "Coming Soon" for disabled buttons
            if not button["enabled"]:
                coming_soon = self.small_font.render("Coming Soon", True, self.BUTTON_DISABLED_TEXT_COLOR)
                coming_rect = coming_soon.get_rect(center=(button_rect.centerx, button_rect.bottom - 11))
                self.screen.blit(coming_soon, coming_rect)
        
        # Draw instructions
        instructions = [
            "Use arrow keys and ENTER to navigate",
            "Or click with mouse",
            "",
            "ESC to exit"
        ]
        
        y_offset = self.height - 120
        for instruction in instructions:
            if instruction:
                text = self.small_font.render(instruction, True, (150, 150, 150))
                text_rect = text.get_rect(center=(self.width // 2, y_offset))
                self.screen.blit(text, text_rect)
            y_offset += 25
        
        pygame.display.flip()
        
    def run(self) -> Optional[str]:
        if not self.initialize():
            return None
            
        self.running = True
        
        while self.running:
            action = self.handle_events()
            if action:
                if action == "local":
                    pygame.quit()
                    # Launch the game
                    game_window = GameWindow()
                    game_window.run()
                    return "local"
                elif action == "exit":
                    self.running = False
                    pygame.quit()
                    return "exit"
                elif action in ["online", "settings"]:
                    # These are not implemented yet
                    continue
                    
            self.draw()
            self.clock.tick(60)
            
        pygame.quit()
        return None