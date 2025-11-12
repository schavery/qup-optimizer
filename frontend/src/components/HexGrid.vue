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
            @mouseenter="showTooltip($event, name, 'static')"
            @mouseleave="hideTooltip"
          />
          <text
            :x="cubeToPixel(node.position[0], node.position[1], node.position[2]).x"
            :y="cubeToPixel(node.position[0], node.position[1], node.position[2]).y"
            text-anchor="middle"
            dominant-baseline="middle"
            class="node-label node-label-static"
            @mouseenter="showTooltip($event, name, 'static')"
            @mouseleave="hideTooltip"
          >
            {{ name }}
          </text>
        </g>

        <!-- Movable nodes (rendered as circles) -->
        <g
          v-for="(pos, name) in movablePositions"
          :key="`movable-${name}`"
          :class="{ 'dragging': draggingNode === name }"
        >
          <circle
            :cx="cubeToPixel(pos[0], pos[1], pos[2]).x"
            :cy="cubeToPixel(pos[0], pos[1], pos[2]).y"
            :r="30"
            class="hex-movable-circle"
            @mousedown="startDrag($event, name)"
            @mouseenter="showTooltip($event, name, 'movable')"
            @mouseleave="hideTooltip"
          />
          <text
            :x="cubeToPixel(pos[0], pos[1], pos[2]).x"
            :y="cubeToPixel(pos[0], pos[1], pos[2]).y"
            text-anchor="middle"
            dominant-baseline="middle"
            class="node-label node-label-movable"
            @mousedown="startDrag($event, name)"
            @mouseenter="showTooltip($event, name, 'movable')"
            @mouseleave="hideTooltip"
          >
            {{ name }}
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

        <!-- Node order labels (rendered last so they're on top) -->
        <g v-for="hex in gridHexes" :key="`order-${hex.q},${hex.r},${hex.s}`">
          <text
            v-if="getNodeOrder(hex) !== null"
            :x="cubeToPixel(hex.q, hex.r, hex.s).x"
            :y="cubeToPixel(hex.q, hex.r, hex.s).y + 20"
            text-anchor="middle"
            class="node-order-label"
          >
            {{ getNodeOrder(hex) }}
          </text>
        </g>
      </g>
    </svg>

    <!-- Tooltip -->
    <div
      v-if="hoveredNode"
      class="node-tooltip"
      :style="{ left: tooltipPos.x + 'px', top: tooltipPos.y + 'px' }"
    >
      <div class="tooltip-header">{{ hoveredNode.name }}</div>
      <div class="tooltip-body">
        <div class="tooltip-row">
          <span class="tooltip-label">Type:</span>
          <span class="tooltip-value">{{ hoveredNode.effect_type }}</span>
        </div>
        <div class="tooltip-row">
          <span class="tooltip-label">Triggers:</span>
          <span class="tooltip-value">{{ hoveredNode.trigger_types.join(', ') }}</span>
        </div>
        <div class="tooltip-row">
          <span class="tooltip-label">AVS:</span>
          <span class="tooltip-value">{{ hoveredNode.base_avs }}</span>
        </div>
        <div v-if="hoveredNode.effect_params && Object.keys(hoveredNode.effect_params).length > 0" class="tooltip-description">
          {{ formatEffectDescription(hoveredNode.effect_type, hoveredNode.effect_params) }}
        </div>
      </div>
    </div>
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
    movableNodes: {
      type: Object,
      required: true
    },
    movablePositions: {
      type: Object,
      required: true
    },
    upgrades: {
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
      gridOrder: new Map(), // Maps position key to order index
      draggingNode: null,
      dragStartPos: null,
      dragOffset: { x: 0, y: 0 },
      highlightedNeighbors: [],
      zoom: 0.85,
      panX: 0,
      panY: 0,
      isPanning: false,
      panStartPos: null,
      hoveredNode: null,
      tooltipPos: { x: 0, y: 0 }
    }
  },
  mounted() {
    this.gridHexes = generateHexGrid(this.radius)
    this.generateGridOrder()
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

    generateGridOrder() {
      // Generate spiral order: center outward
      const positions = []

      // Start at center (0, 0, 0)
      positions.push({ q: 0, r: 0, s: 0 })

      // Generate spiral for each ring
      for (let ring = 1; ring <= this.radius; ring++) {
        // Start at top of ring
        let q = 0, r = -ring, s = ring

        // Traverse the 6 sides of the hexagon
        const directions = [
          [1, 0, -1],   // SE
          [0, 1, -1],   // S
          [-1, 1, 0],   // SW
          [-1, 0, 1],   // NW
          [0, -1, 1],   // N
          [1, -1, 0],   // NE
        ]

        for (const [dq, dr, ds] of directions) {
          for (let i = 0; i < ring; i++) {
            positions.push({ q, r, s })
            q += dq
            r += dr
            s += ds
          }
        }
      }

      // Create map from position to order
      this.gridOrder.clear()
      positions.forEach((pos, index) => {
        const key = `${pos.q},${pos.r},${pos.s}`
        this.gridOrder.set(key, index)
      })
    },

    getNodeOrder(hex) {
      // Return the grid position order (spiral from center)
      const key = `${hex.q},${hex.r},${hex.s}`
      return this.gridOrder.get(key) ?? null
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
      event.preventDefault()
      event.stopPropagation()
      this.draggingNode = nodeName

      // Store the starting position in case drag is cancelled
      this.dragStartPos = [...this.movablePositions[nodeName]]

      // Get mouse position relative to SVG
      const svg = event.target.ownerSVGElement
      const pt = svg.createSVGPoint()
      pt.x = event.clientX
      pt.y = event.clientY
      const svgP = pt.matrixTransform(svg.getScreenCTM().inverse())

      // Calculate offset from node center to mouse
      const nodePos = this.cubeToPixel(
        this.movablePositions[nodeName][0],
        this.movablePositions[nodeName][1],
        this.movablePositions[nodeName][2]
      )
      this.dragOffset = {
        x: svgP.x - nodePos.x,
        y: svgP.y - nodePos.y
      }
    },

    handleMouseMove(event) {
      if (!this.draggingNode) return

      event.preventDefault()

      try {
        // Get mouse position in SVG coordinates
        const svg = event.target.ownerSVGElement || event.target
        if (!svg || !svg.createSVGPoint) return

        const pt = svg.createSVGPoint()
        pt.x = event.clientX
        pt.y = event.clientY
        const svgP = pt.matrixTransform(svg.getScreenCTM().inverse())

        // Find closest hex to mouse position (accounting for zoom and pan)
        const mouseX = (svgP.x - this.svgWidth/2 - this.panX) / this.zoom
        const mouseY = (svgP.y - this.svgHeight/2 - this.panY) / this.zoom

        // Convert pixel to hex coordinates
        const closestHex = this.pixelToHex(mouseX, mouseY)

        // Only update if it's a valid, unoccupied position
        if (closestHex && !this.isOccupiedExcept(closestHex, this.draggingNode)) {
          const updated = { ...this.movablePositions }
          updated[this.draggingNode] = closestHex
          this.$emit('update:movablePositions', updated)
        }
      } catch (err) {
        console.error('Drag error:', err)
        // If there's an error, just end the drag
        this.handleMouseUp()
      }
    },

    handleMouseUp() {
      if (this.draggingNode) {
        // Check if current position is valid, if not restore original
        const currentPos = this.movablePositions[this.draggingNode]
        if (!currentPos || this.isOccupiedExcept(currentPos, this.draggingNode)) {
          // Restore to original position
          if (this.dragStartPos) {
            const updated = { ...this.movablePositions }
            updated[this.draggingNode] = this.dragStartPos
            this.$emit('update:movablePositions', updated)
          }
        }

        this.draggingNode = null
        this.dragOffset = { x: 0, y: 0 }
        this.dragStartPos = null
      }
    },

    handleHexClick(hex) {
      // Show neighbors on click
      const neighbors = getNeighbors(hex.q, hex.r, hex.s)
      this.highlightedNeighbors = neighbors.map(([q, r, s]) => ({ q, r, s }))

      setTimeout(() => {
        this.highlightedNeighbors = []
      }, 1500)
    },

    pixelToHex(x, y) {
      // Pointy-top orientation
      const HEX_SPACING = 35 * 1.8

      // Convert pixel to cube coordinates (inverse of cubeToPixel)
      const q = (2/3 * x) / HEX_SPACING
      const r = (-1/3 * x + Math.sqrt(3)/3 * y) / HEX_SPACING
      const s = -q - r

      // Round to nearest hex
      return this.cubeRound(q, r, s)
    },

    cubeRound(fq, fr, fs) {
      let q = Math.round(fq)
      let r = Math.round(fr)
      let s = Math.round(fs)

      const qDiff = Math.abs(q - fq)
      const rDiff = Math.abs(r - fr)
      const sDiff = Math.abs(s - fs)

      if (qDiff > rDiff && qDiff > sDiff) {
        q = -r - s
      } else if (rDiff > sDiff) {
        r = -q - s
      } else {
        s = -q - r
      }

      // Check if within grid bounds
      const distance = Math.max(Math.abs(q), Math.abs(r), Math.abs(s))
      if (distance > this.radius) {
        return null
      }

      return [q, r, s]
    },

    isOccupiedExcept(pos, exceptNode) {
      // Check static nodes
      for (const node of Object.values(this.staticNodes)) {
        if (positionEquals(node.position, pos)) return true
      }
      // Check movable nodes except the one being dragged
      for (const [nodeName, nodePos] of Object.entries(this.movablePositions)) {
        if (nodeName !== exceptNode && positionEquals(nodePos, pos)) return true
      }
      return false
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
    },

    showTooltip(event, nodeName, nodeType) {
      const node = nodeType === 'static' ? this.staticNodes[nodeName] : this.movableNodes[nodeName]
      if (!node) return

      // Calculate upgraded values
      const upgradeLevels = this.upgrades[nodeName] || []
      const upgradedAVS = this.calculateTotalAVS(node, upgradeLevels)
      const upgradedParams = this.calculateUpgradedParams(node, upgradeLevels)

      this.hoveredNode = {
        name: nodeName,
        ...node,
        base_avs: upgradedAVS,  // Override with upgraded AVS
        effect_params: upgradedParams  // Override with upgraded params
      }

      // Position tooltip near mouse
      const rect = this.$el.getBoundingClientRect()
      this.tooltipPos = {
        x: event.clientX - rect.left + 15,
        y: event.clientY - rect.top + 15
      }
    },

    hideTooltip() {
      this.hoveredNode = null
    },

    calculateTotalAVS(node, upgradeLevels) {
      if (node.base_avs === null || node.base_avs === undefined) return null

      let total = node.base_avs

      if (!node.upgrade_paths || !upgradeLevels) return total

      for (let pathIdx = 0; pathIdx < upgradeLevels.length; pathIdx++) {
        const level = upgradeLevels[pathIdx]
        if (pathIdx >= node.upgrade_paths.length) continue

        const path = node.upgrade_paths[pathIdx]
        for (let stepIdx = 0; stepIdx < level; stepIdx++) {
          if (stepIdx < path.length && path[stepIdx].avs_increase) {
            total += path[stepIdx].avs_increase
          }
        }
      }

      return total
    },

    calculateUpgradedParams(node, upgradeLevels) {
      // Start with base effect params
      const params = { ...node.effect_params }

      if (!node.upgrade_paths || !upgradeLevels) return params

      // Apply each upgrade path's modifications
      for (let pathIdx = 0; pathIdx < upgradeLevels.length; pathIdx++) {
        const level = upgradeLevels[pathIdx]
        if (pathIdx >= node.upgrade_paths.length) continue

        const path = node.upgrade_paths[pathIdx]
        for (let stepIdx = 0; stepIdx < level; stepIdx++) {
          if (stepIdx >= path.length) continue

          const step = path[stepIdx]

          // Apply various upgrade types
          if (step.base_reduction_increase) {
            params.base_reduction = (params.base_reduction || 0) + step.base_reduction_increase
          }
          if (step.bb_multiplier_increase) {
            params.bb_multiplier = (params.bb_multiplier || 0) + step.bb_multiplier_increase
          }
          if (step.base_amount_increase) {
            params.base_amount = (params.base_amount || 0) + step.base_amount_increase
          }
          if (step.q_per_bb_increase) {
            params.q_per_bb = (params.q_per_bb || 0) + step.q_per_bb_increase
          }
          if (step.base_per_loss_increase) {
            params.base_per_loss = (params.base_per_loss || 0) + step.base_per_loss_increase
          }
          if (step.bb_increase) {
            params.bb_increase = (params.bb_increase || 0) + step.bb_increase
          }
          if (step.num_triggers_increase) {
            params.num_triggers = (params.num_triggers || 0) + step.num_triggers_increase
          }
          if (step.nodes_per_loss_increase) {
            params.nodes_per_loss = (params.nodes_per_loss || 0) + step.nodes_per_loss_increase
          }
          if (step.base_per_teammate_increase) {
            params.base_per_teammate = (params.base_per_teammate || 0) + step.base_per_teammate_increase
          }
          if (step.effect_mult) {
            // For multiplier effects, we multiply the effect
            if (params.base_reduction) params.base_reduction *= step.effect_mult
            if (params.bb_multiplier) params.bb_multiplier *= step.effect_mult
            if (params.base_amount) params.base_amount *= step.effect_mult
            if (params.q_per_bb) params.q_per_bb *= step.effect_mult
          }
          // Add depleted_reduction_percent if specified
          if (step.depleted_reduction_percent !== undefined) {
            params.depleted_reduction_percent = step.depleted_reduction_percent
          }
          // Handle base_percent_increase
          if (step.base_percent_increase) {
            params.base_percent = (params.base_percent || 0) + step.base_percent_increase
          }
        }
      }

      return params
    },

    formatEffectDescription(effectType, params) {
      // Format effect description based on effect type
      switch (effectType) {
        case 'trigger_adjacent':
          return 'Triggers all adjacent nodes'
        case 'trigger_most_avs':
          return `Triggers ${params.num_triggers || 1} node(s) with highest AVS`
        case 'trigger_adjacent_most_avs':
          return `Triggers ${params.num_triggers || 1} adjacent node(s) with most AVS`
        case 'trigger_random_adjacent':
          return 'Triggers 1 random adjacent node'
        case 'trigger_adjacent_per_loss':
          return `Triggers ${params.nodes_per_loss || 2} adjacent nodes per loss`
        case 'add_bb_and_trigger':
          return `Adds BB, triggers ${params.bb_threshold_1 ? '1-2' : '1'} adjacent based on BB`
        case 'q_per_qdown_prevented':
          return 'Gains Q for each Qdown prevented'
        case 'flat_q':
          return `Flat ${params.base_amount || 0} Q per trigger`
        case 'flat_q_per_bb':
          return `${params.q_per_bb || 0} Q per Battle Bonus`
        case 'reduce_qdown':
          return `Reduces Qdown by ${params.base_reduction || 0} + ${params.bb_multiplier || 0} × BB`
        case 'reduce_qdown_percent':
          return `Reduces Qdown by ${(params.base_percent * 100).toFixed(0)}%`
        case 'reduce_qdown_per_loss':
          return `Reduces Qdown by ${params.base_per_loss || 0} per loss`
        case 'add_to_qmult':
          return 'Adds Battle Bonus to Qmult'
        case 'add_bb':
          return `Adds ${params.bb_increase || 1} Battle Bonus`
        case 'defence_per_bb':
          return 'Grants defence based on Battle Bonus'
        case 'gold_per_qdown_prevented':
          return `Earns ${params.qdown_per_gold || 0} gold per Qdown prevented`
        case 'flat_q_per_teammate_class':
          return `${params.base_per_teammate || 0} Q per ${params.teammate_class || 'teammate'}`
        default:
          return Object.entries(params).map(([k, v]) => `${k}: ${v}`).join(', ')
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

/* Circle styling for movable nodes */
.hex-movable-circle {
  fill: #3a7a5a;
  stroke: #5a9a7a;
  stroke-width: 2;
  cursor: move;
  transition: all 0.2s;
}

.hex-movable-circle:hover {
  fill: #4a8a6a;
  stroke: #6aaa8a;
  stroke-width: 2.5;
}

.dragging .hex-movable-circle {
  opacity: 0.7;
  stroke: #7aba9a;
  stroke-width: 3;
  filter: drop-shadow(0 0 8px rgba(90, 154, 122, 0.6));
}

.hex-neighbor {
  fill: rgba(255, 200, 100, 0.2);
  stroke: rgba(255, 200, 100, 0.5);
  stroke-width: 2;
  pointer-events: none;
}

.node-label {
  font-size: 10px;
  font-weight: 600;
  user-select: none;
  text-shadow: 0 0 3px rgba(0, 0, 0, 0.8), 0 0 5px rgba(0, 0, 0, 0.6);
}

.node-label-static {
  fill: #eee;
  pointer-events: none;
}

.node-label-movable {
  fill: #ddd;
  cursor: pointer;
  pointer-events: all;
}

.node-label-movable:hover {
  fill: #fff;
}

/* Node order label */
.node-order-label {
  font-size: 8px;
  font-weight: 700;
  fill: #999;
  pointer-events: none;
  user-select: none;
  text-shadow: 0 0 2px rgba(0, 0, 0, 0.8);
  opacity: 0.7;
}

.hex-ring-0 { stroke: #4a4a6e; }
.hex-ring-1 { stroke: #3a3a5e; }
.hex-ring-2 { stroke: #2a2a4e; }

/* Tooltip styles */
.node-tooltip {
  position: absolute;
  background: rgba(20, 20, 35, 0.98);
  border: 2px solid #5a9a7a;
  border-radius: 8px;
  padding: 12px;
  color: #eee;
  font-size: 13px;
  pointer-events: none;
  z-index: 1000;
  min-width: 220px;
  max-width: 350px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.6), 0 0 20px rgba(90, 154, 122, 0.3);
  backdrop-filter: blur(4px);
}

.tooltip-header {
  font-size: 15px;
  font-weight: 700;
  color: #7aba9a;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid #3a3a5e;
}

.tooltip-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tooltip-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.tooltip-label {
  color: #aaa;
  font-weight: 500;
  font-size: 12px;
}

.tooltip-value {
  color: #ddd;
  font-weight: 600;
  text-align: right;
}

.tooltip-description {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #2a2a4e;
  color: #bbb;
  font-size: 12px;
  line-height: 1.4;
  font-style: italic;
}
</style>
