#!/usr/bin/env python3
"""Test Precision Cut node implementation"""

from data.nodes import ALL_NODES, NODES
from simulator import Simulator
from core.game_state import GameState
from core.layout import GridLayout

def test_precision_cut_basic():
    """Test that Precision Cut reduces Qdown based on depleted nodes"""

    # Create a layout with Precision Cut (upgrade it so it doesn't deplete immediately)
    # and EMT which triggers on loss with AVS=2
    layout = GridLayout(
        static_nodes={"Precision Cut": NODES["Precision Cut"], "EMT": NODES["EMT"]},
        movable_positions={},
        upgrade_configs={
            "Precision Cut": [0, 3],  # Upgrade AVS path to 1+1+2=4
            "EMT": [0, 0]  # AVS=2, will deplete after 2 losses
        }
    )

    sim = Simulator(ALL_NODES, layout)
    state = GameState(rank=31)  # Set a rank to get meaningful Qdown

    print("=== Test 1: First loss (no depleted nodes yet) ===")
    q_before_1 = state.q_currency
    state = sim.simulate_flip(state, win=False)
    q_gained_1 = state.q_currency - q_before_1
    print(f"Q gained: {q_gained_1}")

    # Check node states
    for pos, node in sim.nodes.items():
        print(f"  {node.definition.name}: triggered {node.times_triggered_this_flip}/{node.get_total_avs()} times")
    print()

    print("=== Test 2: Second loss (some nodes getting close to depletion) ===")
    q_before_2 = state.q_currency
    state = sim.simulate_flip(state, win=False)
    q_gained_2 = state.q_currency - q_before_2
    print(f"Q gained: {q_gained_2}")

    # Check node states after second loss
    for pos, node in sim.nodes.items():
        avs = node.get_total_avs()
        depleted = node.times_triggered_this_flip >= avs if avs else False
        status = "DEPLETED" if depleted else f"{node.times_triggered_this_flip}/{avs}"
        print(f"  {node.definition.name}: {status}")
    print()

    print("=== Test 3: Third loss (EMT and Battle Medic depleted) ===")
    q_before_3 = state.q_currency
    state = sim.simulate_flip(state, win=False)
    q_gained_3 = state.q_currency - q_before_3
    print(f"Q gained: {q_gained_3}")
    print(f"Expected boost: EMT and Battle Medic should be depleted → +1000 from Precision Cut (500 × 2)")

    # Check node states after third loss
    depleted_count = 0
    for pos, node in sim.nodes.items():
        avs = node.get_total_avs()
        depleted = node.times_triggered_this_flip >= avs if avs else False
        if depleted:
            depleted_count += 1
        status = "DEPLETED" if depleted else f"{node.times_triggered_this_flip}/{avs}"
        print(f"  {node.definition.name}: {status}")
    print(f"Total depleted nodes: {depleted_count}")
    print()

    print(f"=== Summary ===")
    print(f"Total Q Currency: {state.q_currency}")
    print(f"Total flips: {len(state.flip_history)}")
    print(f"Total triggers: {state.total_triggers}")


def test_precision_cut_upgrades():
    """Test that Precision Cut upgrades work correctly"""

    # Test with upgrades
    layout = GridLayout(
        static_nodes={"Precision Cut": NODES["Precision Cut"], "EMT": NODES["EMT"]},
        movable_positions={},
        upgrade_configs={
            "Precision Cut": [3, 0],  # Max first path: +750, +1000, +1250
            "EMT": [0, 0]
        }
    )

    sim = Simulator(ALL_NODES, layout)
    state = GameState(rank=31)

    print("=== Precision Cut with upgrades ===")

    # First two losses to deplete EMT (AVS=2)
    state = sim.simulate_flip(state, win=False)
    q_before = state.q_currency
    state = sim.simulate_flip(state, win=False)
    q_gained = state.q_currency - q_before

    print(f"Loss 2 Q gained: {q_gained}")

    # Third loss - EMT is depleted, Precision Cut should give boosted reduction
    q_before = state.q_currency
    state = sim.simulate_flip(state, win=False)
    q_gained = state.q_currency - q_before

    print(f"Loss 3 Q gained (with 1 depleted EMT): {q_gained}")
    print(f"Expected boost: Base 500 + upgrade 1250 = 1750 per depleted node")
    print(f"With 1 depleted node: +1750")

    # Check node states
    for pos, node in sim.nodes.items():
        avs = node.get_total_avs()
        depleted = node.times_triggered_this_flip >= avs if avs else False
        status = "DEPLETED" if depleted else f"{node.times_triggered_this_flip}/{avs}"
        print(f"  {node.definition.name}: {status}")


if __name__ == "__main__":
    test_precision_cut_basic()
    print("\n" + "="*60 + "\n")
    test_precision_cut_upgrades()
