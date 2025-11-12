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

# Start the web server (runs on port 5001)
python app.py
```

Then open **http://localhost:5001** in your browser for an interactive hex grid editor with real-time simulation.

For development with hot-reload:
```bash
# Terminal 1: Start Flask backend
python app.py

# Terminal 2: Start Vite dev server
cd frontend
npm run dev
# Open http://localhost:3000
```

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

### Backend (Python)

```
optimizer/
├── adjacency_generator.py    # Smart position generation (Panic clusters + Angel)
├── candidate_generator.py    # Basic position generation (ring-based)
├── upgrade_generator.py      # Upgrade configuration generation
├── evaluator.py              # Simulate & score layouts (with caching)
├── local_search.py           # NEW: Iterative refinement via local search
├── layout_ops.py             # NEW: Layout manipulation utilities (swap, rotate)
├── visualizer.py             # Display results (hex grids, Q spectra)
├── main.py                   # Position optimization CLI (with refinement)
└── optimize_upgrades.py      # Upgrade optimization CLI

core/
├── game_state.py        # Game state (Q, BB, qmult, triggers, xp, gold)
├── node.py              # Node definitions & instances
├── hex_grid.py          # Hex coordinate system
└── layout.py            # Grid layout configuration

data/
├── nodes.py            # All node definitions (static + movable)
└── ranks.py            # Complete rank progression (40 ranks)

api/
├── routes.py           # Flask REST API endpoints
└── serializers.py      # JSON serialization helpers

simulator.py            # Core game simulation engine
effects/executor.py     # Effect handlers (Qdown, triggers, etc.)
app.py                  # Flask application (port 5001)
requirements.txt        # Python dependencies
```

### Frontend (Vue.js 3)

```
frontend/
├── index.html          # HTML entry point
├── vite.config.js      # Vite build configuration
├── package.json        # npm dependencies
└── src/
    ├── main.js         # Vue app initialization
    ├── App.vue         # Root component with state management
    ├── components/
    │   ├── HexGrid.vue       # SVG hex grid with zoom/click-to-place
    │   ├── UpgradePanel.vue  # Upgrade sliders + optimizer UI
    │   └── ResultsPanel.vue  # Simulation results visualization
    └── utils/
        ├── api.js            # API client wrapper (axios)
        └── hexMath.js        # Hex coordinate math (cube coords)
```

## Features

### 0. Web Interface

**Interactive hex grid visualization with real-time simulation**

**Key Features:**
- **Click-to-place nodes**: Click a movable node, then click a hex to place it
- **Full node names**: No abbreviations - see complete names on the grid
- **Upgrade optimizer**: Click "Optimize" → "Generate Top 5" to see best upgrade configs
- **Initial BB input**: Set your starting battle bonus (persists across games)
- **Rank selector**: Choose from 40 ranks (Bronze 1 → Legend 5)
- **Live Qdown display**: See penalty for current rank in header
- **Randomize layout**: Generate optimized position layouts with one click
- **Zoom controls**: Mouse wheel or +/- buttons to zoom in/out
- **60° rotated grid**: Node order 1 (Battle Medic) points north

**Interactive Controls:**
- **Upgrade sliders**: Adjust upgrade points for each static node (18 point budget)
- **Real-time evaluation**: Results update automatically after changes (500ms debounce)
- **Visual adjacency**: Click hexes to highlight neighbors (shows trigger relationships)
- **Results panel**: Q outcome spectrum for all 20 round outcomes, trigger metrics, efficiency

**API Endpoints**:
- `GET /api/nodes` - All node definitions (static + movable)
- `POST /api/evaluate` - Evaluate layout with upgrades, rank, and initial BB
- `POST /api/generate-layouts` - Generate optimized candidate layouts
- `POST /api/generate-upgrades` - Generate upgrade configurations (tiered or exhaustive)
- `GET /api/outcomes` - All possible round outcome sequences
- `GET /api/ranks` - Complete rank progression data (1-40)
- `GET /api/rank/<rank>` - Specific rank rewards and penalties

**Tech Stack**: Flask + Vue.js 3 + Vite + SVG hex rendering

**Port Configuration**: Runs on port 5001 (avoid macOS AirPlay Receiver conflict)

### 1. Iterative Position Refinement with Local Search

**NEW**: Intelligent layout improvement through iterative refinement!

**Strategy**: Two-phase optimization
1. **Broad exploration**: Generate 100 random layouts with Panic clustering
2. **Local refinement**: Improve top 10 diverse candidates using local search

**Domain-aware refinement operations**:
- **Node swaps**: Move trigger nodes to optimize cluster configuration
- **Cluster rotation**: Rotate groups of nodes around Panic (60° increments)
- **Angel positioning**: Move Angel into/out of trigger cluster dynamically

**Key insights**:
- **Angel in trigger cluster**: High variance - loses more in worst case but **massively positive on average** (18/20 positive outcomes, avg +43.7M Q)
- **Angel in outer rings**: Low variance - safer worst case but negative average (-574K avg Q, 1/20 positive)
- **Evaluation caching**: 60-72% cache hit rate reduces redundant simulations

**Usage**:
```bash
# With refinement (default)
python -m optimizer.main --candidates 100 --refine-count 10 --top 10 --detailed 3

# Without refinement (old behavior)
python -m optimizer.main --no-refine --candidates 100

# More aggressive refinement
python -m optimizer.main --refine-count 20 --refine-iterations 100 --verbose-refine
```

**Output**:
- Top N layouts ranked by: worst-case Q → efficiency → adjacency score → avg Q
- Hex grid visualization showing node positions
- Complete Q spectrum for all 20 round outcomes (WWW, WWLLL, etc.)
- Trigger counts and efficiency metrics
- Cache statistics (hit rate, total evaluations)
- Per-candidate improvement tracking

**Performance**:
- Typical improvements: **+3M to +320M** min_q per refined candidate
- Cache efficiency: 60-72% hit rate (7,000+ cache hits / 10,000+ evaluations)
- Refinement time: ~10-30 seconds for 10 candidates × 50 iterations

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

### 4. Comprehensive Rank System

**40 Ranks Across 8 Tiers**:
- Bronze (1-5): -100 to -200 Qdown
- Silver (6-10): -500 to -1,200 Qdown
- Gold (11-15): -2,750 to -7,500 Qdown
- Platinum (16-20): -15K to -57.5K Qdown
- Diamond (21-25): -75K to -127K Qdown
- Master (26-30): -200K to -362K Qdown
- Grandmaster (31-35): -700K to -2.7M Qdown
- Legend (36-40): -2M to -15M Qdown

**Data Source**: Based on observed gameplay data with interpolation
- Qup per flip: Always +100
- XP and Gold scale with rank
- Exponential Qdown growth at high ranks

**Implementation**: `data/ranks.py` with complete reward/penalty tables

### 5. Simulation Engine

**Features**:
- Simulates all 20 possible round outcomes (best-of-5)
- Handles recursive trigger cascades with AVS checking
- Tracks: Q currency, qmult, battle bonus, triggers, efficiency
- Proper trigger order: spiral outward from center
- **Battle Bonus persistence**: BB carries across flips, rounds, and games
- **Round multipliers**: 2x Qup/gold/xp on win, 2x Qdown on loss

**Battle Bonus Mechanics**:
- Increments by 1 on each loss flip
- Nodes like Adrenaline add +1 BB per trigger
- Resets to 0 on wins (AFTER node evaluation, not before)
- Used by Battle Medic to multiply qmult
- Persists between games (set via "Initial BB" input)

**Example Flow** (single loss flip with BB=3):
1. Reset all node AVS counters
2. BB increments: 3 → 4
3. Set `q_this_flip = -700,000` (base Qdown)
4. Trigger "flip" nodes (spiral order)
5. Trigger "loss" nodes (spiral order)
   - Angel of Death: `qmult *= 3`
   - Panic: Triggers all 5-6 adjacent nodes
   - Adrenaline triggers: BB increments to 5, 6, 7...
   - Battle Medic uses BB in qmult calculation
   - Those nodes trigger Panic back → cascade
6. Apply qmult: `q_currency += q_this_flip * qmult`
7. If win: BB resets to 0 (otherwise persists)

**Upgrade Path Bug Fix**:
- Fixed non-AVS upgrade attributes to replace instead of accumulate
- AVS increases remain additive as intended
- Affects: Battle Medic effect_mult, EMT bb_multiplier, all node-specific bonuses

## Results at Grandmaster 1 (Rank 31)

### Best Configuration Found (With Refinement)

**Strategy**: Angel in trigger cluster for massive Q gains

**Position Layout**:
- **Angel**: Ring 3, adjacent to Panic (-3, 0, 3)
- **Trigger cluster**: Low Point, Adrenaline, Extra Dose, Angel of Death all near Panic
- **Angel triggers**: 93-114 per outcome (vs 33-45 with Angel outer)

**Performance** (No upgrades):
- **Min Q**: -5.2M (worst case WLWLL)
- **Avg Q**: +43.8M (positive on average!)
- **Max Q**: +109.7M (best case WLWLW)
- **Positive outcomes**: 18/20 (90% success rate)
- **Efficiency**: 87.9%

### Angel Positioning Strategy Comparison

| Metric | Angel Outer (Ring 7-8) | Angel in Cluster (Ring 3-4) |
|--------|------------------------|---------------------------|
| **Min Q (worst case)** | -804K | -5.2M |
| **Avg Q** | -574K | **+43.8M** ✓ |
| **Max Q** | +150K | +109.7M |
| **Positive outcomes** | 1/20 (5%) | **18/20 (90%)** ✓ |
| **Avg triggers/outcome** | 80-90 | **93-114** ✓ |
| **Angel triggers** | 1-2 per round | **30-50 per round** ✓ |
| **Strategy** | Safe, low variance | High risk, high reward |

**Key Insight**: Angel in trigger cluster creates **massive positive Q** in most scenarios (90% success) by getting triggered repeatedly. The tradeoff is a worse worst-case, but the average case is **78x better** (+43.8M vs -574K).

### Refinement Impact

**Typical improvements per candidate**:
- Best: +321.8M min_q (from -327M to -5.2M)
- Average: +3M to +150M per candidate
- All 10/10 candidates improved through local search

**Refinement operations**:
- Node swaps: 50-100 per candidate
- Cluster rotations: 10-20 per candidate
- Cache hit rate: 60-72% (avoids redundant simulations)

### Key Tradeoffs

| Metric | High Panic AVS (6-7) | Low Panic AVS (3-4) |
|--------|---------------------|---------------------|
| Total Triggers | 35-50 per flip | 20-30 per flip |
| Efficiency | 45-52% | 60-75% |
| Q Outcomes | Better (more cascades) | Worse (fewer cascades) |
| Wasted Triggers | High (50%+) | Low (25-40%) |

**Recommendation**: Angel-in-cluster strategy with iterative refinement produces massively positive average Q. Accept the worse worst-case for 90% positive outcomes.

## File Reference

### Debug/Test Scripts
- `debug_panic_efficiency.py` - Analyze Panic trigger efficiency
- `debug_single_flip.py` - Detailed single-flip logging
- `test_triggers.py` - Test trigger clustering

### Data Files
- `data/nodes.py` - All node definitions (NODES + MOVABLE_NODES)
- `data/ranks.py` - Complete rank progression system (40 ranks)
- `rank_notes.txt` - Observed rank data from gameplay

### API Files
- `api/routes.py` - Flask REST API endpoints
- `api/serializers.py` - JSON serialization for dataclasses
- `app.py` - Flask application entry point (port 5001)

### Frontend Files
- `frontend/src/App.vue` - Main Vue application
- `frontend/src/components/HexGrid.vue` - SVG hex grid with zoom/pan
- `frontend/src/components/UpgradePanel.vue` - Upgrade sliders + optimizer
- `frontend/src/components/ResultsPanel.vue` - Simulation results display
- `frontend/src/utils/hexMath.js` - Hex coordinate math (60° rotated)
- `frontend/src/utils/api.js` - API client wrapper

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

## Recent Improvements (2025)

### Iterative Refinement System (NEW!)
- ✅ **Local search optimizer** - Iteratively improve layouts via node swaps and rotations
- ✅ **Evaluation caching** - 60-72% cache hit rate during refinement
- ✅ **Diverse candidate selection** - Pick top layouts across multiple metrics (min_q, avg_q, adjacency, efficiency)
- ✅ **Domain-aware operations** - Angel positioning, trigger cluster optimization, EMT proximity
- ✅ **Cluster rotation** - Rotate groups of nodes around Panic in 60° increments
- ✅ **Angel-in-cluster strategy** - Place Angel adjacent to Panic for 90% positive outcomes
- ✅ **Layout manipulation utilities** - Swap nodes, rotate clusters, validate layouts
- ✅ **Performance tracking** - Show improvement per candidate, cache statistics

### Web Interface
- ✅ Interactive hex grid with SVG rendering
- ✅ Click-to-place node positioning
- ✅ Full node names (no abbreviations)
- ✅ Zoom controls (mouse wheel + buttons)
- ✅ 60° grid rotation (Battle Medic points north)
- ✅ Upgrade optimizer with top 5 configs
- ✅ Initial BB input for persistent state
- ✅ Rank selector (40 ranks across 8 tiers)
- ✅ Real-time evaluation with debouncing

### Simulation Accuracy
- ✅ Fixed BB reset timing (after node evaluation)
- ✅ Battle bonus persistence across games
- ✅ Round multipliers (2x on win/loss)
- ✅ Upgrade path bug fix (replace vs accumulate)
- ✅ Comprehensive rank system with accurate Qdown values

### API & Data
- ✅ Complete rank progression system (Bronze → Legend)
- ✅ JSON serialization for all dataclasses
- ✅ RESTful API with 8 endpoints
- ✅ Initial BB support throughout simulation chain

## Future Improvements

1. **Simulated Annealing**: Explore global optima beyond local search
2. **Multi-Objective Pareto**: Optimize for both worst-case AND average-case Q
3. **Layout Comparison**: Side-by-side comparison of multiple layouts in web UI
4. **Save/Load Layouts**: Persist layouts to localStorage or URL params
5. **Genetic Algorithm**: Evolve layouts over generations with crossover/mutation
6. **Adjacent Node AVS Balancing**: Ensure Panic's targets have enough AVS for all triggers
7. **Battle Bonus Visualization**: Show BB accumulation timeline in results panel
8. **Mobile Responsive**: Optimize layout for smaller screens
9. **Upgrade + Position Co-optimization**: Jointly optimize upgrades and positions
10. **Angel trigger visualization**: Show exactly when/how often Angel triggers per outcome

## Credits

Built to optimize skill tree for Grandmaster rank progression in Qup.

Core insight: Position matters more than raw stats. A well-clustered grid with moderate upgrades outperforms scattered nodes with max upgrades.
