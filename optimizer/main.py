#!/usr/bin/env python3
# optimizer/main.py
"""
Grandmaster Rank Optimizer

Finds optimal positions for movable nodes to maximize Q at high ranks
where Qdown penalties are extreme (-700K at GM1).

Strategy:
- Place Angel in outermost rings to trigger last (captures all Qdown prevention)
- Place Qdown prevention nodes (EMT, Triage) in inner rings to trigger first
- Evaluate all 20 possible round outcomes (best of 5)
"""

import argparse
from typing import Dict, List
from optimizer.candidate_generator import CandidateGenerator
from optimizer.adjacency_generator import AdjacencyAwareGenerator
from optimizer.evaluator import LayoutEvaluator
from optimizer.visualizer import ResultVisualizer


def main():
    parser = argparse.ArgumentParser(description='Optimize skill tree positions for Grandmaster ranks')
    parser.add_argument('--candidates', type=int, default=100,
                       help='Number of candidate layouts to generate (default: 100)')
    parser.add_argument('--rank', type=int, default=31,
                       help='Player rank (default: 31 = Grandmaster 1)')
    parser.add_argument('--top', type=int, default=10,
                       help='Number of top results to display (default: 10)')
    parser.add_argument('--detailed', type=int, default=3,
                       help='Number of detailed results to show (default: 3)')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed for reproducibility (default: 42)')
    parser.add_argument('--upgrades', type=str, default=None,
                       help='Upgrade config as JSON (optional)')

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"GRANDMASTER RANK OPTIMIZER")
    print(f"{'='*60}")
    print(f"Rank: {args.rank} (Grandmaster {args.rank - 30})")
    print(f"Generating {args.candidates} candidate layouts...")
    print(f"Random seed: {args.seed}")
    print()

    # Parse upgrade config if provided
    upgrade_configs = None
    if args.upgrades:
        import json
        upgrade_configs = json.loads(args.upgrades)

    # Step 1: Generate candidates with adjacency awareness
    print("Step 1: Generating candidates with trigger clustering around Panic...")
    generator = AdjacencyAwareGenerator(max_radius=8, seed=args.seed)
    candidates = generator.generate_candidates(num_candidates=args.candidates)
    print(f"Generated {len(candidates)} valid layouts\n")

    # Step 2: Evaluate candidates with adjacency scoring
    print("Step 2: Evaluating all candidates...")
    evaluator = LayoutEvaluator(rank=args.rank, upgrade_configs=upgrade_configs,
                                adjacency_generator=generator)
    results = evaluator.evaluate_batch(candidates, verbose=True)
    print(f"Evaluation complete!\n")

    # Step 3: Display results
    print("Step 3: Analyzing results...")

    # Show top candidates summary
    ResultVisualizer.print_top_candidates(results, top_n=args.top)

    # Show detailed results for top N
    for i in range(min(args.detailed, len(results))):
        ResultVisualizer.print_detailed_result(results[i], rank=i+1)

    # Final summary
    print(f"\n{'='*60}")
    print("OPTIMIZATION SUMMARY")
    print(f"{'='*60}")
    print(f"Best worst-case Q: {results[0].min_q:,}")
    print(f"Best average Q: {max(r.avg_q for r in results):,.0f}")
    print(f"Best max Q: {max(r.max_q for r in results):,}")

    if results[0].min_q >= 0:
        print("\n✓ Found configurations with NON-NEGATIVE worst-case Q!")
        print("  This layout can survive all round outcomes at this rank.")
    else:
        print("\n✗ All configurations have negative worst-case Q")
        print("  Even the best layout will lose Q in some scenarios.")
        print(f"  Consider: upgrading nodes, lowering rank target, or adjusting strategy.")

    print()


if __name__ == "__main__":
    main()
