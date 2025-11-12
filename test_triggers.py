# test_triggers.py
"""Quick test to see what triggers are firing"""

from optimizer.adjacency_generator import AdjacencyAwareGenerator
from optimizer.evaluator import LayoutEvaluator
from simulator import Simulator

# Generate one adjacency-aware layout
gen = AdjacencyAwareGenerator(seed=123)
layouts = gen.generate_candidates(1)
layout = layouts[0]

print("=== Testing Trigger Cascades ===\n")
print("Layout positions:")
for name, pos in sorted(layout.items(), key=lambda x: max(abs(x[1][0]), abs(x[1][1]), abs(x[1][2]))):
    ring = max(abs(pos[0]), abs(pos[1]), abs(pos[2]))
    print(f"  {name:20} at {pos} (ring {ring})")

# Check which nodes are adjacent to Panic
panic_pos = (-2, -1, 3)
from core.hex_grid import HexPosition
panic_hex = HexPosition(*panic_pos)
panic_neighbors = set(n.to_tuple() for n in panic_hex.neighbors())

print(f"\n=== Panic neighbors ===")
print(f"Panic at {panic_pos}")
for name, pos in layout.items():
    if pos in panic_neighbors:
        print(f"  ✓ {name} at {pos} IS ADJACENT")

# Create evaluator and test one flip
eval = LayoutEvaluator(rank=31, upgrade_configs={"Panic": [6], "EMT": [3, 2], "Triage": [2, 4]},
                       adjacency_generator=gen)

result = eval.evaluate_layout(layout)

print(f"\n=== Trigger Statistics ===")
print(f"Adjacency score: {result.adjacency_score}")
print(f"Max triggers per flip: {result.max_triggers_per_flip}")

print(f"\n=== Outcome Details ===")
for seq in ['LLL', 'WWW', 'LLWWL']:
    if seq in result.trigger_counts:
        triggers = result.trigger_counts[seq]
        q = result.outcomes[seq]
        flips = len(seq)
        print(f"{seq}: {triggers} total triggers ({triggers/flips:.1f} per flip), Q={q:,}")
