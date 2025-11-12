# api/serializers.py
"""JSON serializers for dataclasses and core objects"""
from typing import Any, Dict, List, Tuple
from core.node import NodeDefinition, NodeInstance
from core.layout import GridLayout
from optimizer.evaluator import EvaluationResult


def serialize_node_definition(node: NodeDefinition) -> Dict[str, Any]:
    """Convert NodeDefinition to JSON-serializable dict"""
    return {
        "name": node.name,
        "position": list(node.position),  # Tuple to list
        "trigger_types": node.trigger_types,
        "base_avs": node.base_avs,
        "is_static": node.is_static,
        "effect_type": node.effect_type,
        "effect_params": node.effect_params,
        "upgrade_paths": node.upgrade_paths,
        "node_order": node.node_order
    }


def serialize_grid_layout(layout: GridLayout) -> Dict[str, Any]:
    """Convert GridLayout to JSON-serializable dict"""
    return {
        "static_nodes": {
            name: serialize_node_definition(node)
            for name, node in layout.static_nodes.items()
        },
        "movable_positions": {
            name: list(pos)
            for name, pos in layout.movable_positions.items()
        },
        "upgrade_configs": layout.upgrade_configs
    }


def serialize_evaluation_result(result: EvaluationResult) -> Dict[str, Any]:
    """Convert EvaluationResult to JSON-serializable dict"""
    return {
        "layout": {name: list(pos) for name, pos in result.layout.items()},
        "outcomes": result.outcomes,
        "min_q": result.min_q,
        "max_q": result.max_q,
        "avg_q": result.avg_q,
        "positive_outcomes": result.positive_outcomes,
        "total_outcomes": result.total_outcomes,
        "trigger_counts": result.trigger_counts,
        "adjacency_score": result.adjacency_score,
        "max_triggers_per_flip": result.max_triggers_per_flip,
        "avg_efficiency": result.avg_efficiency
    }


def deserialize_layout(data: Dict[str, Any]) -> Dict[str, Tuple[int, int, int]]:
    """Convert JSON layout to internal format"""
    return {
        name: tuple(pos) if isinstance(pos, list) else pos
        for name, pos in data.items()
    }


def deserialize_upgrade_config(data: Dict[str, Any]) -> Dict[str, List[int]]:
    """Convert JSON upgrade config to internal format"""
    return {
        name: levels if isinstance(levels, list) else [levels]
        for name, levels in data.items()
    }
