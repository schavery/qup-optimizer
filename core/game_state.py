# core/game_state.py
from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class GameState:
    q_currency: int = 0
    q_this_flip: int = 0
    qmult: float = 1.0
    battle_bonus: int = 0
    rank: int = 1
    team: str = "Q"

    flip_history: List[bool] = field(default_factory=list)

    def apply_qmult(self):
        """Apply Qmult to q_this_flip and add to total currency"""
        final_q = int(self.q_this_flip * self.qmult)
        self.q_currency += final_q
        self.q_this_flip = 0
        self.qmult = 1.0

    def get_qdown_for_rank(self) -> int:
        """Calculate Q loss based on rank - placeholder"""
        return 600 * self.rank
