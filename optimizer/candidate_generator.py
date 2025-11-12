# optimizer/candidate_generator.py
from typing import Dict, List, Tuple, Set
import random
from core.hex_grid import HexPosition, generate_spiral_order
from core.node import NodeDefinition
from data.nodes import NODES, MOVABLE_NODES


class CandidateGenerator:
    """Generate candidate positions for movable nodes using ring-based strategy"""

    def __init__(self, max_radius: int = 8, seed: int = None):
        self.max_radius = max_radius
        if seed is not None:
            random.seed(seed)

        # Get all positions in spiral order
        self.all_positions = generate_spiral_order(radius=max_radius)

        # Group positions by ring (distance from center)
        self.positions_by_ring: Dict[int, List[Tuple[int, int, int]]] = {}
        for pos in self.all_positions:
            ring = max(abs(pos.q), abs(pos.r), abs(pos.s))
            if ring not in self.positions_by_ring:
                self.positions_by_ring[ring] = []
            self.positions_by_ring[ring].append(pos.to_tuple())

        # Identify static and movable nodes
        self.static_nodes = {}
        self.movable_nodes = MOVABLE_NODES

        for name, node_def in NODES.items():
            self.static_nodes[node_def.position] = name

        # Get occupied positions (only static nodes occupy positions initially)
        self.occupied_positions = set(self.static_nodes.keys())

        # Calculate available positions per ring
        self.available_by_ring: Dict[int, List[Tuple[int, int, int]]] = {}
        for ring, positions in self.positions_by_ring.items():
            available = [pos for pos in positions if pos not in self.occupied_positions]
            if available:
                self.available_by_ring[ring] = available

    def generate_candidates(self, num_candidates: int = 100) -> List[Dict[str, Tuple[int, int, int]]]:
        """
        Generate candidate layouts using ring-based constraints

        Strategy:
        - Angel in outermost rings (5-8) to trigger last
        - High-value trigger nodes in mid rings (2-4)
        - Fill remaining nodes across inner/mid rings

        Returns:
            List of dicts mapping movable node name -> position tuple
        """
        candidates = []

        for _ in range(num_candidates):
            layout = self._generate_single_candidate()
            if layout:  # Only add valid layouts
                candidates.append(layout)

        return candidates

    def _generate_single_candidate(self) -> Dict[str, Tuple[int, int, int]]:
        """Generate a single candidate layout"""
        layout = {}
        used_positions = set(self.occupied_positions)

        # Define node placement strategy
        placement_strategy = {
            # Angel must be in outer rings to trigger last
            'Angel': {'rings': [5, 6, 7, 8], 'priority': 1},

            # Trigger nodes in mid-outer rings
            'Panic': {'rings': [3, 4, 5], 'priority': 2},
            'Low Point': {'rings': [3, 4, 5], 'priority': 2},
            'Focus': {'rings': [2, 3, 4], 'priority': 2},
            'Stimulant': {'rings': [2, 3, 4], 'priority': 2},
            'Extra Dose': {'rings': [2, 3, 4], 'priority': 2},

            # High-value effect nodes
            'Surgeon': {'rings': [3, 4, 5], 'priority': 3},
            'Angel of Death': {'rings': [2, 3, 4, 5], 'priority': 3},
            'Adrenaline': {'rings': [2, 3, 4], 'priority': 3},

            # Utility nodes - more flexible
            'Funeral Rites': {'rings': [1, 2, 3, 4, 5], 'priority': 4},
            'Exhilaration': {'rings': [1, 2, 3, 4, 5], 'priority': 4},
            'Battle Hardened': {'rings': [1, 2, 3, 4, 5], 'priority': 4},

            # Manual trigger nodes - least important positioning
            'Heroine': {'rings': [1, 2, 3, 4, 5, 6], 'priority': 5},
            'Deployment': {'rings': [1, 2, 3, 4, 5, 6], 'priority': 5},
            'Insurance Scam': {'rings': [1, 2, 3, 4, 5, 6], 'priority': 5},
        }

        # Sort nodes by priority
        sorted_nodes = sorted(
            self.movable_nodes.keys(),
            key=lambda name: placement_strategy.get(name, {'priority': 99})['priority']
        )

        # Place each node
        for node_name in sorted_nodes:
            strategy = placement_strategy.get(node_name, {'rings': list(range(1, 9))})
            allowed_rings = strategy['rings']

            # Get available positions in allowed rings
            available_positions = []
            for ring in allowed_rings:
                if ring in self.available_by_ring:
                    ring_positions = [pos for pos in self.available_by_ring[ring]
                                    if pos not in used_positions]
                    available_positions.extend(ring_positions)

            if not available_positions:
                # Fallback: try any available position
                available_positions = [pos for ring_positions in self.available_by_ring.values()
                                     for pos in ring_positions if pos not in used_positions]

            if not available_positions:
                return None  # Failed to place all nodes

            # Randomly select from available positions
            chosen_pos = random.choice(available_positions)
            layout[node_name] = chosen_pos
            used_positions.add(chosen_pos)

        return layout

    def get_ring_for_position(self, position: Tuple[int, int, int]) -> int:
        """Get the ring number for a position"""
        return max(abs(position[0]), abs(position[1]), abs(position[2]))
