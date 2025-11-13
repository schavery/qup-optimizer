# effects/executor.py
from typing import Dict, Callable
from core.node import NodeInstance
from core.game_state import GameState

class EffectExecutor:
    """Handles executing different effect types"""

    def __init__(self):
        self.handlers: Dict[str, Callable] = {
            'add_to_qmult': self._add_to_qmult,
            'reduce_qdown': self._reduce_qdown,
            'flat_q': self._flat_q,
            'reduce_qdown_per_loss': self._reduce_qdown_per_loss,
            'trigger_adjacent': self._trigger_adjacent,
            'reduce_qdown_percent': self._reduce_qdown_percent,
            'flat_q_per_teammate_class': self._flat_q_per_teammate_class,
            'q_per_qdown_prevented': self._q_per_qdown_prevented,
            'flat_q_per_bb': self._flat_q_per_bb,
            'trigger_most_avs': self._trigger_most_avs,
            'add_bb_and_trigger': self._add_bb_and_trigger,
            'trigger_random_adjacent': self._trigger_random_adjacent,
            'trigger_adjacent_most_avs': self._trigger_adjacent_most_avs,
            'xp_per_depleted': self._xp_per_depleted,
            'multiply_qmult': self._multiply_qmult,
            'trigger_adjacent_per_loss': self._trigger_adjacent_per_loss,
            'add_bb': self._add_bb,
            'gold_per_qdown_prevented': self._gold_per_qdown_prevented,
            'defence_per_bb': self._defence_per_bb,
            'teammate_qdown_reduction_per_depleted': self._teammate_qdown_reduction_per_depleted,
        }

    def execute(self, node: NodeInstance, game_state: GameState) -> GameState:
        """Execute a node's effect"""
        effect_type = node.definition.effect_type
        handler = self.handlers.get(effect_type)

        if handler is None:
            raise ValueError(f"Unknown effect type: {effect_type}")

        # Increment trigger counter
        game_state.total_triggers += 1

        return handler(node, game_state)

    def _add_to_qmult(self, node: NodeInstance, game_state: GameState) -> GameState:
        """Battle Medic effect"""
        if not node.can_trigger():
            return game_state

        params = node.definition.effect_params
        source = params.get('multiplier_source', 'battle_bonus')

        # Get base multiplier value
        if source == 'battle_bonus':
            base_value = game_state.battle_bonus
        else:
            base_value = params.get('base_value', 0)

        # Apply upgrade multipliers
        effect_mult = 1
        for path_idx, level in enumerate(node.upgrade_levels):
            path = node.definition.upgrade_paths[path_idx]
            for step_idx in range(level):
                if 'effect_mult' in path[step_idx]:
                    effect_mult = path[step_idx]['effect_mult']

        game_state.qmult += base_value * effect_mult
        node.times_triggered_this_flip += 1
        return game_state

    def _reduce_qdown(self, node: NodeInstance, game_state: GameState) -> GameState:
        """EMT effect"""
        params = node.definition.effect_params
        avs = node.get_total_avs()

        # Check if depleted
        if avs is not None and node.times_triggered_this_flip >= avs:
            if not node.depleted_triggered:
                # Check for depleted effect upgrade (only one level has this, so replace)
                depleted_percent = 0
                for path_idx, level in enumerate(node.upgrade_levels):
                    path = node.definition.upgrade_paths[path_idx]
                    for step_idx in range(level):
                        if 'depleted_reduction_percent' in path[step_idx]:
                            depleted_percent = path[step_idx]['depleted_reduction_percent']

                if depleted_percent > 0:
                    reduction = int(abs(game_state.q_this_flip) * depleted_percent)
                    game_state.q_this_flip += reduction
                    node.depleted_triggered = True
            return game_state

        if not node.can_trigger():
            return game_state

        # Calculate base reduction
        base_reduction = params['base_reduction']
        bb_multiplier = params['bb_multiplier']

        # Apply upgrade replacements to bb_multiplier
        for path_idx, level in enumerate(node.upgrade_levels):
            path = node.definition.upgrade_paths[path_idx]
            for step_idx in range(level):
                if 'bb_multiplier_increase' in path[step_idx]:
                    bb_multiplier = path[step_idx]['bb_multiplier_increase']

        total_reduction = base_reduction + (bb_multiplier * game_state.battle_bonus)
        game_state.q_this_flip += total_reduction
        node.times_triggered_this_flip += 1
        return game_state

    def _flat_q(self, node: NodeInstance, game_state: GameState) -> GameState:
        """Self Diagnosis effect"""
        if not node.can_trigger():
            return game_state

        params = node.definition.effect_params
        q_amount = params['base_amount']

        # Apply upgrade replacements
        for path_idx, level in enumerate(node.upgrade_levels):
            path = node.definition.upgrade_paths[path_idx]
            for step_idx in range(level):
                if 'q_increase' in path[step_idx]:
                    q_amount = path[step_idx]['q_increase']

        game_state.q_this_flip += q_amount
        node.times_triggered_this_flip += 1
        return game_state

    def _reduce_qdown_per_loss(self, node: NodeInstance, game_state: GameState) -> GameState:
        """Stop the Bleeding effect"""
        if not node.can_trigger():
            return game_state

        params = node.definition.effect_params
        per_loss = params['base_per_loss']

        # Apply upgrade replacements
        for path_idx, level in enumerate(node.upgrade_levels):
            path = node.definition.upgrade_paths[path_idx]
            for step_idx in range(level):
                if 'per_loss_increase' in path[step_idx]:
                    per_loss = path[step_idx]['per_loss_increase']

        # Count losses in flip_history
        losses = sum(1 for result in game_state.flip_history if not result)
        total_reduction = per_loss * losses

        game_state.q_this_flip += total_reduction
        node.times_triggered_this_flip += 1
        return game_state

    def _trigger_adjacent(self, node: NodeInstance, game_state: GameState) -> GameState:
        """Panic effect - triggers adjacent nodes"""
        # This will be handled specially in the simulator
        # Just mark that it triggered
        if node.can_trigger():
            node.times_triggered_this_flip += 1
        return game_state

    def _reduce_qdown_percent(self, node: NodeInstance, game_state: GameState) -> GameState:
        """Triage effect - percentage reduction"""
        if not node.can_trigger():
            return game_state

        params = node.definition.effect_params
        percent = params['base_percent']

        # Apply upgrade replacements
        for path_idx, level in enumerate(node.upgrade_levels):
            path = node.definition.upgrade_paths[path_idx]
            for step_idx in range(level):
                if 'percent_increase' in path[step_idx]:
                    percent = path[step_idx]['percent_increase']

        # Apply percentage reduction (only on negative q_this_flip)
        if game_state.q_this_flip < 0:
            reduction = int(abs(game_state.q_this_flip) * percent)
            game_state.q_this_flip += reduction

        node.times_triggered_this_flip += 1
        return game_state

    def _flat_q_per_teammate_class(self, node: NodeInstance, game_state: GameState) -> GameState:
        """Big Sister effect"""
        if not node.can_trigger():
            return game_state

        params = node.definition.effect_params
        per_teammate = params['base_per_teammate']
        teammate_class = params['teammate_class']

        # Apply upgrade replacements
        for path_idx, level in enumerate(node.upgrade_levels):
            path = node.definition.upgrade_paths[path_idx]
            for step_idx in range(level):
                if 'per_teammate_increase' in path[step_idx]:
                    per_teammate = path[step_idx]['per_teammate_increase']

        # For single player optimization, assume 0 gamblers for now
        # This can be parameterized later
        num_gamblers = game_state.__dict__.get('num_gamblers', 0)
        total_q = per_teammate * num_gamblers

        game_state.q_this_flip += total_q
        node.times_triggered_this_flip += 1
        return game_state

    def _q_per_qdown_prevented(self, node: NodeInstance, game_state: GameState) -> GameState:
        """Angel effect - reward for Qdown prevention"""
        if not node.can_trigger():
            return game_state

        # Calculate Qdown prevented
        # This is tracked as the difference between base Qdown and current q_this_flip
        base_qdown = -game_state.get_qdown_for_rank()
        current_q = game_state.q_this_flip

        # Only applies on loss when we've prevented some Qdown
        if current_q > base_qdown:
            qdown_prevented = current_q - base_qdown
            game_state.q_this_flip += qdown_prevented  # +1Q per point prevented

        node.times_triggered_this_flip += 1
        return game_state

    def _flat_q_per_bb(self, node: NodeInstance, game_state: GameState) -> GameState:
        """Exhilaration effect"""
        if not node.can_trigger():
            return game_state

        params = node.definition.effect_params
        q_per_bb = params['q_per_bb']

        game_state.q_this_flip += q_per_bb * game_state.battle_bonus
        node.times_triggered_this_flip += 1
        return game_state

    def _trigger_most_avs(self, node: NodeInstance, game_state: GameState) -> GameState:
        """Surgeon effect - triggers handled in simulator"""
        if node.can_trigger():
            node.times_triggered_this_flip += 1
        return game_state

    def _add_bb_and_trigger(self, node: NodeInstance, game_state: GameState) -> GameState:
        """Adrenaline effect - add to BB, triggers handled in simulator"""
        if not node.can_trigger():
            return game_state

        game_state.battle_bonus += 1
        node.times_triggered_this_flip += 1
        return game_state

    def _trigger_random_adjacent(self, node: NodeInstance, game_state: GameState) -> GameState:
        """Focus effect - triggers handled in simulator"""
        if node.can_trigger():
            node.times_triggered_this_flip += 1
        return game_state

    def _trigger_adjacent_most_avs(self, node: NodeInstance, game_state: GameState) -> GameState:
        """Stimulant effect - triggers handled in simulator"""
        if node.can_trigger():
            node.times_triggered_this_flip += 1
        return game_state

    def _xp_per_depleted(self, node: NodeInstance, game_state: GameState) -> GameState:
        """Funeral Rites effect"""
        if not node.can_trigger():
            return game_state

        # This will be counted in simulator
        node.times_triggered_this_flip += 1
        return game_state

    def _multiply_qmult(self, node: NodeInstance, game_state: GameState) -> GameState:
        """Angel of Death effect"""
        if not node.can_trigger():
            return game_state

        params = node.definition.effect_params
        multiplier = params.get('multiplier', 3)

        game_state.qmult *= multiplier
        node.times_triggered_this_flip += 1
        return game_state

    def _trigger_adjacent_per_loss(self, node: NodeInstance, game_state: GameState) -> GameState:
        """Low Point effect - handled in simulator"""
        if node.can_trigger():
            node.times_triggered_this_flip += 1
        return game_state

    def _add_bb(self, node: NodeInstance, game_state: GameState) -> GameState:
        """Deployment effect"""
        if not node.can_trigger():
            return game_state

        params = node.definition.effect_params
        bb_increase = params.get('bb_increase', 1)

        game_state.battle_bonus += bb_increase
        node.times_triggered_this_flip += 1
        return game_state

    def _gold_per_qdown_prevented(self, node: NodeInstance, game_state: GameState) -> GameState:
        """Insurance Scam effect"""
        if not node.can_trigger():
            return game_state

        params = node.definition.effect_params
        qdown_per_gold = params.get('qdown_per_gold', 33)

        # Calculate Qdown prevented
        base_qdown = -game_state.get_qdown_for_rank()
        current_q = game_state.q_this_flip

        if current_q > base_qdown:
            qdown_prevented = current_q - base_qdown
            gold = qdown_prevented // qdown_per_gold
            # Store in game_state if we're tracking gold
            if not hasattr(game_state, 'gold'):
                game_state.gold = 0
            game_state.gold += gold

        node.times_triggered_this_flip += 1
        return game_state

    def _defence_per_bb(self, node: NodeInstance, game_state: GameState) -> GameState:
        """Battle Hardened effect"""
        if not node.can_trigger():
            return game_state

        params = node.definition.effect_params
        defence_per_bb = params.get('defence_per_bb', 2)

        defence_gain = defence_per_bb * game_state.battle_bonus
        # Store in game_state if we're tracking defence
        if not hasattr(game_state, 'defence'):
            game_state.defence = 0
        game_state.defence += defence_gain

        node.times_triggered_this_flip += 1
        return game_state

    def _teammate_qdown_reduction_per_depleted(self, node: NodeInstance, game_state: GameState) -> GameState:
        """Precision Cut effect - handled in simulator for access to depleted count"""
        if node.can_trigger():
            node.times_triggered_this_flip += 1
        return game_state
