import pygame
import sys
from typing import Optional, Tuple

class GameWindow:
    def __init__(self, width: int = 1200, height: int = 800):
        self.width = width
        self.height = height
        self.screen: Optional[pygame.Surface] = None
        self.clock = pygame.time.Clock()
        self.running = False
        
        # Colors
        self.BACKGROUND_COLOR = (30, 30, 40)
        self.MAP_COLOR = (50, 50, 60)
        self.CARD_AREA_COLOR = (40, 40, 50)
        self.INFO_PANEL_COLOR = (35, 35, 45)
        self.BORDER_COLOR = (100, 100, 120)
        self.TEXT_COLOR = (255, 255, 255)
        
        # UI Layout
        self.map_rect = pygame.Rect(10, 10, 800, 600)
        self.card_area_rect = pygame.Rect(10, 620, 800, 170)
        self.info_panel_rect = pygame.Rect(820, 10, 370, 780)
        
    def initialize(self) -> bool:
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Quantum Ticket-to-Ride")
        
        # Initialize font
        pygame.font.init()
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)
        
        return True
    
    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
    
    def draw_map_area(self) -> None:
        pygame.draw.rect(self.screen, self.MAP_COLOR, self.map_rect)
        pygame.draw.rect(self.screen, self.BORDER_COLOR, self.map_rect, 2)
        
        # Draw placeholder text
        text = self.font.render("Map Area - Cities and Routes", True, self.TEXT_COLOR)
        text_rect = text.get_rect(center=(self.map_rect.centerx, self.map_rect.centery))
        self.screen.blit(text, text_rect)
    
    def draw_card_area(self) -> None:
        pygame.draw.rect(self.screen, self.CARD_AREA_COLOR, self.card_area_rect)
        pygame.draw.rect(self.screen, self.BORDER_COLOR, self.card_area_rect, 2)
        
        # Draw placeholder text
        text = self.font.render("Player Hand - Gate Cards", True, self.TEXT_COLOR)
        text_rect = text.get_rect(center=(self.card_area_rect.centerx, self.card_area_rect.centery))
        self.screen.blit(text, text_rect)
    
    def draw_info_panel(self) -> None:
        pygame.draw.rect(self.screen, self.INFO_PANEL_COLOR, self.info_panel_rect)
        pygame.draw.rect(self.screen, self.BORDER_COLOR, self.info_panel_rect, 2)
        
        # Draw title
        title_text = self.title_font.render("Game Info", True, self.TEXT_COLOR)
        title_rect = title_text.get_rect(centerx=self.info_panel_rect.centerx, y=self.info_panel_rect.y + 20)
        self.screen.blit(title_text, title_rect)
        
        # Draw placeholder info
        info_lines = [
            "Current Player: Player 1",
            "Turn: 1",
            "",
            "Mission:",
            "Start: Berlin |0⟩",
            "Target: Rome |1⟩",
            "",
            "Actions:",
            "1. Draw Cards",
            "2. Claim Route"
        ]
        
        y_offset = 80
        for line in info_lines:
            if line:
                text = self.font.render(line, True, self.TEXT_COLOR)
                self.screen.blit(text, (self.info_panel_rect.x + 20, self.info_panel_rect.y + y_offset))
            y_offset += 30
    
    def draw(self) -> None:
        self.screen.fill(self.BACKGROUND_COLOR)
        
        self.draw_map_area()
        self.draw_card_area()
        self.draw_info_panel()
        
        pygame.display.flip()
    
    def run(self) -> None:
        if not self.initialize():
            return
        
        self.running = True
        
        while self.running:
            self.handle_events()
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

def main():
    game_window = GameWindow()
    game_window.run()

if __name__ == "__main__":
    main()