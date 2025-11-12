# api/routes.py
"""Flask API routes for Qup optimizer"""
from flask import Blueprint, request, jsonify
from typing import Dict, Any, List

from data.nodes import NODES, MOVABLE_NODES, ALL_NODES
from core.layout import GridLayout
from optimizer.evaluator import LayoutEvaluator
from optimizer.adjacency_generator import AdjacencyAwareGenerator
from optimizer.upgrade_generator import UpgradeConfigGenerator
from api.serializers import (
    serialize_node_definition,
    serialize_evaluation_result,
    deserialize_layout,
    deserialize_upgrade_config
)

api = Blueprint('api', __name__)


@api.route('/nodes', methods=['GET'])
def get_nodes():
    """Get all node definitions"""
    return jsonify({
        "static": {name: serialize_node_definition(node) for name, node in NODES.items()},
        "movable": {name: serialize_node_definition(node) for name, node in MOVABLE_NODES.items()}
    })


@api.route('/evaluate', methods=['POST'])
def evaluate_layout():
    """Evaluate a single layout configuration

    Request body:
    {
        "layout": {"Angel": [5, -2, -3], "Focus": [3, 1, -4], ...},
        "upgrades": {"Panic": [6, 0], "EMT": [3, 3], ...},
        "rank": 31
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        if not data or 'layout' not in data:
            return jsonify({"error": "Missing 'layout' in request body"}), 400

        layout = deserialize_layout(data['layout'])
        upgrades = deserialize_upgrade_config(data.get('upgrades', {}))
        rank = data.get('rank', 31)

        # Validate rank
        if not (1 <= rank <= 40):
            return jsonify({"error": "Rank must be between 1 and 40"}), 400

        # Create evaluator and evaluate
        evaluator = LayoutEvaluator(
            rank=rank,
            upgrade_configs=upgrades
        )

        result = evaluator.evaluate_layout(layout)

        return jsonify(serialize_evaluation_result(result))

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route('/generate-layouts', methods=['POST'])
def generate_layouts():
    """Generate candidate layouts

    Request body:
    {
        "count": 20,
        "rank": 31,
        "seed": 42,
        "upgrades": {"Panic": [6, 0], ...}
    }
    """
    try:
        data = request.get_json() or {}

        count = data.get('count', 10)
        rank = data.get('rank', 31)
        seed = data.get('seed', None)
        upgrades = deserialize_upgrade_config(data.get('upgrades', {}))

        # Validate inputs
        if count > 1000:
            return jsonify({"error": "Count cannot exceed 1000"}), 400

        if not (1 <= rank <= 40):
            return jsonify({"error": "Rank must be between 1 and 40"}), 400

        # Generate candidates
        generator = AdjacencyAwareGenerator(
            static_nodes=NODES,
            movable_nodes=MOVABLE_NODES,
            seed=seed
        )

        candidates = generator.generate_candidates(num_candidates=count)

        # Evaluate all candidates
        evaluator = LayoutEvaluator(
            rank=rank,
            upgrade_configs=upgrades
        )

        results = []
        for candidate in candidates:
            result = evaluator.evaluate_layout(candidate)
            results.append(serialize_evaluation_result(result))

        # Sort by min_q (descending - higher is better)
        results.sort(key=lambda r: r['min_q'], reverse=True)

        return jsonify({"layouts": results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route('/generate-upgrades', methods=['POST'])
def generate_upgrades():
    """Generate upgrade configurations

    Request body:
    {
        "budget": 18,
        "strategy": "tiered"  # or "exhaustive"
    }
    """
    try:
        data = request.get_json() or {}

        budget = data.get('budget', 18)
        strategy = data.get('strategy', 'tiered')

        # Validate inputs
        if budget < 0 or budget > 100:
            return jsonify({"error": "Budget must be between 0 and 100"}), 400

        if strategy not in ['tiered', 'exhaustive']:
            return jsonify({"error": "Strategy must be 'tiered' or 'exhaustive'"}), 400

        # Generate configs
        generator = UpgradeConfigGenerator(NODES)

        if strategy == 'tiered':
            configs = generator.generate_tiered_configs(budget)
        else:
            configs = generator.generate_all_valid_configs(budget)

        # Convert to JSON-serializable format
        configs_json = [
            {name: levels for name, levels in config.items()}
            for config in configs
        ]

        return jsonify({"configs": configs_json, "count": len(configs_json)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route('/outcomes', methods=['GET'])
def get_outcomes():
    """Get all possible round outcome sequences"""
    from itertools import product

    # Generate all 20 possible outcomes (best of 5)
    outcomes = []
    for combo in product([True, False], repeat=5):
        wins = sum(combo)
        losses = 5 - wins

        # Only include valid match outcomes (first to 3)
        if wins == 3 or losses == 3:
            sequence = ''.join('W' if w else 'L' for w in combo)
            outcomes.append({
                "sequence": sequence,
                "wins": wins,
                "losses": losses
            })

    return jsonify({"outcomes": outcomes})


@api.route('/ranks', methods=['GET'])
def get_ranks():
    """Get all rank information"""
    from data.ranks import RANK_DATA, get_rank_name

    ranks_list = []
    for rank_num in range(1, 41):
        rewards = RANK_DATA[rank_num]
        ranks_list.append({
            "rank": rank_num,
            "name": get_rank_name(rank_num),
            "tier": rewards.tier_name,
            "tier_level": rewards.tier_level,
            "qup_per_flip": rewards.qup_per_flip,
            "qdown_per_flip": rewards.qdown_per_flip,
            "xp_win": rewards.xp_win,
            "xp_loss": rewards.xp_loss,
            "gold_win": rewards.gold_win
        })

    return jsonify({"ranks": ranks_list})


@api.route('/rank/<int:rank_num>', methods=['GET'])
def get_rank(rank_num):
    """Get specific rank information"""
    from data.ranks import get_rank_rewards, get_rank_name

    rewards = get_rank_rewards(rank_num)
    return jsonify({
        "rank": rank_num,
        "name": get_rank_name(rank_num),
        "tier": rewards.tier_name,
        "tier_level": rewards.tier_level,
        "qup_per_flip": rewards.qup_per_flip,
        "qdown_per_flip": rewards.qdown_per_flip,
        "xp_win": rewards.xp_win,
        "xp_loss": rewards.xp_loss,
        "gold_win": rewards.gold_win
    })


@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "qup-optimizer"})
