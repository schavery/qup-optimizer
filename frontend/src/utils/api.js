// frontend/src/utils/api.js
import axios from 'axios'

const API_BASE = import.meta.env.PROD ? '/api' : 'http://localhost:5001/api'

export const api = {
  async getNodes() {
    const response = await axios.get(`${API_BASE}/nodes`)
    return response.data
  },

  async evaluateLayout(layout, upgrades, rank, initialBB = 0) {
    const response = await axios.post(`${API_BASE}/evaluate`, {
      layout,
      upgrades,
      rank,
      initial_bb: initialBB
    })
    return response.data
  },

  async generateLayouts(count, rank, seed, upgrades) {
    const response = await axios.post(`${API_BASE}/generate-layouts`, {
      count,
      rank,
      seed,
      upgrades
    })
    return response.data
  },

  async generateUpgrades(budget, strategy) {
    const response = await axios.post(`${API_BASE}/generate-upgrades`, {
      budget,
      strategy
    })
    return response.data
  },

  async getOutcomes() {
    const response = await axios.get(`${API_BASE}/outcomes`)
    return response.data
  },

  async getRanks() {
    const response = await axios.get(`${API_BASE}/ranks`)
    return response.data
  },

  async getRank(rank) {
    const response = await axios.get(`${API_BASE}/rank/${rank}`)
    return response.data
  }
}
