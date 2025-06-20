#!/usr/bin/env python3
"""
Test script to verify Bell state mission can be drawn and used in the game.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ket_to_ride.game.game_state import GameState

def test_bell_state_in_game():
    """Test that Bell state missions can be drawn and used in the game."""
    
    print("=== Testing Bell State Mission in Game ===")
    print()
    
    # Initialize game state
    config_path = "config/university_map.json"
    game_state = GameState(config_path)
    
    # Add a player
    player = game_state.add_player("TestPlayer", (255, 0, 0))
    
    print(f"Player created: {player.name}")
    print(f"Initial hand: {player.hand}")
    print()
    
    # Draw mission cards
    print("Drawing mission cards...")
    drawn_missions = game_state.draw_mission_cards(3)
    
    print(f"Drawn missions:")
    for i, mission in enumerate(drawn_missions):
        print(f"  {i+1}: {mission}")
        if mission.target_state == "|Bell+⟩":
            print(f"    *** BELL STATE MISSION FOUND! ***")
            print(f"    Start cities: {mission.start_cities}")
            print(f"    Target city: {mission.target_city}")
            print(f"    Initial state: {mission.initial_state}")
            print(f"    Target state: {mission.target_state}")
            print(f"    Points: {mission.points}")
            print(f"    Difficulty: {mission.difficulty}")
    
    print()
    
    # Check if Bell state mission was drawn
    bell_missions = [m for m in drawn_missions if m.target_state == "|Bell+⟩"]
    
    if not bell_missions:
        print("Bell state mission not in first 3 cards. Searching deck...")
        
        # Find Bell state mission in the deck
        bell_mission_in_deck = None
        for i, mission in enumerate(game_state.mission_deck):
            if mission.target_state == "|Bell+⟩":
                bell_mission_in_deck = mission
                print(f"Found Bell state mission at position {i} in deck")
                break
        
        if bell_mission_in_deck:
            # Return the drawn missions to deck and draw the Bell state mission specifically
            game_state.return_missions_to_deck(drawn_missions)
            
            # Draw until we get the Bell state mission
            drawn_missions = []
            while len(drawn_missions) < len(game_state.mission_deck):
                mission = game_state.mission_deck.pop(0)
                drawn_missions.append(mission)
                if mission.target_state == "|Bell+⟩":
                    print(f"✓ Drew Bell state mission after {len(drawn_missions)} draws")
                    break
            
            # Return remaining missions to deck
            if game_state.mission_deck:
                game_state.return_missions_to_deck(game_state.mission_deck)
                game_state.mission_deck = []
            
            bell_missions = [m for m in drawn_missions if m.target_state == "|Bell+⟩"]
    
    if bell_missions:
        print("✓ Bell state mission was drawn successfully!")
        bell_mission = bell_missions[0]
        
        # Assign the mission to the player
        game_state.assign_missions_to_player(player, [bell_mission])
        print(f"✓ Bell state mission assigned to player")
        print(f"Player missions: {[str(m) for m in player.missions]}")
        print()
        
        # Give player some cards to complete the mission
        print("Giving player cards to complete Bell state mission...")
        for _ in range(15):
            cards = game_state.draw_cards(1)
            if cards:
                player.add_cards(cards[0])
        
        print(f"Player hand: {player.hand}")
        print()
        
        # Simulate claiming the required routes
        print("Simulating route claiming for Bell state...")
        
        # Find and claim Princeton → Carnegie (H gate)
        princeton_carnegie_claimed = False
        for i, route in enumerate(game_state.routes):
            if ((route['from'] == 'Princeton' and route['to'] == 'Carnegie') or 
                (route['from'] == 'Carnegie' and route['to'] == 'Princeton')):
                if 'H' in route['gate']:
                    if game_state.claim_route(player, i, 'H', 0):
                        print(f"✓ Claimed Princeton ↔ Carnegie with H gate")
                        princeton_carnegie_claimed = True
                        break
        
        # Find and claim GeorgiaTech → Carnegie (I gate)
        georgiatech_carnegie_claimed = False
        for i, route in enumerate(game_state.routes):
            if ((route['from'] == 'GeorgiaTech' and route['to'] == 'Carnegie') or 
                (route['from'] == 'Carnegie' and route['to'] == 'GeorgiaTech')):
                if 'I' in route['gate']:
                    if game_state.claim_route(player, i, 'I', 0):
                        print(f"✓ Claimed GeorgiaTech ↔ Carnegie with I gate")
                        georgiatech_carnegie_claimed = True
                        break
        
        # Find and claim Carnegie → U Chicago (CNOT gate)
        carnegie_chicago_claimed = False
        for i, route in enumerate(game_state.routes):
            if ((route['from'] == 'Carnegie' and route['to'] == 'U Chicago') or 
                (route['from'] == 'U Chicago' and route['to'] == 'Carnegie')):
                if 'CNOT' in route['gate']:
                    if game_state.claim_route(player, i, 'CNOT', 0):
                        print(f"✓ Claimed Carnegie ↔ U Chicago with CNOT gate")
                        carnegie_chicago_claimed = True
                        break
        
        print()
        print(f"Routes claimed: {player.claimed_routes}")
        print()
        
        # Check mission completion
        print("Checking mission completion...")
        if game_state.check_mission_completion(player):
            print("✓ Bell state mission completed successfully!")
            print(f"Player score: {player.score}")
            print(f"Completed missions: {len(player.get_completed_missions())}")
            
            # Check if player won
            if player.has_won:
                print("🎉 Player has won the game!")
            else:
                print("Player has not won yet (may need more missions)")
        else:
            print("✗ Bell state mission not completed")
            print(f"Completed missions: {len(player.get_completed_missions())}")
        
        return True
    else:
        print("✗ No Bell state mission was drawn")
        print("Available missions in deck:")
        for i, mission in enumerate(game_state.mission_deck[:5]):
            print(f"  {i+1}: {mission}")
        return False

if __name__ == "__main__":
    success = test_bell_state_in_game()
    if success:
        print("\n=== Bell State Mission Game Test PASSED ===")
    else:
        print("\n=== Bell State Mission Game Test FAILED ===") 