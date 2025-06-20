import time
from typing import Tuple, List, Optional
import pygame


class CardAnimation:
    """Handles card movement animations"""
    def __init__(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int], 
                 card_type, duration: float = 0.5, scale_effect: bool = True):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.card_type = card_type
        self.duration = duration
        self.start_time = time.time()
        self.completed = False
        self.scale_effect = scale_effect
        
        # Additional properties for animation management
        self.card_idx: Optional[int] = None
        
    def get_current_pos(self) -> Tuple[int, int]:
        """Get the current position of the card based on animation progress"""
        elapsed = time.time() - self.start_time
        progress = min(elapsed / self.duration, 1.0)
        
        # Use smooth easing function
        ease_progress = 1 - (1 - progress) ** 3  # Ease-out cubic
        
        x = self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * ease_progress
        y = self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * ease_progress
        
        return (int(x), int(y))
        
    def get_scale(self) -> float:
        """Get the current scale factor for the card (1.0 = normal size)"""
        if not self.scale_effect:
            return 1.0
            
        elapsed = time.time() - self.start_time
        progress = min(elapsed / self.duration, 1.0)
        
        # Scale up to 1.2x at 50% progress, then back to 1.0
        if progress < 0.5:
            scale_progress = progress * 2  # 0 to 1
            return 1.0 + 0.2 * scale_progress
        else:
            scale_progress = (progress - 0.5) * 2  # 0 to 1
            return 1.2 - 0.2 * scale_progress
        
    def is_finished(self) -> bool:
        """Check if animation is complete"""
        if self.completed:
            return True
        if time.time() - self.start_time >= self.duration:
            self.completed = True
        return self.completed


class AnimationManager:
    """Manages all animations in the game"""
    def __init__(self):
        self.card_animations: List[CardAnimation] = []
        self.new_card_animations: List[CardAnimation] = []
        self.deck_animation_start: Optional[float] = None
        
    def add_card_animation(self, animation: CardAnimation) -> None:
        """Add a card animation to the manager"""
        self.card_animations.append(animation)
        
    def add_new_card_animation(self, animation: CardAnimation) -> None:
        """Add a new card animation to the manager"""
        self.new_card_animations.append(animation)
        
    def set_deck_animation_start(self, start_time: float) -> None:
        """Set the deck animation start time"""
        self.deck_animation_start = start_time
        
    def clear_deck_animation_start(self) -> None:
        """Clear the deck animation start time"""
        self.deck_animation_start = None
        
    def get_completed_card_animations(self) -> List[CardAnimation]:
        """Get list of completed card animations"""
        return [anim for anim in self.card_animations if anim.is_finished()]
        
    def get_completed_new_card_animations(self) -> List[CardAnimation]:
        """Get list of completed new card animations"""
        return [anim for anim in self.new_card_animations if anim.is_finished()]
        
    def remove_completed_animations(self) -> None:
        """Remove all completed animations"""
        self.card_animations = [anim for anim in self.card_animations if not anim.is_finished()]
        self.new_card_animations = [anim for anim in self.new_card_animations if not anim.is_finished()]
        
    def is_card_being_animated(self, card_idx: int) -> bool:
        """Check if a specific card is currently being animated"""
        return any(anim.card_idx == card_idx for anim in self.card_animations)
        
    def get_all_animations(self) -> List[CardAnimation]:
        """Get all active animations"""
        return self.card_animations + self.new_card_animations
        
    def clear_all_animations(self) -> None:
        """Clear all animations"""
        self.card_animations.clear()
        self.new_card_animations.clear()
        self.deck_animation_start = None 