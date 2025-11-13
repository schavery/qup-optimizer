#!/usr/bin/env python3
"""Test that upgrade logic uses replacement, not addition"""

from data.nodes import ALL_NODES, NODES
from simulator import Simulator
from core.game_state import GameState
from core.layout import GridLayout

def test_emt_upgrades():
    """EMT bb_multiplier should be REPLACEMENT: 50 → 100 → 200"""
    print("=== Testing EMT bb_multiplier upgrades ===")

    for level in [0, 1, 2]:
        layout = GridLayout(
            static_nodes={'EMT': NODES['EMT']},
            movable_positions={},
            upgrade_configs={'EMT': [0, level]}
        )

        sim = Simulator(ALL_NODES, layout)

        # Manually calculate what EMT should give
        emt_node = list(sim.nodes.values())[0]
        params = emt_node.definition.effect_params
        bb_mult = params['bb_multiplier']

        for path_idx, lvl in enumerate(emt_node.upgrade_levels):
            path = emt_node.definition.upgrade_paths[path_idx]
            for step_idx in range(lvl):
                if 'bb_multiplier_increase' in path[step_idx]:
                    bb_mult = path[step_idx]['bb_multiplier_increase']

        expected_mult = [50, 100, 200][level]
        print(f"  Level {level}: bb_multiplier = {bb_mult} (expected {expected_mult}) {'✓' if bb_mult == expected_mult else '✗ WRONG'}")

def test_self_diagnosis_upgrades():
    """Self Diagnosis q_increase should be REPLACEMENT: 4500 → 7000 → 12000"""
    print("\n=== Testing Self Diagnosis q_increase upgrades ===")

    for level in [0, 1, 2]:
        layout = GridLayout(
            static_nodes={'Self Diagnosis': NODES['Self Diagnosis']},
            movable_positions={},
            upgrade_configs={'Self Diagnosis': [level, 0]}
        )

        sim = Simulator(ALL_NODES, layout)
        sd_node = list(sim.nodes.values())[0]

        params = sd_node.definition.effect_params
        q_amount = params['base_amount']

        for path_idx, lvl in enumerate(sd_node.upgrade_levels):
            path = sd_node.definition.upgrade_paths[path_idx]
            for step_idx in range(lvl):
                if 'q_increase' in path[step_idx]:
                    q_amount = path[step_idx]['q_increase']

        expected_amount = [4500, 7000, 12000][level]
        print(f"  Level {level}: q_amount = {q_amount} (expected {expected_amount}) {'✓' if q_amount == expected_amount else '✗ WRONG'}")

def test_stop_bleeding_upgrades():
    """Stop the Bleeding should be REPLACEMENT: 6000 → 8500 → 11500 → 15000"""
    print("\n=== Testing Stop the Bleeding per_loss upgrades ===")

    for level in [0, 1, 2, 3]:
        layout = GridLayout(
            static_nodes={'Stop the Bleeding': NODES['Stop the Bleeding']},
            movable_positions={},
            upgrade_configs={'Stop the Bleeding': [level, 0]}
        )

        sim = Simulator(ALL_NODES, layout)
        stb_node = list(sim.nodes.values())[0]

        params = stb_node.definition.effect_params
        per_loss = params['base_per_loss']

        for path_idx, lvl in enumerate(stb_node.upgrade_levels):
            path = stb_node.definition.upgrade_paths[path_idx]
            for step_idx in range(lvl):
                if 'per_loss_increase' in path[step_idx]:
                    per_loss = path[step_idx]['per_loss_increase']

        expected_amount = [6000, 8500, 11500, 15000][level]
        print(f"  Level {level}: per_loss = {per_loss} (expected {expected_amount}) {'✓' if per_loss == expected_amount else '✗ WRONG'}")

def test_triage_upgrades():
    """Triage should be REPLACEMENT: 0.03 → 0.04 → 0.05"""
    print("\n=== Testing Triage percent upgrades (REPLACEMENT) ===")

    for level in [0, 1, 2]:
        layout = GridLayout(
            static_nodes={'Triage': NODES['Triage']},
            movable_positions={},
            upgrade_configs={'Triage': [level, 0]}
        )

        sim = Simulator(ALL_NODES, layout)
        triage_node = list(sim.nodes.values())[0]

        params = triage_node.definition.effect_params
        percent = params['base_percent']

        # Now using REPLACEMENT like all other nodes
        for path_idx, lvl in enumerate(triage_node.upgrade_levels):
            path = triage_node.definition.upgrade_paths[path_idx]
            for step_idx in range(lvl):
                if 'percent_increase' in path[step_idx]:
                    percent = path[step_idx]['percent_increase']

        expected_percent = [0.03, 0.04, 0.05][level]
        print(f"  Level {level}: percent = {percent} (expected {expected_percent}) {'✓' if abs(percent - expected_percent) < 0.001 else '✗ WRONG'}")

if __name__ == "__main__":
    test_emt_upgrades()
    test_self_diagnosis_upgrades()
    test_stop_bleeding_upgrades()
    test_triage_upgrades()
