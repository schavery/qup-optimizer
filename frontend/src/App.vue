<template>
  <div id="app">
    <header class="app-header">
      <h1>Qup Skill Tree Optimizer</h1>
      <div class="controls">
        <label>
          Rank:
          <select v-model.number="rank" @change="debouncedEvaluate">
            <option v-for="r in 10" :key="r" :value="30 + r">
              {{ getRankName(30 + r) }}
            </option>
          </select>
        </label>
        <button @click="randomizeLayout" class="btn-secondary">
          Randomize Layout
        </button>
        <button @click="resetLayout" class="btn-secondary">
          Reset
        </button>
      </div>
    </header>

    <main class="app-main">
      <aside class="sidebar-left">
        <UpgradePanel
          :static-nodes="staticNodes"
          :upgrades="upgrades"
          :budget="18"
          @update:upgrades="handleUpgradesUpdate"
        />
      </aside>

      <section class="grid-section">
        <HexGrid
          :static-nodes="staticNodes"
          :movable-positions="movablePositions"
          :radius="8"
          @update:movablePositions="handlePositionsUpdate"
        />
      </section>

      <aside class="sidebar-right">
        <ResultsPanel
          :result="evaluationResult"
          :loading="evaluating"
          :error="evaluationError"
        />
      </aside>
    </main>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import HexGrid from './components/HexGrid.vue'
import UpgradePanel from './components/UpgradePanel.vue'
import ResultsPanel from './components/ResultsPanel.vue'
import { api } from './utils/api'

export default {
  components: {
    HexGrid,
    UpgradePanel,
    ResultsPanel
  },
  setup() {
    const staticNodes = ref({})
    const movableNodes = ref({})
    const movablePositions = ref({})
    const upgrades = ref({})
    const rank = ref(31)
    const evaluationResult = ref(null)
    const evaluating = ref(false)
    const evaluationError = ref(null)

    let evaluateTimeout = null

    // Load nodes from API
    onMounted(async () => {
      try {
        const nodes = await api.getNodes()
        staticNodes.value = nodes.static
        movableNodes.value = nodes.movable

        // Initialize upgrades (all zeros)
        for (const [name, node] of Object.entries(nodes.static)) {
          upgrades.value[name] = new Array(node.upgrade_paths.length).fill(0)
        }

        // Initialize default layout (place movable nodes in rings 5-7)
        const movableNames = Object.keys(nodes.movable)
        const rings = [5, 6, 7]
        let nodeIdx = 0

        for (const ring of rings) {
          // Place nodes around the ring
          for (let q = -ring; q <= ring && nodeIdx < movableNames.length; q++) {
            for (let r = -ring; r <= ring && nodeIdx < movableNames.length; r++) {
              const s = -q - r
              if (Math.max(Math.abs(q), Math.abs(r), Math.abs(s)) === ring) {
                // Check if position is free
                if (!isOccupied([q, r, s], nodes.static, movablePositions.value)) {
                  movablePositions.value[movableNames[nodeIdx]] = [q, r, s]
                  nodeIdx++
                  if (nodeIdx >= movableNames.length) break
                }
              }
            }
          }
        }

        // Initial evaluation
        evaluateLayout()
      } catch (err) {
        console.error('Failed to load nodes:', err)
        evaluationError.value = 'Failed to load node definitions'
      }
    })

    function isOccupied(pos, staticNodesObj, movablePositionsObj) {
      // Check static nodes
      for (const node of Object.values(staticNodesObj)) {
        if (posEqual(node.position, pos)) return true
      }
      // Check movable positions
      for (const mpos of Object.values(movablePositionsObj)) {
        if (posEqual(mpos, pos)) return true
      }
      return false
    }

    function posEqual(p1, p2) {
      return p1[0] === p2[0] && p1[1] === p2[1] && p1[2] === p2[2]
    }

    async function evaluateLayout() {
      evaluating.value = true
      evaluationError.value = null

      try {
        const result = await api.evaluateLayout(
          movablePositions.value,
          upgrades.value,
          rank.value
        )
        evaluationResult.value = result
      } catch (err) {
        console.error('Evaluation failed:', err)
        evaluationError.value = err.response?.data?.error || 'Evaluation failed'
      } finally {
        evaluating.value = false
      }
    }

    function debouncedEvaluate() {
      if (evaluateTimeout) clearTimeout(evaluateTimeout)
      evaluateTimeout = setTimeout(() => {
        evaluateLayout()
      }, 500)
    }

    function handlePositionsUpdate(newPositions) {
      movablePositions.value = newPositions
      debouncedEvaluate()
    }

    function handleUpgradesUpdate(newUpgrades) {
      upgrades.value = newUpgrades
      debouncedEvaluate()
    }

    async function randomizeLayout() {
      try {
        const response = await api.generateLayouts(1, rank.value, null, upgrades.value)
        if (response.layouts && response.layouts.length > 0) {
          const layout = response.layouts[0].layout
          // Extract only movable nodes
          const newPositions = {}
          for (const [name, pos] of Object.entries(layout)) {
            if (movableNodes.value[name]) {
              newPositions[name] = pos
            }
          }
          movablePositions.value = newPositions
          evaluateLayout()
        }
      } catch (err) {
        console.error('Failed to generate layout:', err)
      }
    }

    function resetLayout() {
      // Reset to default positions
      const movableNames = Object.keys(movableNodes.value)
      const newPositions = {}
      let nodeIdx = 0

      for (let ring = 5; ring <= 7 && nodeIdx < movableNames.length; ring++) {
        for (let q = -ring; q <= ring && nodeIdx < movableNames.length; q++) {
          for (let r = -ring; r <= ring && nodeIdx < movableNames.length; r++) {
            const s = -q - r
            if (Math.max(Math.abs(q), Math.abs(r), Math.abs(s)) === ring) {
              if (!isOccupied([q, r, s], staticNodes.value, newPositions)) {
                newPositions[movableNames[nodeIdx]] = [q, r, s]
                nodeIdx++
              }
            }
          }
        }
      }

      movablePositions.value = newPositions
      evaluateLayout()
    }

    function getRankName(r) {
      if (r >= 31) return `Grandmaster ${r - 30}`
      if (r >= 21) return `Master ${r - 20}`
      return `Rank ${r}`
    }

    return {
      staticNodes,
      movableNodes,
      movablePositions,
      upgrades,
      rank,
      evaluationResult,
      evaluating,
      evaluationError,
      handlePositionsUpdate,
      handleUpgradesUpdate,
      randomizeLayout,
      resetLayout,
      getRankName,
      debouncedEvaluate
    }
  }
}
</script>

<style>
#app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #0f0f1e;
  color: #eee;
}

.app-header {
  background: #16213e;
  padding: 20px 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 2px solid #2a2a3e;
}

.app-header h1 {
  font-size: 24px;
  margin: 0;
  color: #eee;
}

.controls {
  display: flex;
  gap: 15px;
  align-items: center;
}

.controls label {
  font-size: 14px;
  color: #ccc;
}

.controls select {
  margin-left: 8px;
  padding: 6px 12px;
  background: #0f0f1e;
  color: #eee;
  border: 1px solid #2a2a3e;
  border-radius: 4px;
  cursor: pointer;
}

button {
  padding: 8px 16px;
  background: #5a9a7a;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.2s;
}

button:hover {
  background: #4a8a6a;
}

.btn-secondary {
  background: #4a4a6e;
}

.btn-secondary:hover {
  background: #5a5a7e;
}

.app-main {
  flex: 1;
  display: grid;
  grid-template-columns: minmax(280px, 300px) minmax(500px, 1fr) minmax(300px, 350px);
  gap: 15px;
  padding: 15px;
  overflow: hidden;
  min-height: 0;
}

.sidebar-left,
.sidebar-right {
  overflow-y: auto;
  min-height: 0;
}

.grid-section {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 0;
  overflow: hidden;
}

/* Responsive layout for smaller screens */
@media (max-width: 1400px) {
  .app-main {
    grid-template-columns: 260px 1fr 280px;
    gap: 12px;
    padding: 12px;
  }
}

@media (max-width: 1200px) {
  .app-main {
    grid-template-columns: 240px 1fr 260px;
    gap: 10px;
    padding: 10px;
  }
}

/* Scrollbar styling */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #0f0f1e;
}

::-webkit-scrollbar-thumb {
  background: #2a2a3e;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #3a3a4e;
}
</style>
