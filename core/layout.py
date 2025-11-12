# core/layout.py
from typing import Dict, List, Tuple
from dataclasses import dataclass

from core.hex_grid import generate_spiral_order
from core.node import NodeDefinition, NodeInstance
from effects.executor import EffectExecutor


@dataclass
class GridLayout:
    """Represents a specific configuration of nodes on the grid"""
    static_nodes: Dict[str, NodeDefinition]
    movable_positions: Dict[str, Tuple[int, int, int]]
    upgrade_configs: Dict[str, List[int]]

    def get_total_upgrade_points_spent(self) -> int:
        """Calculate total upgrade points spent"""
        total = 0
        for node_name, levels in self.upgrade_configs.items():
            total += sum(levels)  # Each upgrade level costs 1 point
        return total

    def is_within_budget(self, max_upgrade_points: int) -> bool:
        """Check if layout is within upgrade point budget"""
        return self.get_total_upgrade_points_spent() <= max_upgrade_points

    def get_all_positions(self) -> Dict[Tuple[int, int, int], str]:
        """Get all occupied positions and the node names at those positions"""
        positions = {}

        for name, definition in self.static_nodes.items():
            positions[definition.position] = name

        for name, pos in self.movable_positions.items():
            if pos in positions:
                raise ValueError(f"Position conflict at {pos}: {positions[pos]} and {name}")
            positions[pos] = name

        return positions

    def validate(self, max_upgrade_points: int = None) -> bool:
        """Check if layout is valid"""
        try:
            self.get_all_positions()
            if max_upgrade_points is not None:
                return self.is_within_budget(max_upgrade_points)
            return True
        except ValueError:
            return False

# Update simulator.py to accept a layout
class Simulator:
    def __init__(self, all_node_definitions: Dict[str, NodeDefinition],
                 layout: GridLayout = None,
                 upgrade_configs: Dict[str, List[int]] = None):
        """
        Initialize simulator with node definitions and layout

        Args:
            all_node_definitions: All available node definitions (static + movable)
            layout: GridLayout specifying where movable nodes are placed
            upgrade_configs: Dict of node name -> list of upgrade levels per path (deprecated, use layout)
        """
        self.executor = EffectExecutor()
        self.all_node_definitions = all_node_definitions

        # If no layout provided, use all static nodes with default positions
        if layout is None:
            layout = GridLayout(
                static_nodes={name: defn for name, defn in all_node_definitions.items() if defn.is_static},
                movable_positions={},
                upgrade_configs=upgrade_configs or {}
            )

        self.layout = layout

        # Create node instances based on layout
        self.nodes: Dict[Tuple[int, int, int], NodeInstance] = {}

        # Add static nodes
        for name, definition in layout.static_nodes.items():
            upgrade_levels = layout.upgrade_configs.get(name, [0] * len(definition.upgrade_paths))
            instance = NodeInstance(definition=definition, upgrade_levels=upgrade_levels)
            self.nodes[definition.position] = instance

        # Add movable nodes at their configured positions
        for name, position in layout.movable_positions.items():
            if name in all_node_definitions:
                definition = all_node_definitions[name]
                # Create a copy with the new position
                positioned_definition = NodeDefinition(
                    name=definition.name,
                    position=position,
                    trigger_types=definition.trigger_types,
                    base_avs=definition.base_avs,
                    is_static=False,  # Keep it marked as movable
                    effect_type=definition.effect_type,
                    effect_params=definition.effect_params,
                    upgrade_paths=definition.upgrade_paths,
                    node_order=definition.node_order
                )
                upgrade_levels = layout.upgrade_configs.get(name, [0] * len(definition.upgrade_paths))
                instance = NodeInstance(definition=positioned_definition, upgrade_levels=upgrade_levels)
                self.nodes[position] = instance

        # Generate spiral order for evaluation
        self.spiral_positions = generate_spiral_order(radius=8)
