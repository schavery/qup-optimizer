<template>
  <div class="hex-grid-container">
    <div class="zoom-controls">
      <button @click="zoomIn" class="zoom-btn" title="Zoom In">+</button>
      <button @click="zoomOut" class="zoom-btn" title="Zoom Out">−</button>
      <button @click="resetZoom" class="zoom-btn" title="Reset Zoom">⟲</button>
      <span class="zoom-level">{{ Math.round(zoom * 100) }}%</span>
    </div>
    <svg
      :width="svgWidth"
      :height="svgHeight"
      @mouseup="handleMouseUp"
      @mousemove="handleMouseMove"
      @mouseleave="handleMouseUp"
      @wheel="handleWheel"
    >
      <g :transform="`translate(${svgWidth/2 + panX}, ${svgHeight/2 + panY}) scale(${zoom})`">
        <!-- Grid hexes (background) -->
        <g v-for="hex in gridHexes" :key="`grid-${hex.q},${hex.r},${hex.s}`">
          <path
            :d="getHexPath(hex)"
            :class="getHexClass(hex)"
            @click="handleHexClick(hex)"
          />
        </g>

        <!-- Static nodes (fixed positions) -->
        <g v-for="(node, name) in staticNodes" :key="`static-${name}`">
          <path
            :d="getHexPath({q: node.position[0], r: node.position[1], s: node.position[2]})"
            class="hex-static"
          />
          <text
            :x="cubeToPixel(node.position[0], node.position[1], node.position[2]).x"
            :y="cubeToPixel(node.position[0], node.position[1], node.position[2]).y"
            text-anchor="middle"
            dominant-baseline="middle"
            class="node-label node-label-static"
          >
            {{ abbreviate(name) }}
          </text>
        </g>

        <!-- Movable nodes -->
        <g
          v-for="(pos, name) in movablePositions"
          :key="`movable-${name}`"
          :class="{ 'dragging': draggingNode === name }"
          @mousedown="startDrag($event, name)"
        >
          <path
            :d="getHexPath({q: pos[0], r: pos[1], s: pos[2]})"
            class="hex-movable"
            :style="draggingNode === name ? `transform: translate(${dragOffset.x}px, ${dragOffset.y}px)` : ''"
          />
          <text
            :x="cubeToPixel(pos[0], pos[1], pos[2]).x + (draggingNode === name ? dragOffset.x : 0)"
            :y="cubeToPixel(pos[0], pos[1], pos[2]).y + (draggingNode === name ? dragOffset.y : 0)"
            text-anchor="middle"
            dominant-baseline="middle"
            class="node-label node-label-movable"
          >
            {{ abbreviate(name) }}
          </text>
        </g>

        <!-- Adjacency highlights -->
        <g v-if="highlightedNeighbors.length > 0">
          <path
            v-for="(neighbor, idx) in highlightedNeighbors"
            :key="`neighbor-${idx}`"
            :d="getHexPath(neighbor)"
            class="hex-neighbor"
          />
        </g>
      </g>
    </svg>
  </div>
</template>

<script>
import { cubeToPixel, hexagonPath, getNeighbors, generateHexGrid, positionEquals, positionKey } from '../utils/hexMath'

export default {
  props: {
    staticNodes: {
      type: Object,
      required: true
    },
    movablePositions: {
      type: Object,
      required: true
    },
    radius: {
      type: Number,
      default: 8
    }
  },
  emits: ['update:movablePositions'],
  data() {
    return {
      svgWidth: 800,
      svgHeight: 700,
      gridHexes: [],
      draggingNode: null,
      dragStartPos: null,
      dragOffset: { x: 0, y: 0 },
      highlightedNeighbors: [],
      zoom: 0.85,
      panX: 0,
      panY: 0,
      isPanning: false,
      panStartPos: null
    }
  },
  mounted() {
    this.gridHexes = generateHexGrid(this.radius)
    this.updateSvgSize()
    window.addEventListener('resize', this.updateSvgSize)
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.updateSvgSize)
  },
  methods: {
    cubeToPixel,

    getHexPath(hex) {
      const { x, y } = cubeToPixel(hex.q, hex.r, hex.s)
      return hexagonPath(x, y, 35)
    },

    getHexClass(hex) {
      const pos = [hex.q, hex.r, hex.s]
      const occupied = this.isOccupied(pos)
      const distance = Math.max(Math.abs(hex.q), Math.abs(hex.r), Math.abs(hex.s))

      return {
        'hex-grid': true,
        'hex-occupied': occupied,
        [`hex-ring-${distance}`]: true
      }
    },

    isOccupied(pos) {
      // Check static nodes
      for (const node of Object.values(this.staticNodes)) {
        if (positionEquals(node.position, pos)) return true
      }
      // Check movable nodes
      for (const nodePos of Object.values(this.movablePositions)) {
        if (positionEquals(nodePos, pos)) return true
      }
      return false
    },

    abbreviate(name) {
      // Abbreviate node names for display
      const abbrevs = {
        'Battle Medic': 'BM',
        'EMT': 'EMT',
        'Self Diagnosis': 'SD',
        'Stop the Bleeding': 'StB',
        'Panic': 'PAN',
        'Triage': 'TRI',
        'Big Sister': 'BS',
        'Angel': 'ANG',
        'Exhilaration': 'EXH',
        'Surgeon': 'SUR',
        'Adrenaline': 'ADR',
        'Focus': 'FOC',
        'Stimulant': 'STM',
        'Heroine': 'HER',
        'Funeral Rites': 'FR',
        'Extra Dose': 'ED',
        'Angel of Death': 'AoD',
        'Low Point': 'LP',
        'Deployment': 'DEP',
        'Insurance Scam': 'IS',
        'Battle Hardened': 'BH'
      }
      return abbrevs[name] || name.substring(0, 3).toUpperCase()
    },

    startDrag(event, nodeName) {
      this.draggingNode = nodeName
      this.dragStartPos = { x: event.clientX, y: event.clientY }
      this.dragOffset = { x: 0, y: 0 }
    },

    handleMouseMove(event) {
      if (!this.draggingNode) return

      this.dragOffset = {
        x: event.clientX - this.dragStartPos.x,
        y: event.clientY - this.dragStartPos.y
      }
    },

    handleMouseUp() {
      if (!this.draggingNode) return

      // Find nearest hex to drop position
      const svgRect = event.currentTarget.getBoundingClientRect()
      // TODO: Convert mouse position to hex coordinates and update position

      this.draggingNode = null
      this.dragOffset = { x: 0, y: 0 }
    },

    handleHexClick(hex) {
      const pos = [hex.q, hex.r, hex.s]

      // If dragging, drop here
      if (this.draggingNode) {
        if (!this.isOccupied(pos)) {
          const updated = { ...this.movablePositions }
          updated[this.draggingNode] = pos
          this.$emit('update:movablePositions', updated)
        }
        this.draggingNode = null
        this.dragOffset = { x: 0, y: 0 }
        return
      }

      // Show neighbors
      const neighbors = getNeighbors(hex.q, hex.r, hex.s)
      this.highlightedNeighbors = neighbors.map(([q, r, s]) => ({ q, r, s }))

      setTimeout(() => {
        this.highlightedNeighbors = []
      }, 1500)
    },

    handleWheel(event) {
      event.preventDefault()
      const delta = event.deltaY > 0 ? -0.1 : 0.1
      this.zoom = Math.max(0.3, Math.min(3.0, this.zoom + delta))
    },

    zoomIn() {
      this.zoom = Math.min(3.0, this.zoom + 0.2)
    },

    zoomOut() {
      this.zoom = Math.max(0.3, this.zoom - 0.2)
    },

    resetZoom() {
      this.zoom = 0.85
      this.panX = 0
      this.panY = 0
    },

    updateSvgSize() {
      const container = this.$el
      if (container) {
        this.svgWidth = container.clientWidth
        this.svgHeight = container.clientHeight
      }
    }
  }
}
</script>

<style scoped>
.hex-grid-container {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #0f0f1e;
  border-radius: 8px;
  position: relative;
}

.zoom-controls {
  position: absolute;
  top: 15px;
  right: 15px;
  display: flex;
  gap: 8px;
  align-items: center;
  z-index: 10;
  background: rgba(26, 26, 46, 0.9);
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid #2a2a3e;
}

.zoom-btn {
  width: 32px;
  height: 32px;
  padding: 0;
  background: #2a2a4e;
  color: #eee;
  border: 1px solid #3a3a5e;
  border-radius: 4px;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.zoom-btn:hover {
  background: #3a3a5e;
  border-color: #4a4a6e;
}

.zoom-btn:active {
  transform: scale(0.95);
}

.zoom-level {
  font-size: 13px;
  color: #aaa;
  min-width: 50px;
  text-align: center;
  font-weight: 500;
}

svg {
  cursor: crosshair;
}

.hex-grid {
  fill: #1a1a2e;
  stroke: #2a2a3e;
  stroke-width: 1;
  transition: fill 0.2s;
}

.hex-grid:hover {
  fill: #252538;
}

.hex-occupied {
  fill: #2a2a3e;
}

.hex-static {
  fill: #4a4a6e;
  stroke: #6a6a8e;
  stroke-width: 2;
  cursor: default;
}

.hex-movable {
  fill: #3a7a5a;
  stroke: #5a9a7a;
  stroke-width: 2;
  cursor: move;
  transition: transform 0.1s;
}

.hex-movable:hover {
  fill: #4a8a6a;
}

.dragging .hex-movable {
  opacity: 0.7;
  stroke: #7aba9a;
  stroke-width: 3;
}

.hex-neighbor {
  fill: rgba(255, 200, 100, 0.2);
  stroke: rgba(255, 200, 100, 0.5);
  stroke-width: 2;
  pointer-events: none;
}

.node-label {
  font-size: 11px;
  font-weight: bold;
  pointer-events: none;
  user-select: none;
}

.node-label-static {
  fill: #eee;
}

.node-label-movable {
  fill: #ddd;
}

.hex-ring-0 { stroke: #4a4a6e; }
.hex-ring-1 { stroke: #3a3a5e; }
.hex-ring-2 { stroke: #2a2a4e; }
</style>
