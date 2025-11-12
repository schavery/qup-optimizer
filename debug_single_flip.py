# debug_single_flip.py
"""Debug a single flip to see exact trigger sequence"""

from optimizer.adjacency_generator import AdjacencyAwareGenerator
from core.game_state import GameState
from core.node import NodeInstance
from simulator import Simulator
from data.nodes import NODES, MOVABLE_NODES
import copy

# Generate one adjacency-aware layout
gen = AdjacencyAwareGenerator(seed=123)
layouts = gen.generate_candidates(1)
layout = layouts[0]

# Create node definitions
node_defs = {}
for name, node_def in NODES.items():
    node_defs[name] = node_def

for name, node_def in MOVABLE_NODES.items():
    if name in layout:
        new_def = copy.deepcopy(node_def)
        new_def.position = layout[name]
        node_defs[name] = new_def

# Create simulator with upgrades
upgrades = {"Panic": [6], "EMT": [3, 2], "Triage": [2, 4]}
sim = Simulator(node_defs, upgrade_configs=upgrades)

# Check what nodes are in the simulator
print("=== Nodes in Simulator ===")
for pos, node in sorted(sim.nodes.items()):
    ring = max(abs(pos[0]), abs(pos[1]), abs(pos[2]))
    avs = node.get_total_avs()
    print(f"{node.definition.name:20} at {pos} (ring {ring}, AVS={avs})")

# Check Panic's neighbors
panic_node = None
for pos, node in sim.nodes.items():
    if node.definition.name == "Panic":
        panic_node = node
        break

if panic_node:
    adjacent = sim.get_adjacent_nodes(panic_node)
    print(f"\n=== Panic's Adjacent Nodes ===")
    print(f"Panic at {panic_node.definition.position}")
    print(f"Found {len(adjacent)} adjacent nodes:")
    for adj in adjacent:
        print(f"  - {adj.definition.name} at {adj.definition.position}")

# Patch the trigger_node to log
original_trigger = sim.trigger_node
trigger_depth = 0

def logged_trigger(node: NodeInstance, game_state: GameState) -> GameState:
    global trigger_depth
    indent = "  " * trigger_depth
    avs = node.get_total_avs()
    remaining = avs - node.times_triggered_this_flip if avs else "∞"
    print(f"{indent}→ Triggering {node.definition.name} (AVS: {remaining} remaining)")

    trigger_depth += 1
    result = original_trigger(node, game_state)
    trigger_depth -= 1

    return result

sim.trigger_node = logged_trigger

# Simulate one loss flip
print("=== Simulating FIRST LOSS FLIP ===\n")
game_state = GameState(rank=31)
game_state = sim.simulate_flip(game_state, win=False)

print(f"\n=== Results ===")
print(f"Total triggers: {game_state.total_triggers}")
print(f"Q this flip (before mult): {game_state.q_this_flip}")
print(f"Qmult: {game_state.qmult}")
print(f"Final Q: {game_state.q_currency}")
