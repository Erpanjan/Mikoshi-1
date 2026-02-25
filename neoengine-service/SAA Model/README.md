# Three-Layer Portfolio Optimization

A multi-layer portfolio construction system that implements Strategic Asset Allocation (SAA) with Black-Litterman optimization across three distinct layers: Layer 1 determines optimal asset class weights using mean-variance optimization with risk profile constraints; Layer 2 allocates active risk budget across asset classes using Black-Litterman to blend equilibrium views with user-provided conviction metrics (tracking error, information ratio, confidence levels); Layer 3 selects and weights individual managers within each asset class using Black-Litterman optimization to match target tracking errors from Layer 2.

---

## Input Data Mapping

### Layer 1: Strategic Asset Allocation

**Script:** `layers/L1/layer1_saa.py` → calls `layers/L1/SAA Model/data_processor.py`

**File:** `Inputs/L1 Asset Allocation/VLTC CMA.xlsx`

| Excel Tab | Code Location | Parameter/Variable | Description |
|-------------|---------------|-------------------|-------------|
| `Market Weight` | `data_processor.py:31-33` | `assets`, `market_weights` | Asset class names (row 0) and market cap weights (row 1) |
| `Expected R&R` | `data_processor.py:37-39` | `exp_returns`, `fu_vols` | Expected returns (row 1) and forward-looking volatilities (row 2) |
| `Naive Benchmark` | `data_processor.py:42` | `risk_profiles` | Risk profile definitions and target volatilities |
| `Asset Cluster Mapping` | `data_processor.py:43` | `clusters` | Asset-to-cluster assignments for constraint grouping |
| `Eq Volatility` | `data_processor.py:47-48` | `eq_vols` | Equilibrium volatilities for equilibrium SAA |
| `Eq Corr Matrix` | `data_processor.py:56-57` | `eq_corr` | Equilibrium correlation matrix for equilibrium SAA |
| `Expected Corr Matrix` | `data_processor.py:65-71` | `active_corr` | Active/forward-looking correlation matrix for Dynamic SAA |

**Config:** `Layer1Config` in `layers/layer_types.py:10-17`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data_file` | `Path` | (required) | Path to VLTC CMA.xlsx |
| `output_file` | `Path` | (required) | Path for SAA results output |
| `risk_profile` | `str` | (required) | Risk profile to optimize (e.g., "RP1") |
| `weight_type` | `str` | `"dynamic"` | `"dynamic"` or `"equilibrium"` weights |

**Optimization Parameters:** `layers/L1/SAA Model/config.py`

| Parameter | Code Location | Default | Description |
|-----------|---------------|---------|-------------|
| `LIQUIDITY_TARGET` | `config.py:20` | `0.02` | Target allocation for cash/liquidity (2%) |
| `ACTIVE_RISK_BUDGET` | `config.py:21` | `0.2` | Active risk budget as fraction of total risk (20%) |
| `LAMBDA_ACTIVE` | `config.py:22` | `2` | Risk aversion parameter for Dynamic SAA objective |
| `GAMMA_ANCHOR` | `config.py:23` | `100.0` | Cluster anchoring strength in Equilibrium objective |
| `RISK_TOLERANCE` | `config.py:29` | `0.008` | Risk tolerance slack for Equilibrium SAA constraints |
| `DYNAMIC_RISK_TOLERANCE` | `config.py:30` | `0.0005` | Risk tolerance slack for Dynamic SAA constraints |
| `LIQUIDITY_MODE` | `config.py:25` | `"exclude_then_add"` | Liquidity handling: `"fixed_post"` or `"exclude_then_add"` |
| `CLUSTER_BUDGET_FACTOR_MIN` | `config.py:44` | `0.5` | Minimum cluster tracking error budget multiplier |
| `CLUSTER_BUDGET_FACTOR_MAX` | `config.py:45` | `1.5` | Maximum cluster tracking error budget multiplier |

---

### Layer 2: Active Risk Budget Allocation

**Script:** `layers/L2/layer2_active_risk.py`

**File 1:** `Inputs/L2 Active Risk Allocation/Active Exposure Conviction.xlsx`

| Excel Sheet | Code Location | Config Parameter | Description |
|-------------|---------------|-----------------|-------------|
| `Active TE IR CL` | `layer2_active_risk.py:179-183` | `config.conviction_sheet` | Asset class expected TE, IR, confidence levels |
| `Active Return Correlation` | `layer2_active_risk.py:224-248` | `config.correlation_sheet` | Asset class active return correlation matrix |

**File 2:** `Inputs/L2 Active Risk Allocation/Passive Vehicle Selection.xlsx`

| Excel Sheet | Code Location | Config Parameter | Description |
|-------------|---------------|-----------------|-------------|
| `Sheet1` | `layer2_active_risk.py:185-201` | `config.asset_allocation_sheet` | Asset class → passive ETF mapping with `Ticker`, `Index`, `Volatility` columns |

**File 3:** `Inputs/L2 Active Risk Allocation/Risk Budgeting.xlsx`

| Excel Sheet | Code Location | Variable | Description |
|-------------|---------------|----------|-------------|
| (default) | `layer2_active_risk.py:175-177` | `passive_risk_pct`, `active_risk_pct` | Active vs passive risk budget split (columns: `Passive`, `Active`) |

**Config:** `Layer2Config` in `layers/layer_types.py:56-66`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `active_exposure_file` | `Path` | (required) | Path to Active Exposure Conviction.xlsx |
| `asset_allocation_file` | `Path` | (required) | Path to Passive Vehicle Selection.xlsx |
| `output_file` | `Path` | (required) | Path for portfolio results output |
| `conviction_sheet` | `str` | `"Active TE IR CL"` | Sheet with asset class TE, IR, confidence |
| `correlation_sheet` | `str` | `"Active Return Correlation"` | Sheet with asset class correlation matrix |
| `asset_allocation_sheet` | `str` | `"Sheet1"` | Sheet with passive ETF mapping |
| `target_volatility` | `float` | `0.12` | Target portfolio volatility (overridden by Layer 1) |

**Optimization Parameters:** `layers/L2/layer2_active_risk.py`

| Parameter | Code Location | Default | Description |
|-----------|---------------|---------|-------------|
| `tau` | `layer2_active_risk.py:258` | `0.05` | Black-Litterman uncertainty parameter for prior scaling |
| `risk_aversion` | `layer2_active_risk.py:311` | `2.5` | Risk aversion parameter for BL optimization |
| `ftol` | `layer2_active_risk.py:432` | `1e-9` | Function convergence tolerance for optimizer |

---

### Layer 3: Manager Selection

**Script:** `layers/L3/layer3_manager_selection.py`

**File:** `Inputs/L3 Active Manager Selection/Active Manager Selection.xlsx`

| Excel Sheet | Code Location | Config Parameter | Description |
|-------------|---------------|-----------------|-------------|
| `Manager Active Exp Conviction` | `layer3_manager_selection.py:120-122` | `config.sheet_name` | Manager data: `AssetClass`, `ISIN`, `Name`, `Expected Tracking Error`, `Expected Information Ratio`, `Confidence Level` |
| `Manager Active Re Corr` | `layer3_manager_selection.py:124-148` | `config.correlation_sheet_name` | Manager active return correlation matrix (ISIN × ISIN) |

**Config:** `ManagerSelectionConfig` in `layers/layer_types.py:34-42`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `manager_selection_file` | `Path` | (required) | Path to Active Manager Selection.xlsx |
| `sheet_name` | `str` | `"Manager Active Exp Conviction"` | Sheet with manager TE, IR, confidence data |
| `correlation_sheet_name` | `str` | `"Manager Active Re Corr"` | Sheet with manager correlation matrix (ISIN × ISIN) |
| `tau` | `float` | `0.05` | Black-Litterman uncertainty parameter |
| `risk_aversion` | `float` | `2.5` | Risk aversion parameter for optimization |

**Optimization Parameters:** `layers/L3/layer3_manager_selection.py`

| Parameter | Code Location | Default | Description |
|-----------|---------------|---------|-------------|
| `tau` | `layer3_manager_selection.py:25` | `0.05` | Black-Litterman uncertainty parameter for prior scaling |
| `risk_aversion` | `layer3_manager_selection.py:48` | `2.5` | Risk aversion parameter for BL optimization |
| `te_penalty_weight` | `layer3_manager_selection.py:52` | `10.0` | Penalty weight for tracking error deviation from target |
| `ftol` | `layer3_manager_selection.py:93` | `1e-9` | Function convergence tolerance for optimizer |

---

## Output

**File:** `outputs/Portfolio_Construction_Results.xlsx`

| Sheet | Contents |
|-------|----------|
| `Asset_Allocation` | One row per vehicle with: Asset Class, Equilibrium Weight, Dynamic Weight, Active Weight, Passive Weight, Portfolio Weight, Vehicle Type (Active/Passive), ISIN/Ticker |
| `Portfolio_Summary` | Risk profile, target volatility, achieved volatility, expected return (Layer 1), portfolio expected return (post Layer 3), portfolio expected volatility (post Layer 3), total portfolio weight |

**Portfolio Summary Outputs (post Layer 3)**

| Output Variable | Code Location | Description |
|----------------|---------------|-------------|
| `Portfolio Expected Return (%)` | `layers/L3/portfolio_metrics.py` → `compute_portfolio_expected_return_and_volatility` | Portfolio-level expected return from Layer 1 base returns plus active alpha from Layer 3 manager selections. |
| `Portfolio Expected Volatility (%)` | `layers/L3/portfolio_metrics.py` → `compute_portfolio_expected_return_and_volatility` | Portfolio-level volatility from blended active/passive sleeve volatilities and Layer 1 correlations. |
| `Expected Return (%)` | `layers/reporting/export.py` | Layer 1 dynamic expected return (for reference). |
| `Achieved Volatility (%)` | `layers/L2/layer2_active_risk.py` | Portfolio volatility achieved by Layer 2 risk-budget optimization (for reference). |

---

## Technical Dependencies

```
python >= 3.9
numpy >= 1.24
pandas >= 2.0
scipy >= 1.10
openpyxl >= 3.1
```

Install: `pip install numpy pandas scipy openpyxl`

---

## Project Structure

```
SAA Model/
├── Inputs/
│   ├── L1 Asset Allocation/
│   │   └── VLTC CMA.xlsx
│   ├── L2 Active Risk Allocation/
│   │   ├── Active Exposure Conviction.xlsx
│   │   ├── Passive Vehicle Selection.xlsx
│   │   └── Risk Budgeting.xlsx
│   └── L3 Active Manager Selection/
│       └── Active Manager Selection.xlsx
├── layers/
│   ├── L1/
│   │   ├── layer1_saa.py
│   │   └── SAA Model/
│   │       ├── config.py
│   │       ├── data_processor.py
│   │       ├── dynamic_saa.py
│   │       ├── equilibrium_saa.py
│   │       ├── main.py
│   │       └── results_exporter.py
│   ├── L2/
│   │   └── layer2_active_risk.py
│   ├── L3/
│   │   └── layer3_manager_selection.py
│   ├── reporting/
│   │   └── export.py
│   └── layer_types.py
└── outputs/
    └── Portfolio_Construction_Results.xlsx
```
