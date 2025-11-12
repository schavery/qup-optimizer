# core/hex_grid.py
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class HexPosition:
    q: int
    r: int
    s: int

    def __post_init__(self):
        assert self.q + self.r + self.s == 0, "Invalid hex coordinates"

    def __hash__(self):
        return hash((self.q, self.r, self.s))

    def __eq__(self, other):
        return (self.q, self.r, self.s) == (other.q, other.r, other.s)

    def neighbors(self) -> List['HexPosition']:
        """Returns 6 adjacent hex positions (clockwise from top)"""
        directions = [
            (0, -1, 1),   # top
            (1, -1, 0),   # top-right
            (1, 0, -1),   # bottom-right
            (0, 1, -1),   # bottom
            (-1, 1, 0),   # bottom-left
            (-1, 0, 1),   # top-left
        ]
        return [HexPosition(self.q + dq, self.r + dr, self.s + ds)
                for dq, dr, ds in directions]

    def to_tuple(self) -> Tuple[int, int, int]:
        return (self.q, self.r, self.s)

def generate_spiral_order(radius: int) -> List[HexPosition]:
    """Generate positions in spiral order from center outward"""
    positions = [HexPosition(0, 0, 0)]  # Start at center

    for ring in range(1, radius + 1):
        # Start at top of ring
        pos = HexPosition(0, -ring, ring)

        # Traverse the 6 sides of the hexagon
        directions = [
            (1, 0, -1),   # SE
            (0, 1, -1),   # S
            (-1, 1, 0),   # SW
            (-1, 0, 1),   # NW
            (0, -1, 1),   # N
            (1, -1, 0),   # NE
        ]

        for direction in directions:
            for _ in range(ring):
                positions.append(pos)
                pos = HexPosition(
                    pos.q + direction[0],
                    pos.r + direction[1],
                    pos.s + direction[2]
                )

    return positions
