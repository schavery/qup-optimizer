# optimizer/visualizer.py
from typing import Dict, Tuple, List
from optimizer.evaluator import EvaluationResult
from data.nodes import NODES, MOVABLE_NODES


class ResultVisualizer:
    """Visualize optimization results"""

    @staticmethod
    def format_node_name(name: str, max_len: int = 12) -> str:
        """Abbreviate node names for display"""
        abbreviations = {
            'Angel': 'Ang',
            'Angel of Death': 'AoD',
            'Battle Medic': 'BMed',
            'Battle Hardened': 'BHard',
            'EMT': 'EMT',
            'Triage': 'Tria',
            'Panic': 'Pan',
            'Surgeon': 'Surg',
            'Focus': 'Foc',
            'Stimulant': 'Stim',
            'Extra Dose': 'ExDo',
            'Low Point': 'LowP',
            'Adrenaline': 'Adre',
            'Heroine': 'Hero',
            'Deployment': 'Depl',
            'Insurance Scam': 'Ins',
            'Funeral Rites': 'Fun',
            'Exhilaration': 'Exhi',
            'Stop the Bleeding': 'StB',
            'Big Sister': 'BigS',
        }
        return abbreviations.get(name, name[:max_len])

    @staticmethod
    def print_hex_grid(layout: Dict[str, Tuple[int, int, int]], radius: int = 8):
        """
        Print ASCII hex grid showing node positions

        Args:
            layout: Dict mapping movable node names to positions
            radius: Max radius to display
        """
        # Combine static and movable nodes
        all_positions = {}

        # Add static nodes
        for name, node_def in NODES.items():
            if node_def.upgrade_paths:  # Static
                all_positions[node_def.position] = name + "*"  # Mark static with *

        # Add movable nodes from layout
        for name, pos in layout.items():
            all_positions[pos] = name

        # Print grid
        print("\nHex Grid (radius {}):".format(radius))
        print("  Static nodes marked with *")
        print()

        # Print row by row
        for r in range(-radius, radius + 1):
            # Calculate q range for this row
            q_min = max(-radius, -radius - r)
            q_max = min(radius, radius - r)

            # Indent based on row
            indent = " " * abs(r) * 2

            row_str = indent
            for q in range(q_min, q_max + 1):
                s = -q - r
                pos = (q, r, s)

                if pos in all_positions:
                    name = all_positions[pos]
                    abbrev = ResultVisualizer.format_node_name(name, max_len=5)
                    row_str += f"[{abbrev:^5}]"
                else:
                    row_str += "[     ]"

            print(row_str)

        print()

    @staticmethod
    def print_outcome_spectrum(result: EvaluationResult):
        """
        Print table showing all 20 round outcomes and their Q values

        Args:
            result: EvaluationResult to display
        """
        print("\n=== Round Outcome Spectrum ===")
        print(f"Min Q: {result.min_q:,}")
        print(f"Max Q: {result.max_q:,}")
        print(f"Avg Q: {result.avg_q:,.0f}")
        print(f"Positive outcomes: {result.positive_outcomes}/{result.total_outcomes}")
        print()

        # Sort outcomes by sequence
        sorted_outcomes = sorted(result.outcomes.items())

        # Print table header
        print(f"{'Outcome':<10} {'Q Currency':>15} {'Status'}")
        print("-" * 40)

        # Print each outcome
        for sequence, q_value in sorted_outcomes:
            wins = sequence.count('W')
            losses = sequence.count('L')
            status = "WIN" if wins == 3 else "LOSS"

            # Highlight best and worst
            marker = ""
            if q_value == result.min_q:
                marker = " ← WORST"
            elif q_value == result.max_q:
                marker = " ← BEST"

            print(f"{sequence:<10} {q_value:>15,} {status}{marker}")

        print()

    @staticmethod
    def print_position_summary(result: EvaluationResult):
        """
        Print summary of node positions by ring

        Args:
            result: EvaluationResult to display
        """
        print("\n=== Node Positions by Ring ===")

        # Group by ring
        by_ring: Dict[int, List[str]] = {}
        for name, pos in result.layout.items():
            ring = max(abs(pos[0]), abs(pos[1]), abs(pos[2]))
            if ring not in by_ring:
                by_ring[ring] = []
            by_ring[ring].append(f"{name} {pos}")

        # Print each ring
        for ring in sorted(by_ring.keys()):
            print(f"\nRing {ring}:")
            for node_str in sorted(by_ring[ring]):
                print(f"  {node_str}")

        print()

    @staticmethod
    def print_top_candidates(results: List[EvaluationResult], top_n: int = 10):
        """
        Print summary of top N candidates

        Args:
            results: List of EvaluationResults (assumed sorted)
            top_n: Number of top candidates to display
        """
        print(f"\n{'='*60}")
        print(f"TOP {top_n} CANDIDATES (by worst-case Q)")
        print(f"{'='*60}\n")

        for i, result in enumerate(results[:top_n], 1):
            print(f"#{i}: Min Q: {result.min_q:,} | Avg Q: {result.avg_q:,.0f} | "
                  f"Max Q: {result.max_q:,} | Positive: {result.positive_outcomes}/{result.total_outcomes}")

        print()

    @staticmethod
    def print_detailed_result(result: EvaluationResult, rank: int = 1):
        """
        Print detailed analysis of a single result

        Args:
            result: EvaluationResult to display
            rank: Rank number in results (for display)
        """
        print(f"\n{'='*60}")
        print(f"DETAILED RESULT #{rank}")
        print(f"{'='*60}")

        ResultVisualizer.print_position_summary(result)
        ResultVisualizer.print_hex_grid(result.layout)
        ResultVisualizer.print_outcome_spectrum(result)
