# Quantum Ticket-to-Ride

## Setup & Installation

1. Ensure you have Python 3.10+ installed
2. Install dependencies:
   ```bash
   pip install -e .
   ```

## Running the Game

To start the game with the Pygame interface:
```bash
python main.py
```

The game window will display:
- **Map Area**: Shows cities and quantum gate routes
- **Player Hand**: Displays your gate cards (I, X, Y, Z, H, CNOT)
- **Info Panel**: Shows current player, mission, and available actions

## Controls

- **ESC**: Exit game
- **Mouse**: Interact with UI elements (future implementation)

---

## Game Description
Game Concept
Players compete to build train-like “quantum circuits” on a map of cities. Each route between two cities is labeled with a quantum gate (I, X, Y, Z, H or CNOT) and a length (the number of gate applications required). To claim a route, a player discards gate cards matching the route’s gate type equal to its length, then places their marker on that route. Every mission starts with a single qubit in a specified initial state at a start city and ends with that qubit arriving in a specified target state at a target city. When a continuous path of claimed routes connects start to target, the player “runs” the circuit by applying each gate in turn (using a quantum simulator or hardware). If the final state matches the mission’s target, the player immediately wins.

Components

City Graph: A network of named nodes (cities) connected by edges (routes).

Routes: Each edge has:

A gate label (I, X, Y, Z, H or CNOT)

A length (an integer ≥ 1)

A claim marker (which player has claimed it, if any)

Gate Card Deck: Cards showing one of the six gate types.

Player Hands: Each player holds up to a fixed number of gate cards.

Mission Cards: One per player, each specifying:

A start city and an initial qubit state (|0⟩ or |1⟩)

A target city and a target qubit state (|0⟩ or |1⟩)

(In advanced missions, two-qubit targets or Bell-state goals are possible.)

Setup

Shuffle the gate-card deck and deal each player a starting hand (e.g. 5 cards).

Place the remaining cards face-down as a draw pile.

Each player draws one mission card and keeps it secret.

Unclaimed all routes on the board.

Determine play order by random draw.

Turn Structure
On a player’s turn they must choose one of two actions:

Draw Cards – take two cards from the face-down deck into their hand.

Claim Route – select any unclaimed route, discard from their hand exactly as many cards of that route’s gate type as the route’s length, and place their marker on that route.

After completing the chosen action, check for mission completion (see below). Then the turn passes to the next player.

Claiming Routes

A route of length N labeled “X” requires discarding exactly N X-gate cards.

Once claimed, the route remains marked and cannot be claimed again.

Claimed routes form each player’s circuit graph.

Mission Completion & Circuit Simulation
Whenever a player’s claimed routes contain at least one continuous path from their mission’s start city to its target city, that player may immediately simulate the quantum circuit formed by that path:

List the gates along the path in the order traveled.

Begin with the mission’s initial qubit state vector.

Sequentially apply each gate’s matrix to the state vector.

Compare the resulting state against the mission’s target state.

If they match (within numerical tolerance), that player wins the game at once.

If they do not match, play continues; the simulated route stays claimed but no win occurs.

Example Mission

Start: Berlin in state |0⟩

Target: Rome in state |1⟩

A valid path might be Berlin→Munich (X, length 1), Munich→Vienna (H, length 1), Vienna→Rome (Z, length 2). The player must have 1 X-card, 1 H-card, and 2 Z-cards to claim those routes. Upon claiming all three, they simulate X→H→Z→Z on |0⟩; if the result is |1⟩, they win.

Multiple Players & Conflicting Goals

Different players may have overlapping start or target cities but distinct missions (e.g. one needs |1⟩, another needs |0⟩).

Routes claimed by one player are blocked to others.

Strategic blocking and card management are key.

Game End and Victory
The first player to successfully simulate a path that produces their mission’s target state wins immediately. If the deck runs out and no one has won, compare partial progress or use a tie-breaker rule (e.g. most claimed route segments).

Play Modes

Local Turn-By-Turn: Two human players share a Pygame window.

Human vs. AI: One or more opponents may be a search-based bot that chooses optimal routes via A* search on city + state.

Client–Server Online: A central server process holds the master GameState; clients connect via WebSockets to send actions and receive updates.

Quantum Backend

Simulator: By default, gate applications and state measurements run on a local Qiskit simulator.

Real Hardware: When ready, the same circuits can be dispatched to an IBMQ device by swapping in the quantum/device.py backend.

Summary of Flow

Setup map, cards, missions, and hands.

Players alternate turns drawing cards or claiming routes by discarding matching gate cards.

Upon forming any continuous route from start to target, simulate the circuit: apply each route’s gate in sequence to the initial state.

If the final state equals the mission’s target state, that player wins immediately.

Otherwise play continues until a player succeeds or the deck is exhausted.

This description encapsulates all game elements, rules, turn flow, and quantum integration in plain text—ready for a coding AI to implement.