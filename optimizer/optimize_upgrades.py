#!/usr/bin/env python3
# optimizer/optimize_upgrades.py
"""
Find optimal upgrade point allocation for Grandmaster ranks

Usage:
    python -m optimizer.optimize_upgrades --budget 18 --top 10
"""

import argparse
from optimizer.upgrade_generator import UpgradeConfigGenerator
from optimizer.adjacency_generator import AdjacencyAwareGenerator
from optimizer.evaluator import LayoutEvaluator
from optimizer.visualizer import ResultVisualizer


def main():
    parser = argparse.ArgumentParser(description='Optimize upgrade point spending')
    parser.add_argument('--budget', type=int, default=18,
                       help='Total upgrade points available (default: 18)')
    parser.add_argument('--rank', type=int, default=31,
                       help='Player rank (default: 31 = Grandmaster 1)')
    parser.add_argument('--top', type=int, default=10,
                       help='Number of top upgrade configs to show (default: 10)')
    parser.add_argument('--layouts-per-config', type=int, default=5,
                       help='Position layouts to test per upgrade config (default: 5)')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed for reproducibility (default: 42)')
    parser.add_argument('--strategy', type=str, default='tiered',
                       choices=['tiered', 'exhaustive'],
                       help='Generation strategy: tiered (smart sampling) or exhaustive (all configs)')

    args = parser.parse_args()

    print(f"\n{'='*70}")
    print(f"UPGRADE POINT OPTIMIZER")
    print(f"{'='*70}")
    print(f"Budget: {args.budget} points")
    print(f"Rank: {args.rank} (Grandmaster {args.rank - 30})")
    print(f"Strategy: {args.strategy}")
    print()

    # Step 1: Generate upgrade configurations
    print("Step 1: Generating upgrade configurations...")
    gen = UpgradeConfigGenerator()

    if args.strategy == 'tiered':
        configs = gen.generate_tiered_configs(budget=args.budget, num_samples=100)
    else:
        configs = gen.generate_all_configs(budget=args.budget, min_panic_avs=4)

    print(f"Generated {len(configs)} upgrade configurations to test\n")

    # Step 2: Evaluate each upgrade config
    print(f"Step 2: Evaluating upgrade configs...")
    print(f"  Testing {args.layouts_per_config} position layouts per upgrade config")
    print(f"  Total evaluations: {len(configs) * args.layouts_per_config}")
    print()

    position_gen = AdjacencyAwareGenerator(seed=args.seed)
    results = []

    for i, upgrade_config in enumerate(configs):
        if (i + 1) % 10 == 0:
            print(f"  Evaluated {i + 1}/{len(configs)} upgrade configs...")

        # Generate position layouts
        layouts = position_gen.generate_candidates(args.layouts_per_config)

        # Evaluate with this upgrade config
        evaluator = LayoutEvaluator(
            rank=args.rank,
            upgrade_configs=upgrade_config,
            adjacency_generator=position_gen
        )

        layout_results = evaluator.evaluate_batch(layouts, verbose=False)

        # Keep best layout for this upgrade config
        if layout_results:
            best_layout_result = layout_results[0]  # Already sorted
            results.append({
                'upgrade_config': upgrade_config,
                'result': best_layout_result,
                'min_q': best_layout_result.min_q,
                'avg_q': best_layout_result.avg_q,
                'max_q': best_layout_result.max_q,
                'max_triggers': best_layout_result.max_triggers_per_flip,
                'adjacency_score': best_layout_result.adjacency_score,
                'efficiency': best_layout_result.avg_efficiency,
            })

    print(f"Evaluation complete!\n")

    # Step 3: Rank and display results
    print("Step 3: Ranking upgrade configurations...")

    # Sort by min_q (best worst-case), then efficiency, then max_triggers, then avg_q
    results.sort(key=lambda r: (r['min_q'], r['efficiency'], r['max_triggers'], r['avg_q']), reverse=True)

    # Display top configs
    print(f"\n{'='*70}")
    print(f"TOP {args.top} UPGRADE CONFIGURATIONS")
    print(f"{'='*70}\n")

    for i, res in enumerate(results[:args.top], 1):
        print(f"#{i}: Min Q: {res['min_q']:,} | Avg Q: {res['avg_q']:,.0f} | Max Q: {res['max_q']:,}")
        print(f"    Efficiency: {res['efficiency']*100:.1f}% | Max Triggers/Flip: {res['max_triggers']} | Adjacency: {res['adjacency_score']:.1f}")
        print(f"\n{gen.config_summary(res['upgrade_config'])}\n")

    # Show detailed view of #1
    if results:
        print(f"\n{'='*70}")
        print(f"DETAILED VIEW: BEST UPGRADE CONFIGURATION")
        print(f"{'='*70}\n")

        best = results[0]
        print(gen.config_summary(best['upgrade_config']))
        print(f"\nWith optimal position layout:")
        ResultVisualizer.print_position_summary(best['result'])
        ResultVisualizer.print_hex_grid(best['result'].layout)
        ResultVisualizer.print_outcome_spectrum(best['result'])

    # Summary
    print(f"\n{'='*70}")
    print("OPTIMIZATION SUMMARY")
    print(f"{'='*70}")
    if results:
        print(f"Best min Q: {results[0]['min_q']:,}")
        print(f"Best avg Q: {max(r['avg_q'] for r in results):,.0f}")
        print(f"Best max Q: {max(r['max_q'] for r in results):,}")
        print(f"Best trigger count: {max(r['max_triggers'] for r in results)} per flip")

        if results[0]['min_q'] >= 0:
            print("\n✓ Found upgrade configs with NON-NEGATIVE worst-case Q!")
        else:
            print("\n✗ All configs have negative worst-case Q at this rank")
            print(f"  Best worst-case: {results[0]['min_q']:,}")
            print(f"  Consider: more upgrade points, lower rank, or different strategy")

    print()


if __name__ == "__main__":
    main()
