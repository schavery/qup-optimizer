<template>
  <div class="results-panel">
    <h3>Simulation Results</h3>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Evaluating layout...</p>
    </div>

    <div v-else-if="error" class="error">
      <p>{{ error }}</p>
    </div>

    <div v-else-if="result" class="results">
      <!-- Summary Stats -->
      <div class="stats-grid">
        <div class="stat-card stat-min">
          <div class="stat-label">Worst Case</div>
          <div class="stat-value">{{ formatQ(result.min_q) }}</div>
        </div>
        <div class="stat-card stat-max">
          <div class="stat-label">Best Case</div>
          <div class="stat-value">{{ formatQ(result.max_q) }}</div>
        </div>
        <div class="stat-card stat-avg">
          <div class="stat-label">Average</div>
          <div class="stat-value">{{ formatQ(result.avg_q) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Positive Outcomes</div>
          <div class="stat-value">{{ result.positive_outcomes }}/{{ result.total_outcomes }}</div>
        </div>
      </div>

      <!-- Trigger Metrics -->
      <div class="metrics">
        <h4>Trigger Metrics</h4>
        <div class="metric-row">
          <span>Max Triggers/Flip:</span>
          <span class="metric-value">{{ result.max_triggers_per_flip }}</span>
        </div>
        <div class="metric-row">
          <span>Avg Efficiency:</span>
          <span class="metric-value">{{ (result.avg_efficiency * 100).toFixed(1) }}%</span>
        </div>
        <div class="metric-row">
          <span>Adjacency Score:</span>
          <span class="metric-value">{{ result.adjacency_score.toFixed(2) }}</span>
        </div>
      </div>

      <!-- Outcome Spectrum -->
      <div class="outcomes">
        <h4>Q Outcome Spectrum</h4>
        <div class="outcome-list">
          <div
            v-for="(q, sequence) in sortedOutcomes"
            :key="sequence"
            class="outcome-row"
          >
            <span class="outcome-sequence">{{ sequence }}</span>
            <div class="outcome-bar-container">
              <div
                class="outcome-bar"
                :style="getBarStyle(q)"
              ></div>
            </div>
            <span class="outcome-value" :class="q >= 0 ? 'positive' : 'negative'">
              {{ formatQ(q) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="empty">
      <p>Make changes to see results</p>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    result: {
      type: Object,
      default: null
    },
    loading: {
      type: Boolean,
      default: false
    },
    error: {
      type: String,
      default: null
    }
  },
  computed: {
    sortedOutcomes() {
      if (!this.result || !this.result.outcomes) return {}

      // Sort by number of wins (descending)
      const entries = Object.entries(this.result.outcomes)
      entries.sort((a, b) => {
        const winsA = (a[0].match(/W/g) || []).length
        const winsB = (b[0].match(/W/g) || []).length
        return winsB - winsA
      })

      return Object.fromEntries(entries)
    }
  },
  methods: {
    formatQ(value) {
      if (value >= 1000000) return `${(value / 1000000).toFixed(2)}M`
      if (value >= 1000) return `${(value / 1000).toFixed(1)}K`
      if (value <= -1000000) return `${(value / 1000000).toFixed(2)}M`
      if (value <= -1000) return `${(value / 1000).toFixed(1)}K`
      return value.toString()
    },

    getBarStyle(q) {
      const maxAbsQ = Math.max(
        Math.abs(this.result.min_q),
        Math.abs(this.result.max_q)
      )

      const width = Math.abs(q) / maxAbsQ * 100
      const color = q >= 0 ? '#4a8a6a' : '#8a4a4a'

      return {
        width: `${width}%`,
        backgroundColor: color
      }
    }
  }
}
</script>

<style scoped>
.results-panel {
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

h4 {
  margin: 15px 0 10px;
  color: #ccc;
  font-size: 13px;
  border-bottom: 1px solid #2a2a3e;
  padding-bottom: 6px;
}

.loading, .error, .empty {
  text-align: center;
  padding: 40px 20px;
  color: #888;
}

.spinner {
  width: 40px;
  height: 40px;
  margin: 0 auto 20px;
  border: 3px solid #2a2a3e;
  border-top-color: #5a9a7a;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error {
  color: #e66;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  margin-bottom: 15px;
}

.stat-card {
  background: #0f0f1e;
  padding: 10px;
  border-radius: 6px;
  border: 1px solid #2a2a3e;
}

.stat-label {
  font-size: 10px;
  color: #888;
  text-transform: uppercase;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 16px;
  font-weight: bold;
  color: #eee;
}

.stat-min .stat-value { color: #e88; }
.stat-max .stat-value { color: #8e8; }
.stat-avg .stat-value { color: #88e; }

.metrics {
  background: #0f0f1e;
  padding: 15px;
  border-radius: 6px;
  border: 1px solid #2a2a3e;
}

.metric-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  font-size: 13px;
  color: #aaa;
  border-bottom: 1px solid #1a1a2e;
}

.metric-row:last-child {
  border-bottom: none;
}

.metric-value {
  color: #eee;
  font-weight: bold;
}

.outcomes {
  margin-top: 20px;
}

.outcome-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.outcome-row {
  display: grid;
  grid-template-columns: 60px 1fr 80px;
  align-items: center;
  gap: 10px;
  font-size: 12px;
}

.outcome-sequence {
  font-family: monospace;
  color: #aaa;
  font-weight: bold;
}

.outcome-bar-container {
  height: 18px;
  background: #0a0a14;
  border-radius: 3px;
  overflow: hidden;
}

.outcome-bar {
  height: 100%;
  transition: width 0.3s;
}

.outcome-value {
  text-align: right;
  font-weight: bold;
}

.outcome-value.positive {
  color: #6a6;
}

.outcome-value.negative {
  color: #e66;
}
</style>
