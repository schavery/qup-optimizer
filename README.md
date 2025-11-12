# Qup Skill Tree Optimizer

A comprehensive optimization system for finding optimal skill tree configurations for high-rank play in Qup, where massive Qdown penalties (-700K+ at Grandmaster 1) make strategic positioning and upgrade choices critical.

## Quick Start

### Web Interface (Recommended)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..

# Start the web server
python app.py
```

Then open http://localhost:5000 in your browser for an interactive hex grid editor with real-time simulation.

### Command Line Interface

```bash
# Basic position optimization
python -m optimizer.main --candidates 20 --rank 31 --top 5

# Upgrade point optimization (18 points)
python -m optimizer.optimize_upgrades --budget 18 --top 5

# Debug trigger efficiency
python debug_panic_efficiency.py
```

## Problem Statement

At Grandmaster ranks (31+):
- **Qdown on loss**: -700,000 Q (rank 31), scaling exponentially
- **Only 14 movable nodes** to place on 210+ available positions
- **18 upgrade points** to spend across 7 static nodes
- **Goal**: Maximize worst-case Q to survive all match outcomes

## Key Mechanics

### Node Types
- **Static Nodes (7)**: Fixed positions, have upgrade paths (Panic, EMT, Triage, etc.)
- **Movable Nodes (14)**: Flexible positioning (Angel, Focus, Surgeon, etc.)

### Trigger Cascades
- **Panic**: Triggers ALL adjacent nodes (cascade engine)
- **AVS (Activation Stock)**: Limits triggers per flip, resets each flip
- **Trigger chains**: Panic → Focus → Panic → Stimulant → ... until AVS depleted
- **Best observed**: 59 triggers in a single flip!

### Critical Strategy
1. **Position trigger nodes adjacent to Panic** for feedback loops
2. **Place Angel in outer rings** to trigger last (captures all Qdown prevention)
3. **Balance Panic AVS vs adjacent node AVS** to minimize wasted triggers

## Architecture

### Core Components

```
optimizer/
├── adjacency_generator.py    # Smart position generation (Panic clusters)
├── candidate_generator.py    # Basic position generation
├── upgrade_generator.py      # Upgrade configuration generation
├── evaluator.py              # Simulate & score layouts
├── visualizer.py             # Display results (hex grids, Q spectra)
├── main.py                   # Position optimization CLI
└── optimize_upgrades.py      # Upgrade optimization CLI
```

### Core System

```
core/
├── game_state.py        # Game state (Q, BB, qmult, triggers)
├── node.py              # Node definitions & instances
├── hex_grid.py          # Hex coordinate system
└── layout.py            # Grid layout configuration

simulator.py             # Core game simulation engine
effects/executor.py      # Effect handlers (Qdown, triggers, etc.)
data/nodes.py           # All node definitions (static + movable)
```

## Features

### 0. Web Interface

**Interactive hex grid visualization with real-time simulation**
- **Drag & drop** movable nodes to any hex position
- **Upgrade sliders** for all static nodes with live point tracking
- **Real-time evaluation** shows Q outcomes as you make changes
- **Visual adjacency** highlights to understand trigger cascades
- **Hex grid rendering** using SVG with proper cube coordinates
- **Results panel** with outcome spectrum, trigger metrics, and efficiency

**API Endpoints**:
- `GET /api/nodes` - All node definitions
- `POST /api/evaluate` - Evaluate a layout configuration
- `POST /api/generate-layouts` - Generate optimized candidate layouts
- `POST /api/generate-upgrades` - Generate upgrade configurations
- `GET /api/outcomes` - All possible round outcome sequences

**Tech Stack**: Flask + Vue.js 3 + Vite

### 1. Adjacency-Aware Position Optimization

**Strategy**: Build trigger clusters around Panic
- Places trigger nodes (Focus, Low Point, Stimulant, etc.) adjacent to Panic
- Positions Angel in outer rings (5-8) to trigger last
- Maximizes feedback loop potential

**Usage**:
```bash
python -m optimizer.main --candidates 100 --rank 31 --top 10 --detailed 3
```

**Output**:
- Top N layouts ranked by: worst-case Q → efficiency → adjacency score
- Hex grid visualization showing node positions
- Complete Q spectrum for all 20 round outcomes (WWW, WWLLL, etc.)
- Trigger counts and efficiency metrics

### 2. Upgrade Point Optimization

**Strategy**: Find best way to spend upgrade points
- Tests 100+ upgrade configurations
- For each config, evaluates 3-5 position layouts
- Ranks by worst-case Q and trigger efficiency

**Usage**:
```bash
python -m optimizer.optimize_upgrades --budget 18 --rank 31 --top 5 --strategy tiered
```

**Key Findings** (18 points):
- **Panic [6,0]**: Always in top configs (6 points = 7 AVS total)
- **EMT [3,3]**: Full BB scaling crucial (6 points)
- **Stop the Bleeding [3,0]**: Flat Qdown reduction (3 points)
- **BUT**: 45-52% of triggers wasted on depleted nodes!

### 3. Trigger Efficiency Tracking

**Innovation**: Measures wasted triggers on depleted nodes

**Metrics**:
- `total_triggers`: Successful node triggers
- `depleted_triggers`: Attempts that hit depleted nodes (wasted)
- `efficiency`: `total / (total + depleted)`

**Key Insight**: Maxing Panic creates massive cascades but wastes 50%+ of late-game triggers because adjacent nodes run out of AVS within the same flip.

**Debug Tool**:
```bash
python debug_panic_efficiency.py
```

Shows exact sequence of Panic triggers and which adjacent nodes are depleted.

### 4. Simulation Engine

**Features**:
- Simulates all 20 possible round outcomes (best-of-5)
- Handles recursive trigger cascades with AVS checking
- Tracks: Q currency, qmult, battle bonus, triggers, efficiency
- Proper trigger order: spiral outward from center

**Example Flow** (single loss flip):
1. Reset all node AVS counters
2. Set `q_this_flip = -700,000` (base Qdown)
3. Trigger "flip" nodes (spiral order)
4. Trigger "loss" nodes (spiral order)
   - Angel of Death: `qmult *= 3`
   - Panic: Triggers all 5-6 adjacent nodes
   - Those nodes trigger Panic back → cascade
5. Apply qmult: `q_currency += q_this_flip * qmult`

## Results at Grandmaster 1 (Rank 31)

### Best Configuration Found
**Upgrades** (18 points):
```
Panic: [6,0] → 7 AVS
EMT: [3,3] → 8 AVS, full BB scaling
Stop the Bleeding: [3,0] → +35K Qdown reduction/loss
Battle Medic: [0,2] → 2x then 3x qmult multiplier
Triage: [2,0] → 4% Qdown reduction
```

**Position Layout**: All trigger nodes adjacent to Panic

**Performance**:
- **Min Q**: -3.6M (LLL worst case)
- **Max Q**: +621K (WWW best case)
- **Triggers**: 35-50 per flip (up from 4-9 without optimization)
- **Efficiency**: 48.6% (51.4% wasted on depleted nodes)

### Key Tradeoffs

| Metric | High Panic AVS (6-7) | Low Panic AVS (3-4) |
|--------|---------------------|---------------------|
| Total Triggers | 35-50 per flip | 20-30 per flip |
| Efficiency | 45-52% | 60-75% |
| Q Outcomes | Better (more cascades) | Worse (fewer cascades) |
| Wasted Triggers | High (50%+) | Low (25-40%) |

**Recommendation**: Current meta favors maxing Panic despite waste, but efficiency tracking reveals the hidden cost.

## File Reference

### Debug/Test Scripts
- `debug_panic_efficiency.py` - Analyze Panic trigger efficiency
- `debug_single_flip.py` - Detailed single-flip logging
- `test_triggers.py` - Test trigger clustering

### Data Files
- `data/nodes.py` - All node definitions (NODES + MOVABLE_NODES)
- `rank_notes.txt` - Rank progression notes

## Advanced Usage

### Generate More Candidates
```bash
# Test 500 layouts with 10 detailed results
python -m optimizer.main --candidates 500 --top 20 --detailed 10
```

### Test Specific Upgrades
```bash
# Manual upgrade config via JSON
python -m optimizer.main --upgrades '{"Panic": [6,0], "EMT": [3,3]}' --candidates 50
```

### Exhaustive Upgrade Search
```bash
# Generate ALL valid configs (slow but comprehensive)
python -m optimizer.optimize_upgrades --budget 18 --strategy exhaustive
```

## Technical Notes

### Hex Grid Coordinates
- Uses cube coordinates: `(q, r, s)` where `q + r + s = 0`
- Distance from center: `max(|q|, |r|, |s|)`
- Spiral order: Center outward, determines trigger priority

### Trigger Order Within Flip
1. Type priority: "flip" nodes first, then "win" or "loss"
2. Spatial order: Spiral from center outward
3. Cascade order: Depth-first recursion with AVS checking

### AVS Reset Behavior
**Critical**: AVS resets EVERY flip, not per round
- Panic with 7 AVS can trigger 7 times PER FLIP
- Adjacent nodes also reset each flip
- Efficiency waste happens WITHIN a single flip

## Future Improvements

1. **Balanced Upgrade Strategy**: Upgrade Panic + adjacent nodes together
2. **Dynamic Position Generation**: Adjust positions based on upgrade config
3. **Multi-Objective Optimization**: Pareto frontier of Q vs efficiency
4. **Genetic Algorithm**: Evolve layouts over generations
5. **Adjacent Node AVS Optimization**: Ensure Panic's targets can handle all triggers

## Credits

Built to optimize skill tree for Grandmaster rank progression in Qup.

Core insight: Position matters more than raw stats. A well-clustered grid with moderate upgrades outperforms scattered nodes with max upgrades.
