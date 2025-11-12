# optimizer/adjacency_generator.py
from typing import Dict, List, Tuple, Set
import random
from core.hex_grid import HexPosition
from optimizer.candidate_generator import CandidateGenerator


class AdjacencyAwareGenerator(CandidateGenerator):
    """
    Enhanced generator that creates trigger clusters for feedback loops

    Strategy:
    1. Build cluster around Panic (static at -2,-1,3)
    2. Place trigger nodes (Low Point, Focus, Stimulant, Adrenaline, Extra Dose) adjacent to Panic
    3. These nodes can trigger each other and Panic, creating cascades
    4. Place Angel in outer ring to trigger last
    """

    def __init__(self, max_radius: int = 8, seed: int = None):
        super().__init__(max_radius, seed)

        # Identify Panic's position from static nodes
        self.panic_position = (-2, -1, 3)  # From NODES data
        self.panic_hex = HexPosition(*self.panic_position)

        # Get Panic's adjacent positions
        self.panic_adjacent = [pos.to_tuple() for pos in self.panic_hex.neighbors()]

        # Filter out occupied positions
        self.panic_adjacent_available = [
            pos for pos in self.panic_adjacent
            if pos not in self.occupied_positions
        ]

        # Define trigger nodes that should be in Panic cluster
        self.trigger_cluster_nodes = [
            'Low Point',      # Triggers 2 adjacent per loss
            'Adrenaline',     # Triggers 1-2 adjacent based on BB
            'Focus',          # Triggers 1 random adjacent
            'Stimulant',      # Triggers adjacent with most AVS
            'Extra Dose',     # Triggers adjacent with most AVS
            'Angel',          # NEW: Place Angel in trigger cluster for multiple triggers!
        ]

        # Nodes that benefit from being near trigger cluster but not critical
        self.secondary_cluster_nodes = [
            'Surgeon',        # Triggers highest AVS globally (doesn't need adjacency)
            'Exhilaration',   # Flat Q per BB (no adjacency needed)
        ]

        # Nodes that should be far from Panic (previously Angel was here)
        self.outer_nodes = []

        # Nodes that don't need specific positioning
        self.flexible_nodes = [
            'Heroine',
            'Deployment',
            'Insurance Scam',
            'Funeral Rites',
            'Battle Hardened',
            'Angel of Death',
        ]

    def _generate_single_candidate(self) -> Dict[str, Tuple[int, int, int]]:
        """Generate a candidate with trigger clustering around Panic"""
        layout = {}
        used_positions = set(self.occupied_positions)

        # Step 1: Place trigger cluster nodes adjacent to Panic
        panic_cluster_positions = list(self.panic_adjacent_available)
        random.shuffle(panic_cluster_positions)

        cluster_nodes_to_place = [n for n in self.trigger_cluster_nodes if n in self.movable_nodes]

        for i, node_name in enumerate(cluster_nodes_to_place):
            if i < len(panic_cluster_positions):
                # Place directly adjacent to Panic
                pos = panic_cluster_positions[i]
                layout[node_name] = pos
                used_positions.add(pos)
            else:
                # If we run out of adjacent slots, place in ring 3-4 near Panic
                candidates = []
                for ring in [3, 4]:
                    if ring in self.available_by_ring:
                        ring_pos = [p for p in self.available_by_ring[ring] if p not in used_positions]
                        candidates.extend(ring_pos)

                if candidates:
                    pos = random.choice(candidates)
                    layout[node_name] = pos
                    used_positions.add(pos)

        # Step 2: Place secondary cluster nodes near Panic (ring 2-4)
        secondary_to_place = [n for n in self.secondary_cluster_nodes if n in self.movable_nodes and n not in layout]

        for node_name in secondary_to_place:
            candidates = []
            for ring in [2, 3, 4]:
                if ring in self.available_by_ring:
                    ring_pos = [p for p in self.available_by_ring[ring] if p not in used_positions]
                    candidates.extend(ring_pos)

            if candidates:
                pos = random.choice(candidates)
                layout[node_name] = pos
                used_positions.add(pos)

        # Step 3: Place Angel in outer rings (5-8) to trigger last
        for node_name in self.outer_nodes:
            if node_name in self.movable_nodes and node_name not in layout:
                candidates = []
                for ring in [5, 6, 7, 8]:
                    if ring in self.available_by_ring:
                        ring_pos = [p for p in self.available_by_ring[ring] if p not in used_positions]
                        candidates.extend(ring_pos)

                if candidates:
                    pos = random.choice(candidates)
                    layout[node_name] = pos
                    used_positions.add(pos)

        # Step 4: Place flexible nodes anywhere available
        flexible_to_place = [n for n in self.flexible_nodes if n in self.movable_nodes and n not in layout]

        for node_name in flexible_to_place:
            # Get all available positions
            all_available = [pos for ring_positions in self.available_by_ring.values()
                           for pos in ring_positions if pos not in used_positions]

            if all_available:
                pos = random.choice(all_available)
                layout[node_name] = pos
                used_positions.add(pos)

        # Verify all movable nodes are placed
        if len(layout) != len(self.movable_nodes):
            return None

        return layout

    def calculate_adjacency_score(self, layout: Dict[str, Tuple[int, int, int]]) -> float:
        """
        Score layout based on adjacency relationships

        Higher score = better trigger cascade potential
        """
        score = 0.0

        # Get positions of trigger nodes
        trigger_positions = {}
        for node_name in self.trigger_cluster_nodes:
            if node_name in layout:
                trigger_positions[node_name] = layout[node_name]

        # Score: trigger nodes adjacent to Panic (worth 10 points each)
        panic_neighbors = set(self.panic_adjacent)
        for node_name, pos in trigger_positions.items():
            if pos in panic_neighbors:
                score += 10.0

        # Score: trigger nodes adjacent to each other (worth 5 points per pair)
        trigger_nodes_list = list(trigger_positions.items())
        for i, (name1, pos1) in enumerate(trigger_nodes_list):
            hex1 = HexPosition(*pos1)
            neighbors1 = set(n.to_tuple() for n in hex1.neighbors())

            for name2, pos2 in trigger_nodes_list[i+1:]:
                if pos2 in neighbors1:
                    score += 5.0

        # Score: Angel far from Panic (worth up to 5 points based on distance)
        if 'Angel' in layout:
            angel_pos = layout['Angel']
            angel_ring = max(abs(angel_pos[0]), abs(angel_pos[1]), abs(angel_pos[2]))
            panic_ring = max(abs(self.panic_position[0]), abs(self.panic_position[1]), abs(self.panic_position[2]))
            distance = angel_ring - panic_ring
            score += min(distance, 5.0)  # Max 5 points

        # Score: Surgeon near trigger cluster (can target high-AVS nodes)
        if 'Surgeon' in layout:
            surgeon_pos = layout['Surgeon']
            surgeon_hex = HexPosition(*surgeon_pos)
            surgeon_neighbors = set(n.to_tuple() for n in surgeon_hex.neighbors())

            # Count adjacent trigger nodes
            adjacent_triggers = sum(1 for pos in trigger_positions.values() if pos in surgeon_neighbors)
            score += adjacent_triggers * 2.0

        return score
