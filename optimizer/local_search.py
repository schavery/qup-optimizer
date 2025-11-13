# optimizer/local_search.py
"""Local search refinement for iteratively improving grid layouts"""
from typing import Dict, List, Tuple, Optional
import random
from optimizer.layout_ops import (
    swap_nodes, rotate_cluster, get_cluster_nodes, is_valid_layout,
    get_neighbors, hex_distance
)
from data.nodes import NODES


class LocalSearchRefiner:
    """
    Iteratively improve layouts using local search with domain knowledge

    Key optimization goals:
    1. Trigger chains near EMT/Battle Medic -> reduce Qdown
    2. Trigger chains far from Angel -> delay Angel, maximize Qup before it fires
    3. Trigger clustering -> maximize cascade potential
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

        # Load static node positions from data
        self.panic_position = NODES['Panic'].position
        self.emt_position = NODES['EMT'].position
        self.battle_medic_position = NODES['Battle Medic'].position

        # Trigger nodes that create chains
        self.trigger_nodes = [
            'Low Point',      # Triggers 2 adjacent per loss
            'Adrenaline',     # Triggers 1-2 adjacent based on BB
            'Focus',          # Triggers 1 random adjacent
            'Stimulant',      # Triggers adjacent with most AVS
            'Extra Dose',     # Triggers adjacent with most AVS
        ]

        # Angel should be in trigger chain (triggers on loss, benefits from being triggered)
        self.angel_node = 'Angel'

        # High-value nodes
        self.high_value_nodes = [
            'Surgeon',        # Triggers highest AVS globally
            'Angel of Death', # Causes losses
        ]

    def refine_layout(self,
                      initial_layout: Dict[str, Tuple[int, int, int]],
                      evaluator,
                      max_iterations: int = 50,
                      early_stop_threshold: int = 10) -> Dict[str, Tuple[int, int, int]]:
        """
        Refine a layout using local search

        Args:
            initial_layout: Starting layout
            evaluator: LayoutEvaluator instance with cached evaluate_layout method
            max_iterations: Maximum refinement iterations
            early_stop_threshold: Stop if no improvement for N iterations

        Returns:
            Best layout found
        """
        current_layout = initial_layout.copy()
        current_result = evaluator.evaluate_layout(current_layout)
        best_layout = current_layout.copy()
        best_result = current_result

        iterations_without_improvement = 0

        if self.verbose:
            print(f"\n=== Local Search Refinement ===")
            print(f"Initial: min_q={current_result.min_q}, avg_q={current_result.avg_q:.0f}, "
                  f"adjacency={current_result.adjacency_score:.1f}")

        for iteration in range(max_iterations):
            improved = False

            # Try all improvement operations
            # 1. Pairwise swaps
            swap_candidates = self._generate_swap_candidates(current_layout)
            for new_layout in swap_candidates:
                if new_layout is None:
                    continue

                new_result = evaluator.evaluate_layout(new_layout)

                # Check if improvement (prioritize min_q, then avg_efficiency, then avg_q)
                if self._is_better(new_result, best_result):
                    best_layout = new_layout.copy()
                    best_result = new_result
                    current_layout = new_layout.copy()
                    current_result = new_result
                    improved = True

                    if self.verbose:
                        print(f"  Iter {iteration+1}: SWAP improved -> min_q={new_result.min_q}, "
                              f"avg_q={new_result.avg_q:.0f}, adjacency={new_result.adjacency_score:.1f}")
                    break  # Take first improvement (greedy)

            # 2. Cluster rotations around Panic
            if not improved:
                rotation_candidates = self._generate_rotation_candidates(current_layout)
                for new_layout in rotation_candidates:
                    if new_layout is None:
                        continue

                    new_result = evaluator.evaluate_layout(new_layout)

                    if self._is_better(new_result, best_result):
                        best_layout = new_layout.copy()
                        best_result = new_result
                        current_layout = new_layout.copy()
                        current_result = new_result
                        improved = True

                        if self.verbose:
                            print(f"  Iter {iteration+1}: ROTATION improved -> min_q={new_result.min_q}, "
                                  f"avg_q={new_result.avg_q:.0f}, adjacency={new_result.adjacency_score:.1f}")
                        break  # Take first improvement (greedy)

            # Track iterations without improvement
            if improved:
                iterations_without_improvement = 0
            else:
                iterations_without_improvement += 1

            # Early stopping
            if iterations_without_improvement >= early_stop_threshold:
                if self.verbose:
                    print(f"  Early stop at iteration {iteration+1} (no improvement for {early_stop_threshold} iters)")
                break

        if self.verbose:
            improvement = best_result.min_q - evaluator.evaluate_layout(initial_layout).min_q
            print(f"Final: min_q={best_result.min_q} (+{improvement}), "
                  f"avg_q={best_result.avg_q:.0f}, adjacency={best_result.adjacency_score:.1f}")

        return best_layout

    def _is_better(self, result1, result2) -> bool:
        """
        Compare two results (follows evaluator sorting criteria)

        Priority: min_q > avg_efficiency > adjacency_score > avg_q
        """
        if result1.min_q != result2.min_q:
            return result1.min_q > result2.min_q

        if abs(result1.avg_efficiency - result2.avg_efficiency) > 0.001:
            return result1.avg_efficiency > result2.avg_efficiency

        if abs(result1.adjacency_score - result2.adjacency_score) > 0.001:
            return result1.adjacency_score > result2.adjacency_score

        return result1.avg_q > result2.avg_q

    def _generate_swap_candidates(self,
                                   layout: Dict[str, Tuple[int, int, int]]) -> List[Optional[Dict]]:
        """
        Generate candidate layouts by swapping pairs of nodes

        Uses domain knowledge to prioritize useful swaps:
        - Trigger nodes with each other (to optimize cluster)
        - Trigger nodes with flexible nodes (to move triggers strategically)
        - Angel with outer nodes (to optimize Angel distance)
        """
        candidates = []
        node_names = list(layout.keys())

        # Prioritized swap strategies
        strategies = [
            # Strategy 1: Move Angel into trigger cluster (adjacent to Panic)
            lambda: self._get_angel_to_cluster_swaps(layout, node_names),

            # Strategy 2: Swap trigger nodes with flexible nodes (move triggers around)
            lambda: self._get_trigger_flexible_swaps(layout, node_names),

            # Strategy 3: Swap trigger nodes with each other (optimize cluster configuration)
            lambda: self._get_trigger_trigger_swaps(layout, node_names),

            # Strategy 4: Random swaps (exploration)
            lambda: self._get_random_swaps(layout, node_names, count=10),
        ]

        for strategy in strategies:
            candidates.extend(strategy())

        return candidates

    def _get_trigger_flexible_swaps(self, layout: Dict, node_names: List[str]) -> List[Dict]:
        """Get swaps between trigger nodes and flexible nodes"""
        swaps = []
        trigger_nodes_in_layout = [n for n in self.trigger_nodes if n in node_names]
        flexible_nodes = [n for n in node_names if n not in self.trigger_nodes
                          and n not in self.high_value_nodes and n != 'Angel']

        for trigger in trigger_nodes_in_layout:
            for flexible in flexible_nodes:
                swapped = swap_nodes(layout, trigger, flexible)
                if is_valid_layout(swapped):
                    swaps.append(swapped)

        return swaps

    def _get_trigger_trigger_swaps(self, layout: Dict, node_names: List[str]) -> List[Dict]:
        """Get swaps between pairs of trigger nodes"""
        swaps = []
        trigger_nodes_in_layout = [n for n in self.trigger_nodes if n in node_names]

        for i, trigger1 in enumerate(trigger_nodes_in_layout):
            for trigger2 in trigger_nodes_in_layout[i+1:]:
                swapped = swap_nodes(layout, trigger1, trigger2)
                if is_valid_layout(swapped):
                    swaps.append(swapped)

        return swaps

    def _get_angel_to_cluster_swaps(self, layout: Dict, node_names: List[str]) -> List[Dict]:
        """Get swaps to move Angel adjacent to Panic/trigger cluster"""
        swaps = []
        if 'Angel' not in layout:
            return swaps

        # Get positions adjacent to Panic
        panic_neighbors = set(get_neighbors(self.panic_position))

        # Get nodes currently adjacent to Panic
        nodes_near_panic = []
        for node_name in node_names:
            if layout[node_name] in panic_neighbors:
                nodes_near_panic.append(node_name)

        # Try swapping Angel with nodes near Panic
        for node_name in nodes_near_panic:
            if node_name != 'Angel':
                swapped = swap_nodes(layout, 'Angel', node_name)
                if is_valid_layout(swapped):
                    swaps.append(swapped)

        # Also try swapping Angel with nodes in rings 2-4 (near Panic)
        for node_name in node_names:
            if node_name == 'Angel':
                continue

            node_pos = layout[node_name]
            node_ring = max(abs(node_pos[0]), abs(node_pos[1]), abs(node_pos[2]))

            # Swap Angel with nodes in rings 2-4 (closer to Panic)
            if 2 <= node_ring <= 4:
                swapped = swap_nodes(layout, 'Angel', node_name)
                if is_valid_layout(swapped):
                    swaps.append(swapped)

        return swaps

    def _get_random_swaps(self, layout: Dict, node_names: List[str], count: int) -> List[Dict]:
        """Get random swaps for exploration"""
        swaps = []
        pairs_tried = set()

        for _ in range(count * 3):  # Try more to get 'count' valid swaps
            if len(swaps) >= count:
                break

            # Pick random pair
            node1, node2 = random.sample(node_names, 2)
            pair = tuple(sorted([node1, node2]))

            if pair in pairs_tried:
                continue
            pairs_tried.add(pair)

            swapped = swap_nodes(layout, node1, node2)
            if is_valid_layout(swapped):
                swaps.append(swapped)

        return swaps

    def _generate_rotation_candidates(self,
                                       layout: Dict[str, Tuple[int, int, int]]) -> List[Optional[Dict]]:
        """
        Generate candidate layouts by rotating trigger clusters around Panic

        This preserves trigger adjacency while exploring different configurations
        """
        candidates = []

        # Get trigger nodes adjacent to Panic (including Angel if present)
        panic_neighbors_set = set(get_neighbors(self.panic_position))
        adjacent_triggers = [
            node for node in self.trigger_nodes
            if node in layout and layout[node] in panic_neighbors_set
        ]

        # Add Angel if it's adjacent to Panic
        if 'Angel' in layout and layout['Angel'] in panic_neighbors_set:
            adjacent_triggers.append('Angel')

        # If we have at least 2 adjacent triggers, try rotating them
        if len(adjacent_triggers) >= 2:
            # Rotate cluster clockwise
            rotated_cw = rotate_cluster(layout, 'Panic', adjacent_triggers, clockwise=True)
            if rotated_cw and is_valid_layout(rotated_cw):
                candidates.append(rotated_cw)

            # Rotate cluster counter-clockwise
            rotated_ccw = rotate_cluster(layout, 'Panic', adjacent_triggers, clockwise=False)
            if rotated_ccw and is_valid_layout(rotated_ccw):
                candidates.append(rotated_ccw)

        # Also try rotating all trigger nodes + Angel (not just adjacent ones)
        all_triggers_in_layout = [n for n in self.trigger_nodes if n in layout]
        if 'Angel' in layout:
            all_triggers_in_layout.append('Angel')

        if len(all_triggers_in_layout) >= 2:
            # Rotate all triggers + Angel around Panic
            rotated_all_cw = rotate_cluster(layout, 'Panic', all_triggers_in_layout, clockwise=True)
            if rotated_all_cw and is_valid_layout(rotated_all_cw):
                candidates.append(rotated_all_cw)

            rotated_all_ccw = rotate_cluster(layout, 'Panic', all_triggers_in_layout, clockwise=False)
            if rotated_all_ccw and is_valid_layout(rotated_all_ccw):
                candidates.append(rotated_all_ccw)

        return candidates


def select_diverse_candidates(all_candidates: List[Dict],
                               evaluation_results: List,
                               count: int = 10) -> List[Tuple[Dict, any]]:
    """
    Select diverse candidates for refinement

    Selection strategy:
    - Top candidates by min_q (worst-case)
    - Top candidates by avg_q (average-case)
    - Top candidates by adjacency_score (trigger clustering)
    - Top candidates by avg_efficiency (trigger/attempt ratio)

    Args:
        all_candidates: List of candidate layouts
        evaluation_results: List of EvaluationResult objects (same order as candidates)
        count: Number of diverse candidates to select

    Returns:
        List of (layout, result) tuples
    """
    # Combine candidates with results
    candidates_with_results = list(zip(all_candidates, evaluation_results))

    selected = []
    selected_indices = set()

    # Helper to add unique candidates
    def add_candidates(sorted_candidates, num_to_add):
        added = 0
        for idx, (candidate, result) in sorted_candidates:
            if idx not in selected_indices and added < num_to_add:
                selected.append((candidate, result))
                selected_indices.add(idx)
                added += 1
            if len(selected) >= count:
                break

    # Track original indices
    indexed_candidates = [(i, c, r) for i, (c, r) in enumerate(candidates_with_results)]

    # Category 1: Best min_q (worst-case optimization)
    by_min_q = sorted(indexed_candidates, key=lambda x: x[2].min_q, reverse=True)
    add_candidates([(i, (c, r)) for i, c, r in by_min_q], count // 4)

    # Category 2: Best avg_q (average-case optimization)
    by_avg_q = sorted(indexed_candidates, key=lambda x: x[2].avg_q, reverse=True)
    add_candidates([(i, (c, r)) for i, c, r in by_avg_q], count // 4)

    # Category 3: Best adjacency_score (trigger clustering)
    by_adjacency = sorted(indexed_candidates, key=lambda x: x[2].adjacency_score, reverse=True)
    add_candidates([(i, (c, r)) for i, c, r in by_adjacency], count // 4)

    # Category 4: Best avg_efficiency (trigger efficiency)
    by_efficiency = sorted(indexed_candidates, key=lambda x: x[2].avg_efficiency, reverse=True)
    add_candidates([(i, (c, r)) for i, c, r in by_efficiency], count // 4)

    # Fill remaining slots with top min_q candidates
    if len(selected) < count:
        add_candidates([(i, (c, r)) for i, c, r in by_min_q], count - len(selected))

    return selected[:count]
