<template>
  <div id="app">
    <header class="app-header">
      <h1>Qup Skill Tree Optimizer</h1>
      <div class="controls">
        <label>
          Initial BB:
          <input
            type="number"
            v-model.number="initialBB"
            @input="debouncedEvaluate"
            min="0"
            max="100"
            class="bb-input"
          />
        </label>
        <label>
          Rank:
          <select v-model.number="rank" @change="debouncedEvaluate">
            <optgroup label="Bronze">
              <option v-for="r in 5" :key="r" :value="r">Bronze {{ r }}</option>
            </optgroup>
            <optgroup label="Silver">
              <option v-for="r in 5" :key="5+r" :value="5+r">Silver {{ r }}</option>
            </optgroup>
            <optgroup label="Gold">
              <option v-for="r in 5" :key="10+r" :value="10+r">Gold {{ r }}</option>
            </optgroup>
            <optgroup label="Platinum">
              <option v-for="r in 5" :key="15+r" :value="15+r">Platinum {{ r }}</option>
            </optgroup>
            <optgroup label="Diamond">
              <option v-for="r in 5" :key="20+r" :value="20+r">Diamond {{ r }}</option>
            </optgroup>
            <optgroup label="Master">
              <option v-for="r in 5" :key="25+r" :value="25+r">Master {{ r }}</option>
            </optgroup>
            <optgroup label="Grandmaster">
              <option v-for="r in 5" :key="30+r" :value="30+r">Grandmaster {{ r }}</option>
            </optgroup>
            <optgroup label="Legend">
              <option v-for="r in 5" :key="35+r" :value="35+r">Legend {{ r }}</option>
            </optgroup>
          </select>
        </label>
        <span class="rank-info" v-if="rankInfo">
          Qdown: {{ formatQ(rankInfo.qdown_per_flip) }}
        </span>
        <button @click="randomizeLayout" class="btn-secondary" :disabled="evaluating">
          {{ evaluating ? 'Optimizing...' : 'Generate Optimized Layout' }}
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
          :movable-nodes="movableNodes"
          :movable-positions="movablePositions"
          :upgrades="upgrades"
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
import { ref, onMounted, watch } from 'vue'
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
    const initialBB = ref(0)
    const evaluationResult = ref(null)
    const evaluating = ref(false)
    const evaluationError = ref(null)
    const rankInfo = ref(null)

    let evaluateTimeout = null

    // LocalStorage keys
    const STORAGE_KEYS = {
      MOVABLE_POSITIONS: 'qup_movable_positions',
      UPGRADES: 'qup_upgrades',
      RANK: 'qup_rank',
      INITIAL_BB: 'qup_initial_bb'
    }

    // Save state to localStorage
    function saveState() {
      try {
        localStorage.setItem(STORAGE_KEYS.MOVABLE_POSITIONS, JSON.stringify(movablePositions.value))
        localStorage.setItem(STORAGE_KEYS.UPGRADES, JSON.stringify(upgrades.value))
        localStorage.setItem(STORAGE_KEYS.RANK, rank.value.toString())
        localStorage.setItem(STORAGE_KEYS.INITIAL_BB, initialBB.value.toString())
      } catch (err) {
        console.error('Failed to save state:', err)
      }
    }

    // Load state from localStorage
    function loadState() {
      try {
        const savedPositions = localStorage.getItem(STORAGE_KEYS.MOVABLE_POSITIONS)
        const savedUpgrades = localStorage.getItem(STORAGE_KEYS.UPGRADES)
        const savedRank = localStorage.getItem(STORAGE_KEYS.RANK)
        const savedBB = localStorage.getItem(STORAGE_KEYS.INITIAL_BB)

        return {
          positions: savedPositions ? JSON.parse(savedPositions) : null,
          upgrades: savedUpgrades ? JSON.parse(savedUpgrades) : null,
          rank: savedRank ? parseInt(savedRank) : null,
          initialBB: savedBB ? parseInt(savedBB) : null
        }
      } catch (err) {
        console.error('Failed to load state:', err)
        return { positions: null, upgrades: null, rank: null, initialBB: null }
      }
    }

    // Load rank info
    async function loadRankInfo(r) {
      try {
        const response = await api.getRank(r)
        rankInfo.value = response
      } catch (err) {
        console.error('Failed to load rank info:', err)
      }
    }

    // Load nodes from API
    onMounted(async () => {
      try {
        const nodes = await api.getNodes()
        staticNodes.value = nodes.static
        movableNodes.value = nodes.movable

        // Load saved state from localStorage
        const savedState = loadState()

        // Restore rank and BB if saved
        if (savedState.rank !== null) {
          rank.value = savedState.rank
        }
        if (savedState.initialBB !== null) {
          initialBB.value = savedState.initialBB
        }

        // Load rank info
        loadRankInfo(rank.value)

        // Initialize or restore upgrades
        if (savedState.upgrades) {
          // Restore saved upgrades
          upgrades.value = savedState.upgrades
        } else {
          // Initialize upgrades (all zeros)
          for (const [name, node] of Object.entries(nodes.static)) {
            upgrades.value[name] = new Array(node.upgrade_paths.length).fill(0)
          }
        }

        // Initialize or restore movable positions
        if (savedState.positions) {
          // Restore saved positions
          movablePositions.value = savedState.positions
        } else {
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
        }

        // Initial evaluation
        evaluateLayout()
      } catch (err) {
        console.error('Failed to load nodes:', err)
        evaluationError.value = 'Failed to load node definitions'
      }
    })

    // Watch for changes to rank and initialBB and save to localStorage
    watch(rank, () => {
      saveState()
    })

    watch(initialBB, () => {
      saveState()
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
          rank.value,
          initialBB.value
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
      loadRankInfo(rank.value)
      evaluateTimeout = setTimeout(() => {
        evaluateLayout()
      }, 500)
    }

    function formatQ(value) {
      const absValue = Math.abs(value)
      if (absValue >= 1000000) return `${(value / 1000000).toFixed(2)}M`
      if (absValue >= 1000) return `${(value / 1000).toFixed(1)}K`
      return value.toString()
    }

    function handlePositionsUpdate(newPositions) {
      movablePositions.value = newPositions
      saveState()
      debouncedEvaluate()
    }

    function handleUpgradesUpdate(newUpgrades) {
      upgrades.value = newUpgrades
      saveState()
      debouncedEvaluate()
    }

    async function randomizeLayout() {
      try {
        console.log('Generating refined layout...')
        evaluating.value = true
        evaluationError.value = null

        const response = await api.generateLayouts(
          20,  // Generate 20 candidates
          rank.value,
          Date.now(),
          upgrades.value,
          {
            initialBB: initialBB.value,
            refine: true,           // Enable refinement
            refineCount: 5,         // Refine top 5 diverse candidates
            refineIterations: 30    // 30 iterations per candidate
          }
        )

        console.log('Response:', response)

        if (response.cache_stats) {
          console.log('Cache stats:', response.cache_stats)
          console.log(`  Hit rate: ${(response.cache_stats.hit_rate * 100).toFixed(1)}%`)
          console.log(`  Refined: ${response.refined_count} candidates`)
        }

        if (response.layouts && response.layouts.length > 0) {
          const layout = response.layouts[0].layout
          console.log('Best refined layout (min_q:', response.layouts[0].min_q, ')')

          // Extract only movable nodes
          const newPositions = {}
          for (const [name, pos] of Object.entries(layout)) {
            if (movableNodes.value[name]) {
              newPositions[name] = pos
            }
          }
          console.log('New movable positions:', newPositions)
          movablePositions.value = newPositions

          // Save the new layout
          saveState()

          // Evaluate the layout to update UI
          evaluateLayout()
        }
      } catch (err) {
        console.error('Failed to generate layout:', err)
        evaluationError.value = 'Failed to generate refined layout: ' + (err.response?.data?.error || err.message)
      } finally {
        evaluating.value = false
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
      saveState()
      evaluateLayout()
    }

    return {
      staticNodes,
      movableNodes,
      movablePositions,
      upgrades,
      rank,
      initialBB,
      rankInfo,
      evaluationResult,
      evaluating,
      evaluationError,
      handlePositionsUpdate,
      handleUpgradesUpdate,
      randomizeLayout,
      resetLayout,
      debouncedEvaluate,
      formatQ
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

.bb-input {
  margin-left: 8px;
  padding: 6px 12px;
  width: 70px;
  background: #0f0f1e;
  color: #eee;
  border: 1px solid #2a2a3e;
  border-radius: 4px;
  font-size: 14px;
}

.bb-input:focus {
  outline: none;
  border-color: #5a9a7a;
}

.rank-info {
  font-size: 13px;
  color: #e88;
  font-weight: 500;
  padding: 6px 12px;
  background: rgba(238, 136, 136, 0.1);
  border-radius: 4px;
  border: 1px solid rgba(238, 136, 136, 0.2);
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
