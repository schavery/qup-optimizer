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
    total_triggers: int = 0  # Track total triggers across all flips

    def apply_qmult(self):
        """Apply Qmult to q_this_flip and add to total currency"""
        final_q = int(self.q_this_flip * self.qmult)
        self.q_currency += final_q
        self.q_this_flip = 0
        self.qmult = 1.0

    def get_qdown_for_rank(self) -> int:
        """Calculate Q loss based on rank - real Grandmaster values"""
        # Grandmaster 1 (rank 31) = 700,000 Qdown
        # This is a steep exponential curve at high ranks
        if self.rank <= 30:
            # Lower ranks use linear scaling
            return 600 * self.rank
        else:
            # Grandmaster ranks (31+) have exponential Qdown penalties
            # GM1 (31) = 700,000
            # GM2 (32) = ~1,000,000 (estimated)
            # GM3 (33) = ~1,500,000 (estimated)
            gm_level = self.rank - 30
            base_gm = 700000
            return int(base_gm * (1.4 ** (gm_level - 1)))
