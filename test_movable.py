# test_movable.py
from simulator import Simulator
from core.layout import GridLayout
from data.nodes import NODES, ALL_NODES

def test_with_movable_nodes():
    """Test simulation with movable nodes placed"""

    # Create a layout with Angel next to Panic
    layout = GridLayout(
        static_nodes={name: defn for name, defn in NODES.items()},
        movable_positions={
            "Angel": (-1, -1, 2),  # Adjacent to Panic at (-2, -1, 3)
            "Exhilaration": (1, 0, -1),  # Somewhere on the grid
        },
        upgrade_configs={}
    )

    sim = Simulator(ALL_NODES, layout=layout, random_seed=42)

    print("=== Test with Angel + Exhilaration ===")
    print("Angel is adjacent to Panic")
    print()

    print("Test 1: Single loss (should trigger Angel via Panic)")
    game_state = sim.simulate_round([False])
    print(f"Q: {game_state.q_currency}, BB: {game_state.battle_bonus}")
    print()

    print("Test 2: Loss-Loss-Win sequence")
    game_state = sim.simulate_round([False, False, True])
    print(f"Q: {game_state.q_currency}, BB: {game_state.battle_bonus}")
    print()

    print("Test 3: All 3-win outcomes with movable nodes")
    all_outcomes = sim.simulate_all_round_outcomes(rounds_to_win=3, max_flips=5)
    for sequence, state in sorted(all_outcomes.items())[:10]:
        print(f"{sequence}: Q={state.q_currency}")

if __name__ == "__main__":
    test_with_movable_nodes()
