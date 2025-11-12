# optimizer/layout_ops.py
"""Utilities for manipulating grid layouts during optimization"""
from typing import Dict, List, Tuple, Set
from copy import deepcopy
from core.hex_grid import HexPosition
from data.nodes import NODES


def swap_nodes(layout: Dict[str, Tuple[int, int, int]],
               node1: str,
               node2: str) -> Dict[str, Tuple[int, int, int]]:
    """
    Swap the positions of two movable nodes

    Args:
        layout: Dict mapping node name -> position tuple
        node1: First node name
        node2: Second node name

    Returns:
        New layout with swapped positions
    """
    new_layout = layout.copy()
    pos1 = layout[node1]
    pos2 = layout[node2]
    new_layout[node1] = pos2
    new_layout[node2] = pos1
    return new_layout


def move_node(layout: Dict[str, Tuple[int, int, int]],
              node_name: str,
              new_position: Tuple[int, int, int]) -> Dict[str, Tuple[int, int, int]]:
    """
    Move a single node to a new position

    Args:
        layout: Dict mapping node name -> position tuple
        node_name: Node to move
        new_position: New position tuple

    Returns:
        New layout with moved node
    """
    new_layout = layout.copy()
    new_layout[node_name] = new_position
    return new_layout


def get_neighbors(position: Tuple[int, int, int]) -> List[Tuple[int, int, int]]:
    """
    Get the 6 adjacent hex positions (clockwise from top)

    Args:
        position: Center position tuple (q, r, s)

    Returns:
        List of 6 adjacent position tuples
    """
    q, r, s = position
    directions = [
        (0, -1, 1),   # top
        (1, -1, 0),   # top-right
        (1, 0, -1),   # bottom-right
        (0, 1, -1),   # bottom
        (-1, 1, 0),   # bottom-left
        (-1, 0, 1),   # top-left
    ]
    return [(q + dq, r + dr, s + ds) for dq, dr, ds in directions]


def get_cluster_nodes(layout: Dict[str, Tuple[int, int, int]],
                      center_position: Tuple[int, int, int],
                      radius: int = 1) -> List[str]:
    """
    Find all nodes within radius hexes of a center position

    Args:
        layout: Dict mapping node name -> position tuple
        center_position: Center position to search from
        radius: Maximum distance in hexes (default 1 = immediate neighbors)

    Returns:
        List of node names within radius
    """
    cluster = []

    for node_name, node_pos in layout.items():
        # Calculate hex distance
        distance = hex_distance(center_position, node_pos)
        if distance <= radius:
            cluster.append(node_name)

    return cluster


def hex_distance(pos1: Tuple[int, int, int], pos2: Tuple[int, int, int]) -> int:
    """
    Calculate hex distance between two positions

    Args:
        pos1: First position tuple (q, r, s)
        pos2: Second position tuple (q, r, s)

    Returns:
        Distance in hexes
    """
    return (abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1]) + abs(pos1[2] - pos2[2])) // 2


def rotate_position_around_center(position: Tuple[int, int, int],
                                   center: Tuple[int, int, int],
                                   steps: int = 1) -> Tuple[int, int, int]:
    """
    Rotate a position around a center by N 60-degree steps (clockwise)

    Args:
        position: Position to rotate
        center: Center of rotation
        steps: Number of 60-degree clockwise rotations (1-5, or negative for CCW)

    Returns:
        New rotated position
    """
    # Translate to origin
    q = position[0] - center[0]
    r = position[1] - center[1]
    s = position[2] - center[2]

    # Rotate using cube coordinate rotation
    # Each step is 60 degrees clockwise
    for _ in range(steps % 6):
        q, r, s = -s, -q, -r

    # Translate back
    return (q + center[0], r + center[1], s + center[2])


def rotate_cluster(layout: Dict[str, Tuple[int, int, int]],
                   center_node: str,
                   nodes_to_rotate: List[str],
                   clockwise: bool = True) -> Dict[str, Tuple[int, int, int]]:
    """
    Rotate a cluster of nodes around a center node by 60 degrees

    Args:
        layout: Dict mapping node name -> position tuple
        center_node: Node to use as rotation center (can be in layout or static)
        nodes_to_rotate: List of node names to rotate
        clockwise: True for clockwise, False for counter-clockwise

    Returns:
        New layout with rotated nodes, or None if rotation creates conflicts
    """
    # Get center position (could be movable or static)
    if center_node in layout:
        center_pos = layout[center_node]
    else:
        # Check if it's a static node
        static_node = NODES.get(center_node)
        if static_node:
            center_pos = static_node.position
        else:
            raise ValueError(f"Center node {center_node} not found in layout or static nodes")

    # Create new layout
    new_layout = layout.copy()

    # Rotate each node
    steps = 1 if clockwise else -1
    rotated_positions = []

    for node_name in nodes_to_rotate:
        if node_name not in layout:
            continue  # Skip if node not in layout

        old_pos = layout[node_name]
        new_pos = rotate_position_around_center(old_pos, center_pos, steps)
        rotated_positions.append((node_name, new_pos))

    # Check for conflicts with static nodes and other movable nodes
    occupied_static = {node.position for node in NODES.values()}
    occupied_other = {pos for name, pos in layout.items() if name not in nodes_to_rotate}

    for node_name, new_pos in rotated_positions:
        if new_pos in occupied_static or new_pos in occupied_other:
            # Conflict detected, rotation not possible
            return None

    # Apply rotations
    for node_name, new_pos in rotated_positions:
        new_layout[node_name] = new_pos

    return new_layout


def is_valid_layout(layout: Dict[str, Tuple[int, int, int]],
                    max_radius: int = 8) -> bool:
    """
    Check if a layout is valid (no conflicts, within bounds)

    Args:
        layout: Dict mapping node name -> position tuple
        max_radius: Maximum distance from center

    Returns:
        True if layout is valid
    """
    # Check for position conflicts within movable nodes
    positions = list(layout.values())
    if len(positions) != len(set(positions)):
        return False  # Duplicate positions

    # Check for conflicts with static nodes
    static_positions = {node.position for node in NODES.values()}
    for pos in positions:
        if pos in static_positions:
            return False  # Conflicts with static node

    # Check if positions are within radius
    for pos in positions:
        distance = max(abs(pos[0]), abs(pos[1]), abs(pos[2]))
        if distance > max_radius:
            return False  # Out of bounds

    return True


def get_all_occupied_positions(layout: Dict[str, Tuple[int, int, int]]) -> Set[Tuple[int, int, int]]:
    """
    Get all occupied positions (static + movable)

    Args:
        layout: Dict mapping node name -> position tuple

    Returns:
        Set of all occupied position tuples
    """
    occupied = {node.position for node in NODES.values()}  # Static nodes
    occupied.update(layout.values())  # Movable nodes
    return occupied


def layout_to_key(layout: Dict[str, Tuple[int, int, int]]) -> tuple:
    """
    Convert layout to a hashable key for caching

    Args:
        layout: Dict mapping node name -> position tuple

    Returns:
        Tuple suitable for use as dict key
    """
    return tuple(sorted(layout.items()))
