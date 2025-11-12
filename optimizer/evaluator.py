# optimizer/evaluator.py
from typing import Dict, List, Tuple
from dataclasses import dataclass
from core.node import NodeDefinition
from simulator import Simulator
from data.nodes import NODES, MOVABLE_NODES
import copy


@dataclass
class EvaluationResult:
    """Results from evaluating a candidate layout"""
    layout: Dict[str, Tuple[int, int, int]]  # node name -> position
    outcomes: Dict[str, int]  # outcome sequence -> final Q
    min_q: int
    max_q: int
    avg_q: float
    positive_outcomes: int
    total_outcomes: int

    def __repr__(self):
        return (f"EvaluationResult(min_q={self.min_q}, max_q={self.max_q}, "
                f"avg_q={self.avg_q:.0f}, positive={self.positive_outcomes}/{self.total_outcomes})")


class LayoutEvaluator:
    """Evaluate candidate layouts by simulating all round outcomes"""

    def __init__(self, rank: int = 31, upgrade_configs: Dict[str, List[int]] = None):
        """
        Initialize evaluator

        Args:
            rank: Player rank (default 31 = Grandmaster 1)
            upgrade_configs: Optional upgrade levels for static nodes
        """
        self.rank = rank
        self.upgrade_configs = upgrade_configs or {}

    def create_node_definitions(self, layout: Dict[str, Tuple[int, int, int]]) -> Dict[str, NodeDefinition]:
        """
        Create complete node definitions with movable nodes positioned

        Args:
            layout: Dict mapping movable node names to positions

        Returns:
            Dict of all nodes (static + positioned movable)
        """
        node_defs = {}

        # Add all static nodes as-is
        for name, node_def in NODES.items():
            node_defs[name] = node_def

        # Add movable nodes with positions from layout
        for name, node_def in MOVABLE_NODES.items():
            if name in layout:
                # Create new NodeDefinition with updated position
                new_def = copy.deepcopy(node_def)
                new_def.position = layout[name]
                node_defs[name] = new_def

        return node_defs

    def evaluate_layout(self, layout: Dict[str, Tuple[int, int, int]]) -> EvaluationResult:
        """
        Evaluate a single layout by simulating all round outcomes

        Args:
            layout: Dict mapping movable node names to positions

        Returns:
            EvaluationResult with all metrics
        """
        # Create node definitions with positioned movable nodes
        node_defs = self.create_node_definitions(layout)

        # Create simulator with this layout
        sim = Simulator(node_defs, upgrade_configs=self.upgrade_configs)

        # Run all round outcomes with proper rank
        all_outcomes = sim.simulate_all_round_outcomes(rounds_to_win=3, max_flips=5, rank=self.rank)

        # Extract Q values
        q_values = []
        outcomes_dict = {}

        for sequence, game_state in all_outcomes.items():
            final_q = game_state.q_currency
            q_values.append(final_q)
            outcomes_dict[sequence] = final_q

        # Calculate metrics
        min_q = min(q_values)
        max_q = max(q_values)
        avg_q = sum(q_values) / len(q_values)
        positive_outcomes = sum(1 for q in q_values if q > 0)
        total_outcomes = len(q_values)

        return EvaluationResult(
            layout=layout,
            outcomes=outcomes_dict,
            min_q=min_q,
            max_q=max_q,
            avg_q=avg_q,
            positive_outcomes=positive_outcomes,
            total_outcomes=total_outcomes
        )

    def evaluate_batch(self, layouts: List[Dict[str, Tuple[int, int, int]]],
                      verbose: bool = False) -> List[EvaluationResult]:
        """
        Evaluate multiple layouts

        Args:
            layouts: List of layout dicts
            verbose: Print progress

        Returns:
            List of EvaluationResults, sorted by min_q (descending)
        """
        results = []

        for i, layout in enumerate(layouts):
            if verbose and (i + 1) % 10 == 0:
                print(f"Evaluated {i + 1}/{len(layouts)} candidates...")

            result = self.evaluate_layout(layout)
            results.append(result)

        # Sort by min_q (best worst-case first)
        results.sort(key=lambda r: r.min_q, reverse=True)

        return results
