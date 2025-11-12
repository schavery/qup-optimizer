#!/usr/bin/env python3
# debug_panic_efficiency.py
"""
Analyze how efficiently Panic's AVS is being used

Shows:
- How many times Panic actually triggers
- How many adjacent nodes it triggers each time
- How many of those triggers hit depleted nodes (wasted)
"""

from optimizer.adjacency_generator import AdjacencyAwareGenerator
from optimizer.evaluator import LayoutEvaluator
from core.layout import GridLayout
from simulator import Simulator
from data.nodes import NODES, MOVABLE_NODES
from core.game_state import GameState

# Test configuration
upgrade_config = {
    'Panic': [6, 0],  # 7 AVS total
    'EMT': [3, 3],
    'Stop the Bleeding': [3, 0],
    'Battle Medic': [0, 2],
    'Triage': [1, 0],
    'Self Diagnosis': [0, 0],
    'Big Sister': [0, 0],
}

# Generate one good layout
gen = AdjacencyAwareGenerator(seed=123)
layouts = gen.generate_candidates(1)
layout = layouts[0]

# Create simulator
grid_layout = GridLayout(
    static_nodes=NODES,
    movable_positions=layout,
    upgrade_configs=upgrade_config
)
all_node_defs = {**NODES, **MOVABLE_NODES}
sim = Simulator(all_node_defs, layout=grid_layout)

# Find Panic node
panic_node = None
for node in sim.nodes.values():
    if node.definition.name == "Panic":
        panic_node = node
        break

print("=" * 70)
print("PANIC EFFICIENCY ANALYSIS")
print("=" * 70)
print(f"Panic AVS: {panic_node.get_total_avs()}")
print(f"Panic position: {panic_node.definition.position}")

# Get adjacent nodes
adjacent_nodes = sim.get_adjacent_nodes(panic_node)
print(f"\nPanic has {len(adjacent_nodes)} adjacent nodes:")
for adj in adjacent_nodes:
    avs = adj.get_total_avs()
    print(f"  - {adj.definition.name:20} AVS: {avs if avs else '∞'}")

# Simulate one loss flip with detailed tracking
print("\n" + "=" * 70)
print("SIMULATING SINGLE LOSS FLIP")
print("=" * 70)

# Patch Panic's handler to track triggers
original_handle_panic = sim.handle_panic
panic_trigger_log = []

def logged_handle_panic(panic_node_arg, game_state):
    adjacent = sim.get_adjacent_nodes(panic_node_arg)

    trigger_info = {
        'panic_triggers_remaining': panic_node_arg.get_total_avs() - panic_node_arg.times_triggered_this_flip,
        'adjacent_triggered': [],
        'depleted_count': 0,
    }

    for adj in adjacent:
        avs_remaining = None
        total_avs = adj.get_total_avs()
        if total_avs is not None:
            avs_remaining = total_avs - adj.times_triggered_this_flip

        is_depleted = avs_remaining is not None and avs_remaining <= 0

        trigger_info['adjacent_triggered'].append({
            'name': adj.definition.name,
            'avs_remaining': avs_remaining if avs_remaining is not None else '∞',
            'depleted': is_depleted
        })

        if is_depleted:
            trigger_info['depleted_count'] += 1

    panic_trigger_log.append(trigger_info)

    return original_handle_panic(panic_node_arg, game_state)

sim.handle_panic = logged_handle_panic

# Run simulation
game_state = GameState(rank=31)
game_state = sim.simulate_flip(game_state, win=False)

# Print results
print(f"\nPanic triggered {len(panic_trigger_log)} times during the flip")
print(f"Total triggers in flip: {game_state.total_triggers}\n")

for i, log in enumerate(panic_trigger_log, 1):
    print(f"Panic Trigger #{i} (AVS remaining: {log['panic_triggers_remaining']})")
    print(f"  Triggered {len(log['adjacent_triggered'])} adjacent nodes:")

    for adj_info in log['adjacent_triggered']:
        status = "DEPLETED ✗" if adj_info['depleted'] else f"AVS: {adj_info['avs_remaining']}"
        print(f"    - {adj_info['name']:20} {status}")

    if log['depleted_count'] > 0:
        print(f"  ⚠ {log['depleted_count']}/{len(log['adjacent_triggered'])} triggers WASTED on depleted nodes")
    print()

# Calculate efficiency
total_panic_triggers = len(panic_trigger_log)
total_adjacent_triggers = sum(len(log['adjacent_triggered']) for log in panic_trigger_log)
total_depleted_triggers = sum(log['depleted_count'] for log in panic_trigger_log)
total_useful_triggers = total_adjacent_triggers - total_depleted_triggers

efficiency = (total_useful_triggers / total_adjacent_triggers * 100) if total_adjacent_triggers > 0 else 0

print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Panic AVS: {panic_node.get_total_avs()}")
print(f"Panic actually triggered: {total_panic_triggers} times")
print(f"Adjacent nodes triggered: {total_adjacent_triggers} total")
print(f"Useful triggers: {total_useful_triggers}")
print(f"Wasted on depleted: {total_depleted_triggers}")
print(f"Efficiency: {efficiency:.1f}%")
print()

if total_panic_triggers < panic_node.get_total_avs():
    unused = panic_node.get_total_avs() - total_panic_triggers
    print(f"⚠ Panic has {unused} UNUSED AVS - consider reducing Panic upgrades")
elif total_depleted_triggers > 0:
    print(f"⚠ {total_depleted_triggers} triggers wasted on depleted nodes")
    print(f"  → Consider: upgrading adjacent nodes' AVS or repositioning")
else:
    print(f"✓ All Panic triggers were useful!")
