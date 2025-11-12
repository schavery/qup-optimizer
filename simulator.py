# simulator.py
import random
from typing import Dict, List, Tuple, Optional
from core.game_state import GameState
from core.node import NodeInstance, NodeDefinition
from core.hex_grid import HexPosition, generate_spiral_order
from core.layout import GridLayout
from effects.executor import EffectExecutor

class Simulator:
    def __init__(self, all_node_definitions: Dict[str, NodeDefinition],
                 layout: GridLayout = None,
                 upgrade_configs: Dict[str, List[int]] = None,
                 random_seed: int = None):
        """
        Initialize simulator with node definitions and layout

        Args:
            all_node_definitions: All available node definitions (static + movable)
            layout: GridLayout specifying where movable nodes are placed
            upgrade_configs: Dict of node name -> list of upgrade levels per path (deprecated, use layout)
            random_seed: Seed for random number generation (for reproducibility)
        """
        self.executor = EffectExecutor()
        self.all_node_definitions = all_node_definitions

        if random_seed is not None:
            random.seed(random_seed)

        # If no layout provided, use all static nodes with default positions
        if layout is None:
            layout = GridLayout(
                static_nodes={name: defn for name, defn in all_node_definitions.items() if defn.is_static},
                movable_positions={},
                upgrade_configs=upgrade_configs or {}
            )

        self.layout = layout

        # Create node instances based on layout
        self.nodes: Dict[Tuple[int, int, int], NodeInstance] = {}
        self.node_by_name: Dict[str, NodeInstance] = {}

        # Add static nodes
        for name, definition in layout.static_nodes.items():
            upgrade_levels = layout.upgrade_configs.get(name, [0] * len(definition.upgrade_paths))
            instance = NodeInstance(definition=definition, upgrade_levels=upgrade_levels)
            self.nodes[definition.position] = instance
            self.node_by_name[name] = instance

        # Add movable nodes at their configured positions
        for name, position in layout.movable_positions.items():
            if name in all_node_definitions:
                definition = all_node_definitions[name]
                # Create a copy with the new position
                positioned_definition = NodeDefinition(
                    name=definition.name,
                    position=position,
                    trigger_types=definition.trigger_types,
                    base_avs=definition.base_avs,
                    is_static=False,
                    effect_type=definition.effect_type,
                    effect_params=definition.effect_params,
                    upgrade_paths=definition.upgrade_paths,
                    node_order=definition.node_order
                )
                upgrade_levels = layout.upgrade_configs.get(name, [0] * len(definition.upgrade_paths))
                instance = NodeInstance(definition=positioned_definition, upgrade_levels=upgrade_levels)
                self.nodes[position] = instance
                self.node_by_name[name] = instance

        # Generate spiral order for evaluation
        self.spiral_positions = generate_spiral_order(radius=8)

    def reset_nodes(self):
        """Reset all node counters for a new flip"""
        for node in self.nodes.values():
            node.reset_flip_counter()

    def get_nodes_to_trigger(self, game_state: GameState, trigger_type: str) -> List[NodeInstance]:
        """Get nodes that should trigger based on flip outcome, in spiral order"""
        triggered_nodes = []

        for pos in self.spiral_positions:
            pos_tuple = pos.to_tuple()
            if pos_tuple in self.nodes:
                node = self.nodes[pos_tuple]
                if trigger_type in node.definition.trigger_types:
                    triggered_nodes.append(node)

        return triggered_nodes

    def get_node_with_most_avs(self, exclude_node: NodeInstance = None) -> Optional[NodeInstance]:
        """Find the node with most remaining AVS"""
        best_node = None
        best_remaining = -1

        for node in self.nodes.values():
            if node == exclude_node:
                continue

            total_avs = node.get_total_avs()
            if total_avs is None:  # Infinite AVS
                remaining = float('inf')
            else:
                remaining = total_avs - node.times_triggered_this_flip

            if remaining > best_remaining:
                best_remaining = remaining
                best_node = node

        # Handle ties randomly
        if best_node and best_remaining > 0:
            tied_nodes = [n for n in self.nodes.values()
                          if n != exclude_node and self._get_remaining_avs(n) == best_remaining]
            if tied_nodes:
                best_node = random.choice(tied_nodes)

        return best_node

    def _get_remaining_avs(self, node: NodeInstance) -> float:
        """Helper to get remaining AVS for a node"""
        total_avs = node.get_total_avs()
        if total_avs is None:
            return float('inf')
        return total_avs - node.times_triggered_this_flip

    def get_adjacent_nodes(self, node: NodeInstance) -> List[NodeInstance]:
        """Get all nodes adjacent to the given node"""
        pos = HexPosition(*node.definition.position)
        adjacent_positions = pos.neighbors()

        adjacent_nodes = []
        for adj_pos in adjacent_positions:
            adj_tuple = adj_pos.to_tuple()
            if adj_tuple in self.nodes:
                adjacent_nodes.append(self.nodes[adj_tuple])

        return adjacent_nodes

    def get_adjacent_with_most_avs(self, node: NodeInstance) -> Optional[NodeInstance]:
        """Find adjacent node with most remaining AVS"""
        adjacent = self.get_adjacent_nodes(node)
        if not adjacent:
            return None

        best_node = None
        best_remaining = -1

        for adj_node in adjacent:
            remaining = self._get_remaining_avs(adj_node)
            if remaining > best_remaining:
                best_remaining = remaining
                best_node = adj_node

        # Handle ties randomly
        if best_node and best_remaining > 0:
            tied_nodes = [n for n in adjacent if self._get_remaining_avs(n) == best_remaining]
            if tied_nodes:
                best_node = random.choice(tied_nodes)

        return best_node

    def handle_panic(self, panic_node: NodeInstance, game_state: GameState) -> GameState:
        """Handle Panic's adjacent node triggering"""
        adjacent_nodes = self.get_adjacent_nodes(panic_node)

        # Trigger adjacent nodes in order
        for adj_node in adjacent_nodes:
            game_state = self.trigger_node(adj_node, game_state)

        return game_state

    def handle_surgeon(self, surgeon_node: NodeInstance, game_state: GameState) -> GameState:
        """Handle Surgeon's effect - trigger node with most AVS 2 times"""
        target = self.get_node_with_most_avs(exclude_node=surgeon_node)
        if target:
            num_triggers = surgeon_node.definition.effect_params.get('num_triggers', 2)
            for _ in range(num_triggers):
                game_state = self.trigger_node(target, game_state)

        return game_state

    def handle_adrenaline(self, adrenaline_node: NodeInstance, game_state: GameState) -> GameState:
        """Handle Adrenaline's conditional adjacent triggering"""
        params = adrenaline_node.definition.effect_params
        threshold_1 = params.get('bb_threshold_1', 5)
        threshold_2 = params.get('bb_threshold_2', 10)

        adjacent = self.get_adjacent_nodes(adrenaline_node)
        if not adjacent:
            return game_state

        num_to_trigger = 0
        if game_state.battle_bonus > threshold_2:
            num_to_trigger = 2
        elif game_state.battle_bonus > threshold_1:
            num_to_trigger = 1

        # Trigger random adjacent nodes
        if num_to_trigger > 0:
            targets = random.sample(adjacent, min(num_to_trigger, len(adjacent)))
            for target in targets:
                game_state = self.trigger_node(target, game_state)

        return game_state

    def handle_focus(self, focus_node: NodeInstance, game_state: GameState) -> GameState:
        """Handle Focus's random adjacent trigger"""
        adjacent = self.get_adjacent_nodes(focus_node)
        if adjacent:
            target = random.choice(adjacent)
            game_state = self.trigger_node(target, game_state)

        return game_state

    def handle_stimulant(self, stimulant_node: NodeInstance, game_state: GameState) -> GameState:
        """Handle Stimulant's effect - trigger adjacent with most AVS 2 times"""
        target = self.get_adjacent_with_most_avs(stimulant_node)
        if target:
            num_triggers = stimulant_node.definition.effect_params.get('num_triggers', 2)
            for _ in range(num_triggers):
                game_state = self.trigger_node(target, game_state)

        return game_state


    def handle_low_point(self, low_point_node: NodeInstance, game_state: GameState) -> GameState:
        """Handle Low Point's effect - trigger 2 adjacent per loss"""
        params = low_point_node.definition.effect_params
        nodes_per_loss = params.get('nodes_per_loss', 2)

        # Count losses in this match
        losses = sum(1 for result in game_state.flip_history if not result)
        total_triggers = nodes_per_loss * losses

        adjacent = self.get_adjacent_nodes(low_point_node)
        if not adjacent or total_triggers == 0:
            return game_state

        # Trigger random adjacent nodes
        for _ in range(total_triggers):
            target = random.choice(adjacent)
            game_state = self.trigger_node(target, game_state)

        return game_state

    def count_depleted_nodes(self) -> int:
        """Count how many nodes are fully depleted"""
        count = 0
        for node in self.nodes.values():
            total_avs = node.get_total_avs()
            if total_avs is not None and node.times_triggered_this_flip >= total_avs:
                count += 1
        return count

    def handle_funeral_rites(self, funeral_node: NodeInstance, game_state: GameState) -> GameState:
        """Handle Funeral Rites XP gain"""
        params = funeral_node.definition.effect_params
        xp_per_depleted = params.get('xp_per_depleted', 500)

        depleted_count = self.count_depleted_nodes()
        xp_gain = xp_per_depleted * depleted_count

        if not hasattr(game_state, 'xp'):
            game_state.xp = 0
        game_state.xp += xp_gain

        return game_state

    def trigger_node(self, node: NodeInstance, game_state: GameState) -> GameState:
        """Trigger a single node and handle its special effects"""
        # Check if node can still trigger (has AVS remaining)
        if not node.can_trigger():
            # Track this as a wasted trigger on a depleted node
            game_state.depleted_triggers += 1
            return game_state

        # Execute the node's primary effect
        game_state = self.executor.execute(node, game_state)

        # Handle special trigger effects (only if primary effect succeeded)
        effect_type = node.definition.effect_type

        if effect_type == "trigger_adjacent":
            game_state = self.handle_panic(node, game_state)
        elif effect_type == "trigger_most_avs":
            game_state = self.handle_surgeon(node, game_state)
        elif effect_type == "add_bb_and_trigger":
            game_state = self.handle_adrenaline(node, game_state)
        elif effect_type == "trigger_random_adjacent":
            game_state = self.handle_focus(node, game_state)
        elif effect_type == "trigger_adjacent_most_avs":
            game_state = self.handle_stimulant(node, game_state)
        elif effect_type == "trigger_adjacent_per_loss":
            game_state = self.handle_low_point(node, game_state)
        elif effect_type == "xp_per_depleted":
            game_state = self.handle_funeral_rites(node, game_state)

        return game_state

    def simulate_flip(self, game_state: GameState, win: bool) -> GameState:
        """Simulate a single flip"""
        self.reset_nodes()

        # Record flip result
        game_state.flip_history.append(win)

        # Apply base Q change
        if win:
            game_state.q_this_flip = 100
            game_state.battle_bonus = 0  # Reset on win
        else:
            game_state.q_this_flip = -game_state.get_qdown_for_rank()
            game_state.battle_bonus += 1  # Increment on loss

        # Determine trigger types - "flip" nodes trigger on both win and loss
        trigger_types = ["flip"]
        if win:
            trigger_types.append("win")
        else:
            trigger_types.append("loss")

        # Get nodes to trigger in spiral order for each trigger type
        for trigger_type in trigger_types:
            nodes_to_trigger = self.get_nodes_to_trigger(game_state, trigger_type)

            # Execute each node
            for node in nodes_to_trigger:
                game_state = self.trigger_node(node, game_state)

        # Apply Qmult at the end
        game_state.apply_qmult()

        return game_state

    def simulate_round(self, flip_sequence: List[bool], rank: int = 1) -> GameState:
        """Simulate a full round (series of flips)"""
        game_state = GameState(rank=rank)

        for flip_result in flip_sequence:
            game_state = self.simulate_flip(game_state, flip_result)

        # Apply round win/loss multiplier
        wins = sum(flip_sequence)
        losses = len(flip_sequence) - wins

        if wins > losses:
            # Round WIN: 2x Qup, 2x gold, 2x xp
            game_state.q_currency *= 2
            if hasattr(game_state, 'gold'):
                game_state.gold *= 2
            if hasattr(game_state, 'xp'):
                game_state.xp *= 2
        else:
            # Round LOSS: 2x Qdown
            game_state.q_currency *= 2

        return game_state

    def simulate_all_round_outcomes(self, rounds_to_win: int = 3, max_flips: int = 5, rank: int = 1) -> Dict[str, GameState]:
        """Simulate all possible round outcomes"""
        from itertools import product

        results = {}

        # Generate all possible flip sequences
        for num_flips in range(rounds_to_win, max_flips + 1):
            for flip_sequence in product([True, False], repeat=num_flips):
                wins = sum(flip_sequence)
                losses = len(flip_sequence) - wins

                # Only include valid game endings
                if wins == rounds_to_win or losses == rounds_to_win:
                    # Check if game would have ended earlier
                    early_end = False
                    for i in range(len(flip_sequence) - 1):
                        partial_wins = sum(flip_sequence[:i+1])
                        partial_losses = i + 1 - partial_wins
                        if partial_wins == rounds_to_win or partial_losses == rounds_to_win:
                            early_end = True
                            break

                    if not early_end:
                        sequence_str = ''.join(['W' if f else 'L' for f in flip_sequence])
                        results[sequence_str] = self.simulate_round(list(flip_sequence), rank=rank)

        return results
