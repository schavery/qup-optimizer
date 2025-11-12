// frontend/src/utils/hexMath.js
// Hex coordinate math utilities

export const HEX_SIZE = 35
export const HEX_SPACING = HEX_SIZE * 1.8

// Convert cube coordinates (q, r, s) to pixel coordinates
// Rotated 60 degrees left so (0, -1, 1) points north
export function cubeToPixel(q, r, s) {
  // Original pointy-top orientation rotated 60 degrees CCW
  const x = HEX_SPACING * (Math.sqrt(3) * q + Math.sqrt(3)/2 * r)
  const y = HEX_SPACING * (3/2 * r)
  return { x, y }
}

// Convert pixel coordinates to cube coordinates (approximate)
export function pixelToCube(x, y) {
  const q = Math.round((2/3 * x) / HEX_SPACING)
  const r = Math.round((-1/3 * x + Math.sqrt(3)/3 * y) / HEX_SPACING)
  const s = -q - r
  return { q, r, s }
}

// Get distance from center
export function cubeDistance(q, r, s) {
  return Math.max(Math.abs(q), Math.abs(r), Math.abs(s))
}

// Get all neighbors of a hex
export function getNeighbors(q, r, s) {
  return [
    [q + 1, r - 1, s],
    [q + 1, r, s - 1],
    [q, r + 1, s - 1],
    [q - 1, r + 1, s],
    [q - 1, r, s + 1],
    [q, r - 1, s + 1]
  ]
}

// Generate all hexes in a radius
export function generateHexGrid(radius) {
  const hexes = []
  for (let q = -radius; q <= radius; q++) {
    for (let r = -radius; r <= radius; r++) {
      const s = -q - r
      if (Math.abs(s) <= radius) {
        hexes.push({ q, r, s })
      }
    }
  }
  return hexes
}

// SVG path for a hexagon
export function hexagonPath(cx, cy, size) {
  const points = []
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 3) * i - Math.PI / 2
    const x = cx + size * Math.cos(angle)
    const y = cy + size * Math.sin(angle)
    points.push(`${x},${y}`)
  }
  return `M ${points.join(' L ')} Z`
}

// Check if two positions are the same
export function positionEquals(pos1, pos2) {
  if (!pos1 || !pos2) return false
  return pos1[0] === pos2[0] && pos1[1] === pos2[1] && pos1[2] === pos2[2]
}

// Convert position array to key string
export function positionKey(pos) {
  return `${pos[0]},${pos[1]},${pos[2]}`
}
