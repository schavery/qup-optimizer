# Skill Tree Position Optimizer

Optimizes movable node positions for high-rank play where Qdown penalties are extreme.

## Strategy

At Grandmaster ranks (31+), Qdown penalties are massive (-700K at GM1). The optimization strategy focuses on:

1. **Qdown Prevention First**: Nodes like EMT and Triage reduce the Qdown penalty
2. **Angel Triggers Last**: Angel must be in outer rings (5-8) to trigger after all Qdown prevention, doubling the benefit
3. **Maximize Worst-Case**: Optimize for the worst possible round outcome to ensure survival

## Usage

### Basic Run
```bash
python -m optimizer.main --candidates 100 --rank 31
```

### Arguments
- `--candidates N`: Number of random layouts to generate and evaluate (default: 100)
- `--rank N`: Player rank (default: 31 = Grandmaster 1)
- `--top N`: Show top N candidates in summary (default: 10)
- `--detailed N`: Show detailed results for top N candidates (default: 3)
- `--seed N`: Random seed for reproducibility (default: 42)
- `--upgrades JSON`: Upgrade configuration as JSON (optional)

### Example with Upgrades
```bash
python -m optimizer.main --candidates 200 --rank 31 --upgrades '{"EMT": [2, 1], "Triage": [1, 3]}'
```

## Output

The optimizer shows:

1. **Top Candidates Summary**: Min/Max/Avg Q for best layouts
2. **Detailed Results**: For top N candidates:
   - Node positions by ring
   - ASCII hex grid visualization
   - Complete outcome spectrum (all 20 round outcomes)
3. **Optimization Summary**: Best overall metrics

## Understanding Results

### Ring Positions
- **Ring 0-2**: Inner rings, trigger early in spiral order
- **Ring 3-5**: Mid rings, good for trigger nodes
- **Ring 6-8**: Outer rings, trigger last (ideal for Angel)

### Round Outcomes
Format: `WWW` = 3-0 win, `WWLLL` = 2-3 loss

- Best-case is usually rounds with losses early (WWLLL) - more BB accumulation
- Worst-case is usually clean sweeps (WWW or LLL) - less node triggering

### Status Indicators
- `✓ NON-NEGATIVE worst-case Q`: Configuration can survive all outcomes
- `✗ Negative worst-case Q`: Some outcomes will lose Q currency

## Files

- `candidate_generator.py`: Ring-based position generation
- `evaluator.py`: Simulates all round outcomes and scores layouts
- `visualizer.py`: Formats and displays results
- `main.py`: CLI entry point
