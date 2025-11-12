<template>
  <div class="upgrade-panel">
    <h3>Upgrades ({{ totalPoints }} / {{ budget }} points)</h3>

    <div class="upgrades-list">
      <div
        v-for="(node, name) in staticNodes"
        :key="name"
        class="upgrade-node"
      >
        <div class="node-header">
          <span class="node-name">{{ name }}</span>
          <span class="node-points">{{ getNodePoints(name) }}pts</span>
        </div>

        <div
          v-for="(path, pathIdx) in node.upgrade_paths"
          :key="`${name}-path-${pathIdx}`"
          class="upgrade-path"
        >
          <label class="path-label">Path {{ pathIdx + 1 }}</label>
          <input
            type="range"
            :min="0"
            :max="path.length"
            :value="upgrades[name]?.[pathIdx] || 0"
            @input="updateUpgrade(name, pathIdx, $event.target.value)"
            :disabled="isPathDisabled(name, pathIdx)"
            class="upgrade-slider"
          />
          <span class="path-level">{{ upgrades[name]?.[pathIdx] || 0 }} / {{ path.length }}</span>

          <div class="path-details">
            <div
              v-for="(step, stepIdx) in path"
              :key="`${name}-path-${pathIdx}-step-${stepIdx}`"
              :class="['upgrade-step', { active: (upgrades[name]?.[pathIdx] || 0) > stepIdx }]"
            >
              {{ formatUpgradeStep(step) }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    staticNodes: {
      type: Object,
      required: true
    },
    upgrades: {
      type: Object,
      required: true
    },
    budget: {
      type: Number,
      default: 18
    }
  },
  emits: ['update:upgrades'],
  computed: {
    totalPoints() {
      let total = 0
      for (const [nodeName, levels] of Object.entries(this.upgrades)) {
        if (Array.isArray(levels)) {
          total += levels.reduce((sum, level) => sum + level, 0)
        }
      }
      return total
    }
  },
  methods: {
    getNodePoints(nodeName) {
      const levels = this.upgrades[nodeName]
      if (!levels || !Array.isArray(levels)) return 0
      return levels.reduce((sum, level) => sum + level, 0)
    },

    updateUpgrade(nodeName, pathIdx, value) {
      const newLevel = parseInt(value)
      const updated = { ...this.upgrades }

      if (!updated[nodeName]) {
        const node = this.staticNodes[nodeName]
        updated[nodeName] = new Array(node.upgrade_paths.length).fill(0)
      }

      const oldLevel = updated[nodeName][pathIdx]
      updated[nodeName][pathIdx] = newLevel

      // Check budget
      const newTotal = Object.values(updated).reduce((sum, levels) =>
        sum + levels.reduce((s, l) => s + l, 0), 0)

      if (newTotal <= this.budget) {
        this.$emit('update:upgrades', updated)
      } else {
        // Revert if over budget
        updated[nodeName][pathIdx] = oldLevel
      }
    },

    isPathDisabled(nodeName, pathIdx) {
      const currentLevel = this.upgrades[nodeName]?.[pathIdx] || 0
      if (currentLevel > 0) return false // Can always decrease

      // Check if increasing would exceed budget
      return this.totalPoints >= this.budget
    },

    formatUpgradeStep(step) {
      if (step.avs_increase) return `+${step.avs_increase} AVS`
      if (step.effect_mult) return `${step.effect_mult}x effect`
      if (step.bb_multiplier_increase) return `+${step.bb_multiplier_increase} BB mult`
      if (step.depleted_reduction_percent) return `${(step.depleted_reduction_percent * 100).toFixed(0)}% depleted`
      if (step.q_increase) return `+${step.q_increase} Q`
      if (step.per_loss_increase) return `+${step.per_loss_increase} per loss`
      if (step.percent_increase) return `+${(step.percent_increase * 100).toFixed(0)}%`
      if (step.per_teammate_increase) return `+${step.per_teammate_increase} per teammate`
      if (step.noop) return '(no effect)'
      return JSON.stringify(step)
    }
  }
}
</script>

<style scoped>
.upgrade-panel {
  background: #16213e;
  padding: 15px;
  border-radius: 8px;
  height: 100%;
  overflow-y: auto;
}

h3 {
  margin-bottom: 15px;
  color: #eee;
  font-size: 16px;
}

.upgrades-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.upgrade-node {
  background: #0f0f1e;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid #2a2a3e;
}

.node-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.node-name {
  font-weight: bold;
  color: #eee;
  font-size: 14px;
}

.node-points {
  color: #ffa500;
  font-size: 12px;
  font-weight: bold;
}

.upgrade-path {
  margin-bottom: 15px;
  padding: 10px;
  background: #1a1a2e;
  border-radius: 4px;
}

.upgrade-path:last-child {
  margin-bottom: 0;
}

.path-label {
  display: inline-block;
  font-size: 12px;
  color: #aaa;
  margin-bottom: 6px;
}

.upgrade-slider {
  width: 100%;
  margin: 8px 0;
  cursor: pointer;
}

.upgrade-slider:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.path-level {
  font-size: 12px;
  color: #888;
  float: right;
}

.path-details {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.upgrade-step {
  font-size: 11px;
  color: #666;
  padding: 4px 8px;
  background: #0a0a14;
  border-radius: 3px;
  border-left: 2px solid #333;
}

.upgrade-step.active {
  color: #4a8a6a;
  border-left-color: #5a9a7a;
  background: #0f1a14;
}
</style>
