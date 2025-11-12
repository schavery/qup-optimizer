# data/ranks.py
"""
Rank progression data for Qup

Based on observed values from rank_notes.txt with interpolation for missing data.

Rank structure:
- Bronze: ranks 1-5
- Silver: ranks 6-10
- Gold: ranks 11-15
- Platinum: ranks 16-20
- Diamond: ranks 21-25
- Master: ranks 26-30
- Grandmaster: ranks 31-35
- Legend: ranks 36-40
"""

from dataclasses import dataclass
from typing import Dict

@dataclass
class RankRewards:
    """Rewards and penalties for a given rank"""
    rank: int
    tier_name: str
    tier_level: int
    qup_per_flip: int  # Q gained per winning flip
    qdown_per_flip: int  # Q lost per losing flip (negative value)
    xp_win: int  # XP per winning flip
    xp_loss: int  # XP per losing flip
    gold_win: int  # Gold per winning flip


# Observed data points from rank_notes.txt
OBSERVED_RANKS = {
    5: RankRewards(5, "Bronze", 5, 100, -200, 220, 99, 132),
    6: RankRewards(6, "Silver", 1, 100, -500, 300, 135, 180),  # Interpolated qdown
    7: RankRewards(7, "Silver", 2, 100, -650, 375, 158, 225),  # Interpolated
    9: RankRewards(9, "Silver", 4, 100, -950, 450, 203, 270),
    11: RankRewards(11, "Gold", 1, 100, -2750, 750, 338, 450),
    12: RankRewards(12, "Gold", 2, 100, -3500, 875, 394, 525),
    13: RankRewards(13, "Gold", 3, 100, -4500, 1000, 450, 600),
    14: RankRewards(14, "Gold", 4, 100, -6000, 1150, 518, 690),
    15: RankRewards(15, "Gold", 5, 100, -7500, 1325, 596, 795),
    16: RankRewards(16, "Platinum", 1, 100, -15000, 1500, 675, 900),
    17: RankRewards(17, "Platinum", 2, 100, -22500, 1700, 765, 1020),
    18: RankRewards(18, "Platinum", 3, 100, -32500, 1900, 855, 1140),
    19: RankRewards(19, "Platinum", 4, 100, -42500, 2100, 945, 1260),
}


def interpolate_rank_data() -> Dict[int, RankRewards]:
    """Generate full rank data with interpolation for missing values"""
    ranks = {}

    # Bronze (ranks 1-5): Linear progression
    # Qdown: -100 to -200 (steps of 25)
    # XP win: 100 to 220 (steps of 30)
    # XP loss: 45 to 99 (steps of ~13.5)
    # Gold win: 60 to 132 (steps of 18)
    for i in range(1, 6):
        ranks[i] = RankRewards(
            rank=i,
            tier_name="Bronze",
            tier_level=i,
            qup_per_flip=100,
            qdown_per_flip=-100 - (i - 1) * 25,
            xp_win=100 + (i - 1) * 30,
            xp_loss=45 + int((i - 1) * 13.5),
            gold_win=60 + (i - 1) * 18
        )

    # Silver (ranks 6-10): Moderate progression
    # Qdown: -500 to -1200 (increasing steps)
    # XP win: 300 to 600
    # Gold win: 180 to 360
    silver_qdowns = [-500, -650, -800, -950, -1200]
    for i in range(5):
        rank = 6 + i
        ranks[rank] = RankRewards(
            rank=rank,
            tier_name="Silver",
            tier_level=i + 1,
            qup_per_flip=100,
            qdown_per_flip=silver_qdowns[i],
            xp_win=300 + i * 75,
            xp_loss=135 + i * 23,
            gold_win=180 + i * 45
        )

    # Gold (ranks 11-15): Steep progression
    gold_qdowns = [-2750, -3500, -4500, -6000, -7500]
    gold_xp_wins = [750, 875, 1000, 1150, 1325]
    gold_xp_losses = [338, 394, 450, 518, 596]
    gold_golds = [450, 525, 600, 690, 795]
    for i in range(5):
        rank = 11 + i
        ranks[rank] = RankRewards(
            rank=rank,
            tier_name="Gold",
            tier_level=i + 1,
            qup_per_flip=100,
            qdown_per_flip=gold_qdowns[i],
            xp_win=gold_xp_wins[i],
            xp_loss=gold_xp_losses[i],
            gold_win=gold_golds[i]
        )

    # Platinum (ranks 16-20): Very steep progression
    plat_qdowns = [-15000, -22500, -32500, -42500, -57500]
    plat_xp_wins = [1500, 1700, 1900, 2100, 2350]
    plat_xp_losses = [675, 765, 855, 945, 1057]
    plat_golds = [900, 1020, 1140, 1260, 1410]
    for i in range(5):
        rank = 16 + i
        ranks[rank] = RankRewards(
            rank=rank,
            tier_name="Platinum",
            tier_level=i + 1,
            qup_per_flip=100,
            qdown_per_flip=plat_qdowns[i],
            xp_win=plat_xp_wins[i],
            xp_loss=plat_xp_losses[i],
            gold_win=plat_golds[i]
        )

    # Diamond (ranks 21-25): Exponential growth begins
    for i in range(5):
        rank = 21 + i
        ranks[rank] = RankRewards(
            rank=rank,
            tier_name="Diamond",
            tier_level=i + 1,
            qup_per_flip=100,
            qdown_per_flip=int(-75000 * (1.3 ** i)),
            xp_win=2600 + i * 300,
            xp_loss=1170 + i * 130,
            gold_win=1560 + i * 180
        )

    # Master (ranks 26-30): High exponential
    for i in range(5):
        rank = 26 + i
        ranks[rank] = RankRewards(
            rank=rank,
            tier_name="Master",
            tier_level=i + 1,
            qup_per_flip=100,
            qdown_per_flip=int(-200000 * (1.35 ** i)),
            xp_win=4100 + i * 400,
            xp_loss=1845 + i * 180,
            gold_win=2460 + i * 240
        )

    # Grandmaster (ranks 31-35): Extreme exponential
    for i in range(5):
        rank = 31 + i
        ranks[rank] = RankRewards(
            rank=rank,
            tier_name="Grandmaster",
            tier_level=i + 1,
            qup_per_flip=100,
            qdown_per_flip=int(-700000 * (1.4 ** i)),
            xp_win=6000 + i * 500,
            xp_loss=2700 + i * 225,
            gold_win=3600 + i * 300
        )

    # Legend (ranks 36-40): Maximum difficulty
    for i in range(5):
        rank = 36 + i
        ranks[rank] = RankRewards(
            rank=rank,
            tier_name="Legend",
            tier_level=i + 1,
            qup_per_flip=100,
            qdown_per_flip=int(-2000000 * (1.5 ** i)),
            xp_win=8500 + i * 600,
            xp_loss=3825 + i * 270,
            gold_win=5100 + i * 360
        )

    return ranks


# Generate the full rank table
RANK_DATA: Dict[int, RankRewards] = interpolate_rank_data()


def get_rank_rewards(rank: int) -> RankRewards:
    """Get rewards for a specific rank"""
    if rank < 1:
        rank = 1
    if rank > 40:
        # Beyond rank 40, use exponential scaling
        base = RANK_DATA[40]
        multiplier = 1.5 ** (rank - 40)
        return RankRewards(
            rank=rank,
            tier_name="Legend",
            tier_level=5 + (rank - 40),
            qup_per_flip=100,
            qdown_per_flip=int(base.qdown_per_flip * multiplier),
            xp_win=int(base.xp_win * multiplier),
            xp_loss=int(base.xp_loss * multiplier),
            gold_win=int(base.gold_win * multiplier)
        )
    return RANK_DATA[rank]


def get_rank_name(rank: int) -> str:
    """Get display name for a rank"""
    rewards = get_rank_rewards(rank)
    return f"{rewards.tier_name} {rewards.tier_level}"


def get_qdown_for_rank(rank: int) -> int:
    """Get Qdown penalty for a rank (returns positive value)"""
    return -get_rank_rewards(rank).qdown_per_flip
