#!/usr/bin/env python3
"""
Script to create a topographic-style background image for testing.
In a real implementation, you would replace this with the actual map image.
"""

import pygame
import random
import math

def create_topographic_background(width=1400, height=900):
    # Initialize pygame
    pygame.init()
    
    # Create surface
    surface = pygame.Surface((width, height))
    
    # Earth tone colors inspired by topographic maps
    colors = [
        (85, 95, 82),    # Sage green
        (95, 105, 92),   # Lighter sage
        (75, 85, 72),    # Darker sage
        (105, 115, 102), # Light green
        (65, 75, 62),    # Dark green
        (120, 110, 95),  # Brown
        (140, 130, 115), # Light brown
        (100, 90, 75),   # Dark brown
    ]
    
    # Fill base color
    surface.fill((85, 95, 82))
    
    # Create organic patterns
    for i in range(200):
        # Random color
        color = random.choice(colors)
        
        # Random position and size
        x = random.randint(0, width)
        y = random.randint(0, height)
        radius = random.randint(20, 100)
        
        # Create irregular shape
        points = []
        num_points = random.randint(6, 12)
        for j in range(num_points):
            angle = (2 * math.pi * j) / num_points
            r = radius + random.randint(-15, 15)
            px = x + r * math.cos(angle)
            py = y + r * math.sin(angle)
            points.append((px, py))
        
        # Draw shape
        if len(points) > 2:
            pygame.draw.polygon(surface, color, points)
    
    # Add some linear features (like rivers or ridges)
    for i in range(20):
        color = random.choice(colors[:4])  # Use greener colors
        start_x = random.randint(0, width)
        start_y = random.randint(0, height)
        
        points = [(start_x, start_y)]
        x, y = start_x, start_y
        
        for j in range(random.randint(10, 30)):
            x += random.randint(-30, 30)
            y += random.randint(-30, 30)
            x = max(0, min(width, x))
            y = max(0, min(height, y))
            points.append((x, y))
        
        if len(points) > 1:
            pygame.draw.lines(surface, color, False, points, random.randint(3, 8))
    
    return surface

def main():
    print("Creating topographic background image...")
    
    # Create the background
    background = create_topographic_background()
    
    # Save the image
    pygame.image.save(background, "assets/topographic_map.jpg")
    print("Background image saved to assets/topographic_map.jpg")
    
    pygame.quit()

if __name__ == "__main__":
    main()