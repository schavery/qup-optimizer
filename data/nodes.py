# data/nodes.py
from core.node import NodeDefinition

NODES = {
    "Battle Medic": NodeDefinition(
        name="Battle Medic",
        position=(1, -1, 0),
        trigger_types=["win"],
        base_avs=2,
        is_static=True,
        effect_type="add_to_qmult",
        effect_params={
            "multiplier_source": "battle_bonus"
        },
        upgrade_paths=[
            [
                {"avs_increase": 1},
                {"avs_increase": 1},
                {"avs_increase": 2}
            ],
            [
                {"noop": True},
                {"effect_mult": 2},
                {"effect_mult": 3}
            ]
        ],
        node_order=2
    ),

    "EMT": NodeDefinition(
        name="EMT",
        position=(-1, 1, 0),
        trigger_types=["loss"],
        base_avs=2,
        is_static=True,
        effect_type="reduce_qdown",
        effect_params={
            "base_reduction": 350,
            "bb_multiplier": 50
        },
        upgrade_paths=[
            [
                {"avs_increase": 1},
                {"avs_increase": 2},
                {"avs_increase": 3}
            ],
            [
                {"bb_multiplier_increase": 100},
                {"bb_multiplier_increase": 200},
                {"depleted_reduction_percent": 0.03}
            ]
        ],
        node_order=5
    ),

    "Self Diagnosis": NodeDefinition(
        name="Self Diagnosis",
        position=(3, -2, -1),
        trigger_types=["win"],
        base_avs=3,
        is_static=True,
        effect_type="flat_q",
        effect_params={
            "base_amount": 4500
        },
        upgrade_paths=[
            [
                {"q_increase": 7000},
                {"q_increase": 12000}
            ],
            [
                {"avs_increase": 1},
                {"avs_increase": 1},
                {"avs_increase": 2},
                {"avs_increase": 2}
            ]
        ],
        node_order=23
    ),

    "Stop the Bleeding": NodeDefinition(
        name="Stop the Bleeding",
        position=(0, -3, 3),
        trigger_types=["loss"],
        base_avs=2,
        is_static=True,
        effect_type="reduce_qdown_per_loss",
        effect_params={
            "base_per_loss": 6000
        },
        upgrade_paths=[
            [
                {"per_loss_increase": 8500},
                {"per_loss_increase": 11500},
                {"per_loss_increase": 15000}
            ],
            [
                {"avs_increase": 1},
                {"avs_increase": 2},
                {"avs_increase": 3}
            ]
        ],
        node_order=19
    ),

    "Panic": NodeDefinition(
        name="Panic",
        position=(-3, 2, 1),
        trigger_types=["loss"],
        base_avs=1,
        is_static=True,
        effect_type="trigger_adjacent",
        effect_params={},
        upgrade_paths=[
            [
                {"avs_increase": 1},
                {"avs_increase": 1},
                {"avs_increase": 1},
                {"avs_increase": 1},
                {"avs_increase": 1},
                {"avs_increase": 1}
            ]
        ],
        node_order=32
    ),

    "Triage": NodeDefinition(
        name="Triage",
        position=(4, -1, -3),
        trigger_types=["loss"],
        base_avs=2,
        is_static=True,
        effect_type="reduce_qdown_percent",
        effect_params={
            "base_percent": 0.03  # 3%
        },
        upgrade_paths=[
            [
                {"percent_increase": 0.04},  # 4%
                {"percent_increase": 0.05}   # 5%
            ],
            [
                {"avs_increase": 1},
                {"avs_increase": 1},
                {"avs_increase": 1},
                {"avs_increase": 1}
            ]
        ],
        node_order=44
    ),

    "Big Sister": NodeDefinition(
        name="Big Sister",
        position=(-4, 1, 3),
        trigger_types=["win"],
        base_avs=3,
        is_static=True,
        effect_type="flat_q_per_teammate_class",
        effect_params={
            "base_per_teammate": 300,
            "teammate_class": "Gambler"
        },
        upgrade_paths=[
            [
                {"per_teammate_increase": 500},
                {"per_teammate_increase": 800}
            ],
            [
                {"avs_increase": 1},
                {"avs_increase": 1},
                {"avs_increase": 2}
            ]
        ],
        node_order=56
    ),

    "Precision Cut": NodeDefinition(
        name="Precision Cut",
        position=(3, -4, 1),
        trigger_types=["loss"],
        base_avs=1,
        is_static=True,
        effect_type="teammate_qdown_reduction_per_depleted",
        effect_params={
            "base_per_depleted": 500,
        },
        upgrade_paths=[
            [
                {"per_depleted_increase": 750},
                {"per_depleted_increase": 1000},
                {"per_depleted_increase": 1250}
            ],
            [
                {"avs_increase": 1},
                {"avs_increase": 1},
                {"avs_increase": 2}
            ]
        ],
        node_order=40,
    ),
}

MOVABLE_NODES = {
    "Angel": NodeDefinition(
        name="Angel",
        position=(0, 0, 0),  # Placeholder, will be set by layout
        trigger_types=["loss"],
        base_avs=3,
        is_static=False,
        effect_type="q_per_qdown_prevented",
        effect_params={},
        upgrade_paths=[],
        node_order=-1  # Movable nodes don't have fixed order
    ),

    "Exhilaration": NodeDefinition(
        name="Exhilaration",
        position=(0, 0, 0),
        trigger_types=["flip"],
        base_avs=3,
        is_static=False,
        effect_type="flat_q_per_bb",
        effect_params={"q_per_bb": 100},
        upgrade_paths=[],
        node_order=-1
    ),

    "Surgeon": NodeDefinition(
        name="Surgeon",
        position=(0, 0, 0),
        trigger_types=["flip"],
        base_avs=3,
        is_static=False,
        effect_type="trigger_most_avs",
        effect_params={"num_triggers": 2},
        upgrade_paths=[],
        node_order=-1
    ),

    "Adrenaline": NodeDefinition(
        name="Adrenaline",
        position=(0, 0, 0),
        trigger_types=["loss"],
        base_avs=3,
        is_static=False,
        effect_type="add_bb_and_trigger",
        effect_params={
            "bb_threshold_1": 5,
            "bb_threshold_2": 10
        },
        upgrade_paths=[],
        node_order=-1
    ),

    "Focus": NodeDefinition(
        name="Focus",
        position=(0, 0, 0),
        trigger_types=["loss"],
        base_avs=3,
        is_static=False,
        effect_type="trigger_random_adjacent",
        effect_params={},
        upgrade_paths=[],
        node_order=-1
    ),

    "Stimulant": NodeDefinition(
        name="Stimulant",
        position=(0, 0, 0),
        trigger_types=["flip"],
        base_avs=4,
        is_static=False,
        effect_type="trigger_adjacent_most_avs",
        effect_params={"num_triggers": 2},
        upgrade_paths=[],
        node_order=-1
    ),
    "Heroine": NodeDefinition(
        name="Heroine",
        position=(0, 0, 0),
        trigger_types=["manual"],  # Only triggers when forced
        base_avs=3,
        is_static=False,
        effect_type="add_to_qmult",
        effect_params={
            "multiplier_source": "battle_bonus"
        },
        upgrade_paths=[],
        node_order=-1
    ),

    "Funeral Rites": NodeDefinition(
        name="Funeral Rites",
        position=(0, 0, 0),
        trigger_types=["flip"],
        base_avs=3,
        is_static=False,
        effect_type="xp_per_depleted",
        effect_params={
            "xp_per_depleted": 500
        },
        upgrade_paths=[],
        node_order=-1
    ),

    "Extra Dose": NodeDefinition(
        name="Extra Dose",
        position=(0, 0, 0),
        trigger_types=["loss"],
        base_avs=2,
        is_static=False,
        effect_type="trigger_adjacent_most_avs",
        effect_params={
            "num_triggers": 3
        },
        upgrade_paths=[],
        node_order=-1
    ),

    "Angel of Death": NodeDefinition(
        name="Angel of Death",
        position=(0, 0, 0),
        trigger_types=["loss"],
        base_avs=1,
        is_static=False,
        effect_type="multiply_qmult",
        effect_params={
            "multiplier": 3
        },
        upgrade_paths=[],
        node_order=-1
    ),

    "Low Point": NodeDefinition(
        name="Low Point",
        position=(0, 0, 0),
        trigger_types=["loss"],
        base_avs=5,
        is_static=False,
        effect_type="trigger_adjacent_per_loss",
        effect_params={
            "nodes_per_loss": 2
        },
        upgrade_paths=[],
        node_order=-1
    ),

    "Deployment": NodeDefinition(
        name="Deployment",
        position=(0, 0, 0),
        trigger_types=["manual"],
        base_avs=7,
        is_static=False,
        effect_type="add_bb",
        effect_params={
            "bb_increase": 1
        },
        upgrade_paths=[],
        node_order=-1
    ),

    "Insurance Scam": NodeDefinition(
        name="Insurance Scam",
        position=(0, 0, 0),
        trigger_types=["manual"],
        base_avs=2,
        is_static=False,
        effect_type="gold_per_qdown_prevented",
        effect_params={
            "qdown_per_gold": 33
        },
        upgrade_paths=[],
        node_order=-1
    ),

    "Battle Hardened": NodeDefinition(
        name="Battle Hardened",
        position=(0, 0, 0),
        trigger_types=["loss"],
        base_avs=3,
        is_static=False,
        effect_type="defence_per_bb",
        effect_params={
            "defence_per_bb": 2
        },
        upgrade_paths=[],
        node_order=-1
    ),
}

# Combine all nodes
ALL_NODES = {**NODES, **MOVABLE_NODES}
