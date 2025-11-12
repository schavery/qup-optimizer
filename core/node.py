# core/node.py
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum

class TriggerType(Enum):
    WIN = "win"
    LOSS = "loss"
    FLIP = "flip"
    MANUAL = "manual"

@dataclass
class NodeDefinition:
    """Data-only node configuration"""
    name: str
    position: Tuple[int, int, int]  # (q, r, s)
    trigger_types: List[str]
    base_avs: Optional[int]
    is_static: bool
    effect_type: str
    effect_params: Dict[str, Any]
    upgrade_paths: List[List[Dict[str, Any]]]
    node_order: int

@dataclass
class NodeInstance:
    """Runtime instance of a node"""
    definition: NodeDefinition
    upgrade_levels: List[int] = field(default_factory=list)  # Level for each path
    times_triggered_this_flip: int = 0
    depleted_triggered: bool = False  # For nodes with depleted effects

    def __post_init__(self):
        if not self.upgrade_levels:
            self.upgrade_levels = [0] * len(self.definition.upgrade_paths)

    def get_total_avs(self) -> Optional[int]:
        """Calculate total AVS including upgrades"""
        if self.definition.base_avs is None:
            return None

        total = self.definition.base_avs
        for path_idx, level in enumerate(self.upgrade_levels):
            path = self.definition.upgrade_paths[path_idx]
            for step_idx in range(level):
                if 'avs_increase' in path[step_idx]:
                    total += path[step_idx]['avs_increase']
        return total

    def can_trigger(self) -> bool:
        """Check if node has activation stock remaining"""
        avs = self.get_total_avs()
        return avs is None or self.times_triggered_this_flip < avs

    def reset_flip_counter(self):
        """Called at start of each flip"""
        self.times_triggered_this_flip = 0
        self.depleted_triggered = False
