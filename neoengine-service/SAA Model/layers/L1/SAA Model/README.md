# Strategic Asset Allocation (SAA) Model

## Overview

This repository contains the implementation of HSBC's Strategic Asset Allocation methodology as described in the SAA Methodology Paper (October 2020). The model provides both **Equilibrium SAA** and **Dynamic SAA** optimization capabilities, designed to streamline and standardize multi-asset portfolio construction across the client continuum.

## Model Architecture

### Core Components

1. **Equilibrium SAA** (`equilibrium_saa.py`)
   - No-view strategic allocation that minimizes tracking error to market portfolio
   - Implements transformation approach using cluster-level optimization
   - Anchors to naive benchmarks while expanding opportunity set

2. **Dynamic SAA** (`dynamic_saa.py`) 
   - Incorporates active views through expected returns
   - Maximizes utility while controlling active risk
   - Applies sophisticated tracking error constraints at portfolio and cluster levels

3. **Data Processor** (`data_processor.py`)
   - Handles covariance matrix estimation and validation
   - Manages asset return data processing and outlier detection
   - Provides data validation and quality assurance

4. **Results Exporter** (`results_exporter.py`)
   - Generates comprehensive Excel reports with optimization results
   - Provides detailed portfolio analytics and risk attribution
   - Supports multiple output formats for different stakeholders

## Mathematical Framework

### Equilibrium SAA Formulation

**Objective:** Minimize tracking error to market portfolio in cluster space
```
ŵ*_e = argmin (ŵe - γŵb)′ Π (ŵe - γŵb)
```

**Subject to:**
- Risk targeting: `ŵe′ Π ŵe ≤ σ²_target`
- Full investment: `ŵe′ 1 = 1`
- Non-negativity: `ŵe,i ≥ 0`

**Transformation:** `w*_e = Ω ŵ*_e`

Where:
- `Ω`: Transformation matrix mapping cluster weights to asset weights
- `Π`: Cluster-level covariance matrix (`Π = Ω′ Σ Ω`)
- `γ`: Large scaling factor (default: 100)

Liquidity handling:
- The optimizer works in cluster-space and then transforms back to asset weights. Liquidity can be handled in two ways (set in `config.py` via `LIQUIDITY_MODE`):
  - `fixed_post` (default): optimize including liquidity, then force the liquidity asset to `LIQUIDITY_TARGET` post‑hoc and rescale other assets.
  - `exclude_then_add`: optimize only non‑liquidity assets with an adjusted target risk `σ_nonliq = σ_total / (1 − L)` assuming zero‑risk liquidity, then add back liquidity at `L = LIQUIDITY_TARGET`.
  - Note: the Summary “Equilibrium Risk” is computed in asset space after liquidity handling.
  - Update (2025‑09): In `exclude_then_add`, Equilibrium now truly excludes the Liquidity cluster from the decision variables and constraints, applies the risk band in the reduced cluster space, and then maps back to asset space with Liquidity set to `L`.

### Dynamic SAA Formulation

**Objective:** Maximize risk-adjusted expected return
```
w*_d = argmax wd′r - λ/2(wd - we)′ Σ̃ (wd - we)
```

**Subject to:**
- Total risk: `wd′ Σ̃ wd ≤ σ²` (Paper Equation 7)
- Tracking error: `(wd - we)′ Σ̃ (wd - we) ≤ (ACTIVE_RISK_BUDGET)² × σ²`
- Cluster constraints: `(ec ⊙ (wd - φwb))′ Σ̃ (ec ⊙ (wd - φwb)) ≤ (ACTIVE_RISK_BUDGET)² × σ²_c`
- Full investment: `wd′ 1 = 1`
- Non-negativity: `wd,i ≥ 0`

Liquidity handling (Dynamic SAA):
- `fixed_post`: liquidity is part of the decision vector and can drift under constraints.
- Update (2025‑09): `exclude_then_add` implemented to mirror Equilibrium. Dynamic now removes the Liquidity asset from the decision vector, enforces `sum(non‑liq) = 1−L`, sets Liquidity to `L`, and evaluates total‑risk, TE, and cluster TE on the full portfolio. This keeps Liquidity exactly at `LIQUIDITY_TARGET` in Dynamic outputs.

Where:
- `φ = (ec ⊙ wd)′1 / (ec ⊙ wb)′1`: Dynamic scaling factor
- `σ² ≡ we′ Σ we`: Variance target from equilibrium portfolio
- `σ²_c ≡ (ec ⊙ we)′ Σ (ec ⊙ we)`: Cluster-level variance

## Constraint (7) feasibility and diagnostics

The model enforces the paper’s total risk constraint:
```
wd′ Σ̃ wd ≤ σ²   (σ² = we′ Σ we)
```

Note: if the active covariance Σ̃ embeds higher risk than the base Σ, the paper form can be infeasible (e.g., `we′ Σ̃ we > σ²`). To help you assess this, the exporter writes a `Constraint7_Feasibility` sheet to `SAA_Results.xlsx` with:
- `σ²` target from equilibrium, `we′Σ̃we` and `we′Σwe` values, feasibility flags, slack/violation, and a recommendation.

If you encounter infeasibility in your own datasets, consider:
- Adjusting `ACTIVE_RISK_BUDGET` or the target volatility, and verifying matrix conditioning in the diagnostics.
- If needed for operations, a practical alternative sometimes used in industry is `wd′ Σ wd ≤ σ²` (uses base covariance for total risk), while keeping Σ̃ for tracking-error constraints.

## Configuration Parameters

### Risk Management (`config.py`)

```python
# Core risk parameters
ACTIVE_RISK_BUDGET = 0.1           # 10% active risk budget (volatility)
LAMBDA_ACTIVE = 2                  # Active risk aversion parameter
RISK_TOLERANCE = 0.001             # Equilibrium optimization tolerance (cluster-space risk band)
DYNAMIC_RISK_TOLERANCE = 0.0005    # Dynamic optimization tolerance (used in total risk band)

# Liquidity management
LIQUIDITY_TARGET = 0.02            # 2% minimum liquidity allocation

# Optimization settings
NUM_OPTIMIZATION_ATTEMPTS = 4      # Multiple starting points for stability
MAX_OPTIMIZATION_ITERATIONS = 500  # Maximum solver iterations
CONVERGENCE_TOLERANCE = 1e-8       # Numerical convergence threshold
LIQUIDITY_MODE = 'fixed_post'      # 'fixed_post' | 'exclude_then_add'
GAMMA_ANCHOR = 100.0               # Anchoring strength in Equilibrium objective
```

Notes:
- In some datasets, raising `ACTIVE_RISK_BUDGET` (e.g., to `0.30`) materially improves Dynamic feasibility under the paper total‑risk constraint with Σ̃ on the LHS.
- Set `LIQUIDITY_MODE = 'exclude_then_add'` to keep Liquidity fixed at `LIQUIDITY_TARGET` in both Equilibrium and Dynamic outputs.

### Asset Class Configuration

The model supports the following asset classes:
- **Equities:** DME (Developed Market Equities), EME (Emerging Market Equities), FME (Frontier Market Equities)
- **Fixed Income:** 
  - Defensive: Gov (Government), Infl (Inflation-Linked), IG (Investment Grade)
  - Risky: HYD (High Yield), EMD_H (EM Debt Hard Currency), EMD_L (EM Debt Local), EMD_C (EM Corporate)
- **Alternatives:** SIG (Securitized), Liquidity
- **Others:** Cash equivalents

### Risk Profiles

The model supports 5 risk profiles with corresponding naive benchmarks:
- **RP1 (Conservative):** 15% Equity / 85% Fixed Income
- **RP2 (Cautious):** 30% Equity / 70% Fixed Income  
- **RP3 (Balanced):** 50% Equity / 50% Fixed Income
- **RP4 (Growth):** 70% Equity / 30% Fixed Income
- **RP5 (Equity):** 85% Equity / 15% Fixed Income

## Usage Guide

### Basic Usage

```python
from saa_model import EquilibriumSAA, DynamicSAA
import numpy as np

# 1. Equilibrium SAA
equilibrium_model = EquilibriumSAA(
    market_weights=market_weights,
    asset_clusters=asset_clusters,
    risk_target=0.12,  # 12% target volatility
    cov_matrix=covariance_matrix,
    asset_names=asset_names
)

equilibrium_weights = equilibrium_model.optimize()

# 2. Dynamic SAA  
dynamic_model = DynamicSAA(
    equilibrium_weights=equilibrium_weights,
    expected_returns=expected_returns,
    active_cov_matrix=active_covariance,
    asset_clusters=asset_clusters,
    asset_names=asset_names,
    risk_target=0.12,
    base_cov_matrix=base_covariance,
    market_weights=market_weights
)

dynamic_weights = dynamic_model.optimize()
```

### Advanced Configuration

```python
# Custom risk parameters
dynamic_model = DynamicSAA(
    # ... basic parameters ...
    lambda_active=3.0,  # Higher risk aversion
    market_weights=custom_market_weights,  # Custom benchmark
    historical_cov_matrix=fallback_matrix,  # Fallback data
    ask_user_for_fallback=False  # Automated fallback
)

# Diagnostics and validation
diagnostics = dynamic_model.get_implementation_diagnostics()
transformation_info = equilibrium_model.get_transformation_diagnostics()

# Check if paper's constraint (7) would be feasible with your data
feasibility = dynamic_model.check_constraint_7_feasibility()
print(f"Paper constraint feasible: {feasibility['paper_formulation']['feasible']}")
print(f"Recommendation: {feasibility['recommendation']}")
```

## Integration Guide

### Data Requirements

**Input Data Specifications:**
```python
# Required arrays (all same length)
market_weights: np.array      # Market capitalization weights
expected_returns: np.array    # Arithmetic expected returns  
base_cov_matrix: np.array     # Base covariance matrix (n×n)
active_cov_matrix: np.array   # Active covariance matrix (n×n)
asset_names: List[str]        # Asset class identifiers

# Required mappings
asset_clusters: Dict[str, str]  # Asset → Cluster mapping
# Example: {'DME': 'Equities', 'Gov': 'Defensive Fixed Income'}
```

**Data Quality Requirements:**
- Minimum 60 monthly observations for covariance estimation
- No missing values in return series
- Positive definite covariance matrices
- Normalized market weights (sum to 1)

### Integration with External Systems

#### 1. Portfolio Management Systems

```python
# Integration with portfolio management platform
class SAA_Integration:
    def __init__(self, pms_connection):
        self.pms = pms_connection
        
    def run_monthly_saa_update(self, risk_profile):
        # Fetch latest market data
        market_data = self.pms.get_market_data()
        
        # Run optimization
        saa_weights = self.optimize_portfolio(market_data, risk_profile)
        
        # Upload to PMS
        self.pms.update_strategic_allocation(saa_weights)
        
        return saa_weights
```

#### 2. Risk Management Systems

```python
# Risk reporting integration
def generate_risk_report(portfolio_weights, model):
    metrics = model._calculate_metrics(portfolio_weights)
    
    risk_report = {
        'portfolio_volatility': metrics['risk'],
        'tracking_error': metrics['tracking_error'], 
        'expected_return': metrics['expected_return'],
        'active_risk_budget_utilization': metrics['tracking_error'] / model.active_risk_budget,
        'constraint_violations': model.check_constraint_compliance(portfolio_weights)
    }
    
    return risk_report
```

## Troubleshooting

### Common Issues

1. **Optimization Convergence Failures**
   ```
   Solution: Check covariance matrix condition number
   Use: model.get_transformation_diagnostics()
   ```

2. **Infeasible Constraint Systems**
   ```
   Solution: Verify active risk budget settings
   Check: constraint_violations in diagnostics
   ```

3. **Matrix Singularity Issues**
   ```
   Solution: Increase regularization parameters
   Modify: MIN_EIGENVALUE_THRESHOLD in config.py
   ```

4. **Paper Constraint (7) Infeasibility**
   ```
   Symptom: Optimization fails with "infeasible problem"
   Diagnosis: Use model.check_constraint_7_feasibility()
Assessment: The implementation enforces the paper form (wd′ Σ̃ wd ≤ σ² with σ² = we′ Σ we)
Action: If infeasible with your data, consider using wd′ Σ wd ≤ σ² operationally while keeping Σ̃ for TE constraints
Note: Infeasibility can occur when active covariance embeds higher risk than the base covariance
   ```

5. **Equilibrium risk above target while Status = Success**
```
Meaning: “Success” indicates the optimizer converged and satisfied constraints in cluster space. The reported “Equilibrium Risk” is computed in asset space after liquidity handling.
Common causes:
- Liquidity enforcement: in `fixed_post`, forcing liquidity to `LIQUIDITY_TARGET` and rescaling others can move asset‑space risk upward, especially for low targets.
- Limited low‑vol capacity with non‑negativity and market anchoring; the minimum achievable risk may exceed very low targets.
- Tolerances: we enforce a small risk band in cluster space; mapping and rounding can introduce small asset‑space drift.
What to try:
- Set `LIQUIDITY_MODE = 'exclude_then_add'` to better match low targets, or raise `LIQUIDITY_TARGET` for low risk profiles.
- Review cluster mapping and (optionally) reduce `γ` to allow more deviation from market if appropriate.
```

### Performance Characteristics
- **Computational Complexity:** O(k³) for Equilibrium, O(n³) for Dynamic
- **Typical runtime:** < 1 second for standard configurations
- **Memory usage:** ~50MB for typical dataset
- **Supports:** 100+ simultaneous optimizations

### Support and Maintenance

For technical support, integration assistance, or methodology questions, please contact the SAA Model development team.

---

*This README provides comprehensive documentation for the SAA Model implementation. For additional technical details, please refer to the SAA Methodology Paper and inline code documentation.*
 
## Empirical experiments: volatility floor diagnostics

### Goal

Diagnose why very low target volatilities cannot be achieved with certain inputs, and verify whether the lower bound is driven by the data/universe rather than the optimization engine.

### Summary of findings

- **Universe composition matters most**: adding truly low‑volatility sleeves (cash/short‑duration IG) lowered the floor from ~8.8% to ~8.1% (RP1), and further down to ~6.7% in synthetic cases.
- **Covariance structure dominates**: high cross‑cluster correlation produces a high floor even with liquidity present; lowering cross‑asset correlation materially reduces the floor.
- **Non‑negativity is binding**: without low‑vol sleeves, you cannot hedge to very low risk; adding a low‑vol sleeve makes the target approachable.
- **Anchoring (market weights) shifts the floor**: equity‑heavy benchmarks yield notably higher floors than defensive benchmarks under the same covariance.
- **γ (anchoring strength) alone had little effect** in our real dataset; paired with a defensive benchmark tilt, the floor dropped meaningfully. γ matters when constraints are slack enough to allow movement.

### Experiments (no engine changes)

- Baseline (current pack; historical‑risk mode):
  - RP1 target 4% → achieved ~8.8%.

- Add low‑risk sleeves (augmented pack; pre‑calculated risks):
  - RP1 target 4% → achieved ~8.1%.
  - Group the two low‑risk sleeves into one cluster → ~8.1% (no material change).
  - Liquidity mode `fixed_post` vs `exclude_then_add` → ~8.1% (no material change).

- Synthetic low‑variance sleeves:
  - Include near‑cash (≈0.5%) and short‑duration IG (≈2%): dynamic achieved ~6.7% at 3% target.

- Covariance dominance (synthetic):
  - High correlations, modest vols → RP1 ≈ 9.1%.
  - Low correlations, include very low‑vol asset → RP1 ≈ 5.2%.

- Non‑negativity (synthetic):
  - Negative‑corr hedges, no low‑vol sleeve → RP1 ≈ 5.1%.
  - Add short‑duration low‑vol sleeve → RP1 ≈ 4.2%.

- Anchoring (synthetic; same covariance, different benchmarks):
  - Equity‑heavy market weights → RP1 ≈ 8.0%.
  - Defensive‑heavy market weights → RP1 ≈ 5.7%.

- γ sweep (augmented pack; γ ∈ {1,10,100,300}):
  - RP1 ≈ 8.1% for all γ (no movement).

- γ with defensive benchmark tilt (augmented pack):
  - Mild tilt → RP1 ≈ 7.5% for γ ∈ {1,5,10}.
  - Strong tilt → RP1 ≈ 6.7% for γ ∈ {1,5,10}.

### Interpretation

- **Clustering helps only if Π has weak off‑diagonals**: the equilibrium step optimizes in cluster space using Π = Ω′ΣΩ. If clusters remain materially correlated, the cluster‑space risk constraint still binds at a high level.
- **Anchoring and TE constraints bind around the equilibrium**: the dynamic step remains close to equilibrium via TE and cluster‑TE constraints; a riskier equilibrium (from risky benchmarks or high Π cross‑correlations) implies a higher realized floor.
- **Why γ often doesn’t move results**: if the cluster‑space risk band and non‑negativity already pin the solution to a narrow feasible face, changing γ does not change the boundary point. γ matters when constraints are slack and Π allows movement.

### Reproduce locally

- Scripts (all under `scripts/`):
  - `augment_low_risk_data_pack.py`: append cash/short‑duration assets across sheets.
  - `remap_lowrisk_cluster.py`: group low‑risk sleeves into a single cluster label.
  - `test_low_variance_synthetic.py`: synthetic case with near‑cash and short‑duration sleeves.
  - `generate_synthetic_packs.py`: builds covariance, non‑negativity, and anchoring scenarios.
  - `tilt_market_weights.py`: tilt benchmarks toward defensive clusters.
  - Gamma sweeps were run by setting `config.GAMMA_ANCHOR` at runtime before invoking `main.py`.

### Practical levers to lower the floor (data/config only)

- Add or scale genuinely low‑volatility sleeves (cash/T‑bills, short‑duration IG) in the universe and benchmark.
- Improve cluster mapping to reduce Π off‑diagonals (e.g., correlation‑driven clustering; isolate very low‑vol sleeves into their own clusters).
- Consider modestly loosening the cluster‑space risk band (`RISK_TOLERANCE`) if appropriate for your governance.
- Ensure TE budgets and λ allow dynamic to realize equilibrium de‑risking without violating tracking constraints.

### Financially reasonable dataset test (sanity check)

- Composition (13 assets):
  - Equities: `US Equity`, `Dev ex US Equity`, `EM Equity`
  - Fixed income: `Global Gov Bonds`, `Global IG Corporate`, `Short Duration IG`, `Global High Yield`, `EM Debt (Hard)`, `Inflation-Linked Bonds`
  - Alternatives: `Commodities`, `Gold`, `Hedge Funds`
  - Liquidity: `Cash_TBills`
- Market weights (example): equity ~47%, fixed income ~36%, alts ~15%, cash 2% (sums to 1)
- Expected returns and vols: long‑run plausible ranges (equities higher return/vol; Gov/IG lower; ShortDur ≈ 2.5% vol; cash ≈ 0.5% vol)
- Correlations:
  - High within‑equities (≈0.78–0.85); moderate FI within‑block (Gov–IG 0.7; IG–ShortDur 0.5; Gov–IL 0.6)
  - Cross equity–FI sensible (equity vs Gov ≈ −0.10; vs IG ≈ 0.20; vs HY/EMD higher)
  - Alternatives: commodities ~0.3 to equities; gold ≈ −0.1 to equities; hedge funds ~0.5 to equities; cash ≈ 0.02 to all
- Validation checks performed:
  - Weights sum to 1; vols > 0; correlations clipped to [−0.9, 0.95] and symmetrized
  - Covariance positive‑definite adjustment (nearest PD via diagonal shift) applied if needed; reported shift 1.95e‑03
- Results (pre‑calculated risks):
  - RP1 target 4% → achieved ≈ 4.67%
  - RP2 → ≈ 6.46%; RP3 → ≈ 10.15%; RP4 → ≈ 12.15%; RP5 → ≈ 15.15%
  - RP6 equilibrium failed in this configuration (upper‑end constraints; not material for low‑floor focus)
- Files and reproduction:
  - Data: `SAA Data Pack (Reasonable).xlsx`
  - Results: `SAA_Results_Reasonable.xlsx`
  - Script: `scripts/build_financially_reasonable_pack.py`
  - Run: `python3 -u "SAA Model/main.py" --data "SAA Data Pack (Reasonable).xlsx" --output "SAA_Results_Reasonable.xlsx" --no-calc-risk`