<template>
  <div class="upgrade-panel">
    <div class="panel-header">
      <h3>Upgrades ({{ totalPoints }} / {{ budget }} points)</h3>
      <button @click="showOptimizer = !showOptimizer" class="btn-optimize">
        {{ showOptimizer ? 'Hide' : 'Optimize' }}
      </button>
    </div>

    <div v-if="showOptimizer" class="optimizer-section">
      <div class="optimizer-controls">
        <button @click="generateOptimizedConfigs" :disabled="loading" class="btn-generate">
          {{ loading ? 'Generating...' : 'Generate Top 5' }}
        </button>
      </div>
      <div v-if="optimizedConfigs.length > 0" class="config-list">
        <div
          v-for="(config, idx) in optimizedConfigs"
          :key="idx"
          class="config-item"
          @click="applyConfig(config)"
        >
          <div class="config-header">
            <span class="config-rank">#{{ idx + 1 }}</span>
            <span class="config-points">{{ getTotalPoints(config) }}pts</span>
          </div>
          <div class="config-details">
            <div v-for="(levels, nodeName) in config" :key="nodeName" class="config-node">
              <span class="node-name">{{ nodeName }}:</span>
              <span class="node-levels">[{{ levels.join(', ') }}]</span>
            </div>
          </div>
        </div>
      </div>
    </div>

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
  data() {
    return {
      showOptimizer: false,
      optimizedConfigs: [],
      loading: false
    }
  },
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
    async generateOptimizedConfigs() {
      this.loading = true
      try {
        console.log('Generating upgrade configs with budget:', this.budget)
        const response = await fetch('/api/generate-upgrades', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ budget: this.budget, strategy: 'tiered' })
        })

        if (!response.ok) {
          const error = await response.json()
          throw new Error(error.error || 'Failed to generate configs')
        }

        const data = await response.json()
        console.log('Generated configs:', data)
        this.optimizedConfigs = data.configs.slice(0, 5)
        console.log('Showing top 5:', this.optimizedConfigs)
      } catch (err) {
        console.error('Failed to generate configs:', err)
        alert('Error: ' + err.message)
      } finally {
        this.loading = false
      }
    },

    applyConfig(config) {
      console.log('Applying config:', config)
      const newUpgrades = {}

      // Initialize all static nodes with zeros first
      for (const name in this.staticNodes) {
        newUpgrades[name] = new Array(this.staticNodes[name].upgrade_paths.length).fill(0)
      }

      // Then apply the config
      for (const [nodeName, levels] of Object.entries(config)) {
        newUpgrades[nodeName] = levels
      }

      console.log('New upgrades:', newUpgrades)
      this.$emit('update:upgrades', newUpgrades)
      this.showOptimizer = false
    },

    getTotalPoints(config) {
      let total = 0
      for (const levels of Object.values(config)) {
        if (Array.isArray(levels)) {
          total += levels.reduce((sum, level) => sum + level, 0)
        }
      }
      return total
    },
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

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

h3 {
  margin: 0;
  color: #eee;
  font-size: 16px;
}

.btn-optimize {
  padding: 4px 12px;
  background: #4a4a6e;
  color: #eee;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: background 0.2s;
}

.btn-optimize:hover {
  background: #5a5a7e;
}

.optimizer-section {
  background: #0f0f1e;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 15px;
  border: 1px solid #2a2a3e;
}

.optimizer-controls {
  margin-bottom: 10px;
}

.btn-generate {
  width: 100%;
  padding: 8px;
  background: #5a9a7a;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
}

.btn-generate:hover:not(:disabled) {
  background: #4a8a6a;
}

.btn-generate:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.config-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.config-item {
  background: #1a1a2e;
  padding: 10px;
  border-radius: 4px;
  cursor: pointer;
  border: 1px solid #2a2a3e;
  transition: all 0.2s;
}

.config-item:hover {
  background: #252538;
  border-color: #5a9a7a;
}

.config-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  font-weight: bold;
}

.config-rank {
  color: #aaa;
  font-size: 12px;
}

.config-points {
  color: #ffa500;
  font-size: 12px;
}

.config-details {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.config-node {
  font-size: 11px;
  color: #ccc;
}

.node-name {
  color: #888;
}

.node-levels {
  color: #5a9a7a;
  font-weight: 500;
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
