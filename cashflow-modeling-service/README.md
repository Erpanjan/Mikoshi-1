# Cashflow Analytics Engine
Python package for performing time step-based simulations of personal finances. Built for multi-year cashflow projections with comprehensive modeling of income, expenses, loans, accounts, and taxes.

## Overview
The package provides comprehensive models of people, jobs, accounts, insurance, debt, and more within a time step-based simulation framework. Built on the [Mesa](https://github.com/projectmesa/mesa) agent-based modeling framework, it supports both **deterministic projections** and **Monte Carlo simulations** with correlated investment returns. Includes an example Jupyter Notebook and can be used programmatically for in-depth financial studies.

## Key Features
- **Comprehensive Financial Modeling**: Model families, individuals, jobs, various account types, insurance policies, debt, taxes, and more
- **Dual Simulation Modes**: 
  - **Deterministic**: Fixed growth rates for predictable projections
  - **Probabilistic (Monte Carlo)**: Stochastic returns with asset class correlations for risk analysis
- **Asset Allocation-Based Returns**: Investment accounts can derive expected returns and volatility from asset allocations
- **Multi-Year Projections**: Simulate cashflows over decades with configurable scenarios
- **Flexible Configuration**: YAML-based configuration system for different economic scenarios

## Repository Structure

```
life-model/
├── src/life_model/           # Core cashflow engine
│   ├── model.py              # Main LifeModel simulation class
│   ├── registry.py           # Component registry system
│   ├── people/               # Person and Family models
│   ├── account/              # Financial accounts (Bank, 401k, IRA, HSA, Brokerage)
│   ├── debt/                 # Debt instruments (Loans, Credit Cards)
│   ├── insurance/            # Insurance policies (Life, General, Annuities, Social Security)
│   ├── housing/              # Housing models (Home, Apartment)
│   ├── work/                 # Employment and salary models
│   ├── tax/                  # Tax calculations (Federal, State, FICA)
│   ├── charity/              # Charitable giving (Donations, DAF)
│   ├── dependents/           # Children and 529 plans
│   ├── config/               # Configuration management
│   ├── services/             # Payment and tax services
│   ├── montecarlo/           # Monte Carlo simulation engine
│   └── tests/                # Comprehensive test suite (290+ tests)
├── config/                   # YAML configuration files
│   └── scenarios/            # Economic scenario configurations
└── deepqlearning/            # Optional AI/RL components (not part of core)
```

## Motivation
While impossible to predict the future, the goal of this package is to provide a robust framework for modeling financial outcomes based on various inputs. The best way to use this model is to change one variable at a time and evaluate how it impacts the outcome.

## Getting Started

### Quick Start
Check out the example simulation notebook:
- [Google Colab (interactive)](https://colab.research.google.com/github/sw23/life-model/blob/main/ExampleSimulation.ipynb)
- [GitHub](https://github.com/sw23/life-model/blob/main/ExampleSimulation.ipynb)

![Training Statistics](img/stats.png)

### Installation
```bash
python -m pip install life-model
```

## Simulation Modes

### Deterministic Mode (Default)
In deterministic mode, investment accounts use fixed growth rates for predictable projections:
- Default growth rate: 7% annually (configurable per account)
- Accounts with asset allocations derive expected returns from the allocation weights

### Probabilistic Mode (Monte Carlo)
For risk analysis, the Monte Carlo simulator provides:
- **Correlated Returns**: Investment returns are correlated across accounts based on asset allocations
- **Market Assumptions**: Configurable expected returns, volatilities, and correlations for 8 asset classes
- **Percentile Analysis**: Results include 5th, 10th, 25th, 50th, 75th, 90th, 95th percentiles
- **Success Rate Calculation**: Probability of maintaining positive balances throughout retirement

#### Default Asset Classes
| Asset Class | Expected Return | Volatility |
|-------------|----------------|------------|
| US Large Cap | 10% | 18% |
| US Small Cap | 12% | 22% |
| International Developed | 8% | 20% |
| Emerging Markets | 10% | 28% |
| US Bonds | 4% | 6% |
| International Bonds | 3% | 8% |
| REITs | 9% | 20% |
| Cash | 2% | 1% |

#### Example: Running Monte Carlo Simulation
```python
from life_model.montecarlo import MonteCarloSimulator, MonteCarloConfig

def create_model():
    # Your model setup code here
    return model

simulator = MonteCarloSimulator(
    config=MonteCarloConfig(num_simulations=500, random_seed=42)
)
results = simulator.run(create_model)

print(f"Success rate: {results.success_rate():.1%}")
percentiles = results.get_percentile_df('Bank Balance')
```

## Modeling Status
This package supports a comprehensive range of financial modeling components:

### Core Components
- [x] **Family & Person Models** - Multi-person households with individual financial profiles
- [ ] **Children** - Dependents with education and care costs
- [x] **Jobs** - Employment with salary progression and benefits

### Accounts & Investments
- [x] **Bank Accounts** - Checking/savings with interest
- [x] **401k Plans** - Traditional and Roth with employer matching
- [x] **Traditional & Roth IRAs** - Individual retirement accounts with asset allocation support
- [x] **HSA** - Health Savings Accounts
- [x] **529 Plans** - Education savings accounts with Monte Carlo support
- [x] **Brokerage Accounts** - Taxable investment accounts with asset allocation
- [ ] **Pensions** - Defined benefit retirement plans
- [ ] **Trust Accounts** - Revocable and irrevocable trusts for estate planning

### Insurance & Protection
- [x] **Life Insurance** - Term and whole life policies with loans
- [x] **General Insurance** - Health, auto, home, umbrella insurance
- [ ] **Long Term Care Insurance** - Coverage for nursing home, assisted living, and in-home care
- [x] **Annuities** - Fixed and variable annuities with various payout options
- [x] **Social Security** - Comprehensive benefit calculations with timing strategies

### Debt Management
- [x] **Student Loans** - Education debt with various repayment options
- [x] **Car Loans** - Auto financing
- [x] **Credit Cards** - Revolving debt with interest calculations
- [x] **Mortgages** - Home loans (integrated with housing model)

### Tax System
- [x] **Federal Taxes** - Complete income tax calculations with brackets
- [ ] **State Taxes** - Configurable state tax rates (basic flat rate only)
- [x] **FICA Taxes** - Social Security and Medicare taxes
- [x] **Required Minimum Distributions (RMDs)** - Retirement account distributions

### Housing & Lifestyle
- [x] **Home Ownership** - Purchase, mortgage, appreciation, and selling
- [x] **Rental Housing** - Apartment leasing with rent increases
- [x] **Life Events** - Marriage, retirement, career changes

### Non-Housing Real Assets
- [ ] **Vehicles** - Cars, boats, RVs with purchase, financing, depreciation, maintenance, insurance, and resale
- [ ] **Collectibles & Valuables** - Art, jewelry, antiques with appreciation/depreciation and insurance
- [ ] **Other Tangible Assets** - Equipment, machinery with rental income potential
- [ ] **Asset Financing** - Loans and leases for non-housing assets

### Healthcare & Aging
- [ ] **Medicare Coverage** - Parts A, B, C, D with premium calculations
- [ ] **Long-Term Care Services** - Nursing homes, assisted living, home health aides
- [ ] **Medical Expense Modeling** - Age-related healthcare cost increases
- [ ] **Chronic Care Management** - Ongoing medical conditions and treatment costs
- [ ] **Prescription Drug Coverage** - Medicare Part D and supplemental insurance

### Giving & Legacy
- [x] **Charitable Giving** - Tax-deductible donations with itemized deduction support
- [x] **Donor Advised Funds** - Charitable investment accounts with growth, fees, and distributions
- [ ] **Estate Planning** - Wills, trusts, and inheritance tax modeling
- [ ] **End of Life Care** - Long-term care facilities and medical expenses
- [ ] **Funeral and Final Expenses** - End-of-life costs and pre-planning

### Simulation & Analysis
- [x] **Monte Carlo Simulation** - Probabilistic projections with correlated returns
- [x] **Economic Scenarios** - Configurable market conditions (recession, inflation, etc.)
- [x] **Payment Services** - Intelligent bill payment with account prioritization
- [x] **Tax Optimization** - Strategic withdrawal and contribution planning

> **Note**: The `deepqlearning/` folder contains optional AI-driven optimization features and is not part of the core cashflow model. It can be safely removed if AI features are not needed.

## Examples and Documentation

### Configuration System
YAML-based configuration files in `/config/scenarios/` allow modeling of different economic conditions:
- `conservative.yaml` - Low growth, stable conditions
- `aggressive.yaml` - High growth, volatile markets
- `recession.yaml` - Economic downturn scenarios
- `high_inflation.yaml` - Inflationary environment modeling

### Investment Account Configuration
Investment accounts support two modes of return configuration:

**Fixed Growth Rate (Deterministic)**
```python
from life_model.account.brokerage import BrokerageAccount

account = BrokerageAccount(
    person=person,
    company="Vanguard",
    balance=100000,
    growth_rate=7.0  # Fixed 7% annual growth
)
```

**Asset Allocation (Supports Monte Carlo)**
```python
account = BrokerageAccount(
    person=person,
    company="Vanguard", 
    balance=100000,
    asset_allocation={
        "us_large_cap": 0.40,
        "us_small_cap": 0.10,
        "intl_developed": 0.20,
        "us_bonds": 0.25,
        "cash": 0.05
    }
)
# Expected return and volatility are derived from the allocation
print(f"Derived return: {account.derived_expected_return:.2%}")
print(f"Derived volatility: {account.derived_volatility:.2%}")
```

## Contributing
This project is open source and welcomes contributions. Please see the test suite in `src/life_model/tests/` for examples of expected functionality and to ensure your changes don't break existing features.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## How to Cite
If you use this package in your research, please cite it as follows:
```bibtex
@software{life_model,
  author = {Spencer Williams},
  title = {life-model: Personal Finance Simulation Framework},
  url = {https://github.com/sw23/life-model},
  version = {0.0.0},
  year = 2025
}
```
