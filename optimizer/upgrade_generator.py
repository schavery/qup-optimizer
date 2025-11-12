# optimizer/upgrade_generator.py
"""
Generate valid upgrade configurations within a point budget

Key insight: With 18 points and 7 nodes, we need smart enumeration.
Strategy: Use constraint-based generation with tier priorities.
"""

from typing import Dict, List, Tuple
from itertools import product
from data.nodes import NODES


class UpgradeConfigGenerator:
    """Generate upgrade configurations within budget constraints"""

    def __init__(self):
        # Extract upgrade info from static nodes
        self.node_info = {}

        for name, node_def in NODES.items():
            if not node_def.upgrade_paths:
                continue

            paths = []
            for path in node_def.upgrade_paths:
                paths.append(len(path))  # Max levels in this path

            self.node_info[name] = {
                'max_paths': paths,
                'total_possible': sum(paths),
                'base_avs': node_def.base_avs
            }

    def generate_all_configs(self, budget: int,
                           min_panic_avs: int = 4,
                           skip_noops: bool = True) -> List[Dict[str, List[int]]]:
        """
        Generate all valid upgrade configurations within budget

        Args:
            budget: Total upgrade points available
            min_panic_avs: Minimum AVS for Panic (4 = 3 upgrades minimum)
            skip_noops: Skip Battle Medic Path 2 Level 1 (it's a noop)

        Returns:
            List of upgrade configs, each is Dict[node_name -> [path1_level, path2_level]]
        """
        configs = []

        # Generate configs using recursive enumeration
        partial_config = {}
        self._enumerate_configs(
            nodes=list(self.node_info.keys()),
            budget_remaining=budget,
            partial_config=partial_config,
            configs=configs,
            min_panic_avs=min_panic_avs,
            skip_noops=skip_noops
        )

        return configs

    def _enumerate_configs(self, nodes: List[str], budget_remaining: int,
                          partial_config: Dict[str, List[int]],
                          configs: List[Dict[str, List[int]]],
                          min_panic_avs: int, skip_noops: bool):
        """Recursively enumerate valid configurations"""

        # Base case: no more nodes to configure
        if not nodes:
            # Check if we should save this config
            if budget_remaining >= 0:  # Valid config
                configs.append(dict(partial_config))
            return

        # Take next node
        node = nodes[0]
        remaining_nodes = nodes[1:]
        info = self.node_info[node]

        # Special constraint: Panic must have minimum AVS
        if node == "Panic":
            min_path1 = max(0, min_panic_avs - 1)  # -1 because base is 1
            max_path1 = min(info['max_paths'][0], budget_remaining)
            path1_range = range(min_path1, max_path1 + 1)
            path2_range = [0]  # Panic only has 1 path
        else:
            # General case: try all combinations within budget
            max_path1 = min(info['max_paths'][0], budget_remaining)
            path1_range = range(0, max_path1 + 1)

            if len(info['max_paths']) > 1:
                max_path2 = min(info['max_paths'][1], budget_remaining)
                path2_range = range(0, max_path2 + 1)
            else:
                path2_range = [0]

        # Try all combinations for this node
        for path1_level in path1_range:
            for path2_level in path2_range:
                cost = path1_level + path2_level

                # Skip if over budget
                if cost > budget_remaining:
                    continue

                # Skip Battle Medic Path 2 Level 1 (it's a noop)
                if skip_noops and node == "Battle Medic":
                    if path1_level == 0 and path2_level == 1:
                        continue

                # Add this config and recurse
                partial_config[node] = [path1_level, path2_level]
                self._enumerate_configs(
                    remaining_nodes,
                    budget_remaining - cost,
                    partial_config,
                    configs,
                    min_panic_avs,
                    skip_noops
                )

        # Clean up (backtrack)
        if node in partial_config:
            del partial_config[node]

    def generate_tiered_configs(self, budget: int, num_samples: int = 100) -> List[Dict[str, List[int]]]:
        """
        Generate high-quality configs using tier-based heuristics

        Strategy:
        1. Always max Panic (6 points)
        2. Heavily invest in EMT (3-6 points)
        3. Moderate investment in Stop the Bleeding (2-4 points)
        4. Light investment in others (0-3 points)

        Returns fewer, higher-quality configs for faster evaluation
        """
        configs = []

        # Tier 1: Panic configurations (high priority)
        panic_configs = [
            [6, 0],  # Max Panic
            [5, 0],  # Near-max
            [4, 0],  # Minimum viable
        ]

        # Tier 2: EMT configurations
        emt_configs = [
            [3, 3],  # Balanced (max both paths)
            [3, 2],  # Favor AVS
            [2, 3],  # Favor BB scaling
            [3, 1],  # AVS + some scaling
            [1, 3],  # Minimal AVS, max scaling
        ]

        # Tier 3: Stop the Bleeding
        stb_configs = [
            [2, 1],  # Good balance
            [0, 3],  # Max AVS
            [3, 0],  # Max effect
            [1, 2],  # Moderate
        ]

        # Tier 4: Others (lower priority)
        other_configs = [
            [2, 0],  # Self Diagnosis flat Q
            [0, 2],  # Self Diagnosis AVS
            [1, 1],  # Balanced
            [0, 0],  # Skip
        ]

        # Combine strategically
        import random
        random.seed(42)

        for panic_cfg in panic_configs:
            panic_cost = sum(panic_cfg)
            remaining = budget - panic_cost

            # Sample EMT configs that fit budget
            for emt_cfg in emt_configs:
                emt_cost = sum(emt_cfg)
                if emt_cost > remaining:
                    continue

                remaining_2 = remaining - emt_cost

                # Sample Stop the Bleeding
                for stb_cfg in stb_configs:
                    stb_cost = sum(stb_cfg)
                    if stb_cost > remaining_2:
                        continue

                    remaining_3 = remaining_2 - stb_cost

                    # Distribute remaining points among others
                    # Simple heuristic: split between Self Diagnosis and Battle Medic
                    for self_diag_cfg in other_configs:
                        sd_cost = sum(self_diag_cfg)
                        if sd_cost > remaining_3:
                            continue

                        remaining_4 = remaining_3 - sd_cost

                        # Battle Medic gets what's left (up to max)
                        bm_max = min(remaining_4, 5)  # Max 5 points (skip noop)
                        for bm_total in range(0, bm_max + 1):
                            # Allocate between paths
                            for bm_p1 in range(0, min(bm_total, 3) + 1):
                                bm_p2 = bm_total - bm_p1
                                if bm_p2 > 3:
                                    continue
                                # Skip noop
                                if bm_p1 == 0 and bm_p2 == 1:
                                    continue

                                remaining_5 = remaining_4 - bm_total

                                # Triage gets remainder
                                triage_max = min(remaining_5, 6)
                                for t_total in range(0, triage_max + 1):
                                    for t_p1 in range(0, min(t_total, 2) + 1):
                                        t_p2 = t_total - t_p1
                                        if t_p2 > 4:
                                            continue

                                        # Big Sister gets remainder (usually 0)
                                        bs_remaining = remaining_5 - t_total
                                        if bs_remaining > 5:
                                            bs_remaining = 0  # Skip Big Sister if too many points

                                        # Create config
                                        config = {
                                            'Panic': panic_cfg,
                                            'EMT': emt_cfg,
                                            'Stop the Bleeding': stb_cfg,
                                            'Self Diagnosis': self_diag_cfg,
                                            'Battle Medic': [bm_p1, bm_p2],
                                            'Triage': [t_p1, t_p2],
                                            'Big Sister': [0, 0],  # Usually skip
                                        }

                                        total_cost = sum(sum(v) for v in config.values())
                                        if total_cost == budget:
                                            configs.append(config)

                                        if len(configs) >= num_samples:
                                            return configs

        return configs

    def config_summary(self, config: Dict[str, List[int]]) -> str:
        """Generate human-readable summary of an upgrade config"""
        lines = []
        total_points = 0

        for node_name, levels in sorted(config.items()):
            points = sum(levels)
            total_points += points

            if points == 0:
                continue

            info = self.node_info.get(node_name, {})
            base_avs = info.get('base_avs', 0)

            # Calculate total AVS
            total_avs = base_avs
            # Simplified AVS calculation (would need full node data for exact)
            # For now, approximate

            lines.append(f"  {node_name:20} {levels} ({points} pts)")

        lines.append(f"  {'Total':20} {total_points} points")
        return '\n'.join(lines)
