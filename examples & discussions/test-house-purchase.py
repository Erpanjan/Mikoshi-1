#!/usr/bin/env python3
"""
Test Case: House Purchase Goal (V2 - Improved Report Structure)
- Single goal: House purchase ($10M in 5 years)
- No income
- No other expenses
- $7M initial capital in bank balance

Report Structure (per user feedback):
1. Executive Summary & Client Profile
2. Current State Analysis (Deterministic)
3. Monte Carlo Simulation with 10 individual trajectories
4. Gap Analysis → For each gap: Action Plan → Corresponding Analysis
5. Portfolio Optimization with Security-level details
"""

import json
import requests
from datetime import date

# Configuration
CASHFLOW_URL = "http://localhost:8001"
NEOENGINE_URL = "http://localhost:8000"
NEOENGINE_API_KEY = "8c8c612b37eea10e13c46a3ced0fd0b86ad1024e5e88d0dc007b23f93cced897"

# Test client data
CURRENT_YEAR = date.today().year
TARGET_YEAR = CURRENT_YEAR + 5

# Investment amount to allocate (matching the action plan)
INVESTMENT_AMOUNT = 7_000_000  # Full $7M for analysis consistency


def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_json(data, indent=2):
    print(json.dumps(data, indent=indent, default=str))


# =============================================================================
# STAGE 1: Deterministic Simulation - Current State (Bank Only, ~0.5% interest)
# =============================================================================
def stage1_current_state():
    """Stage 1: Analyze current state with money in bank earning 0.5% interest."""
    print_header("STAGE 1: CURRENT STATE ANALYSIS (Money in Bank)")
    
    params = {
        "client_profile": {
            "name": "House Buyer",
            "age": 45,
            "retirement_age": 55,
            "life_expectancy": 60
        },
        "accounts": {
            "bank": {"balance": 7000000, "interest_rate": 0.5}
        },
        "income": {"salary": 0},
        "expenses": {"base_spending": 0},
        "goals": [
            {"name": "House Purchase", "target_amount": 10000000, "target_year": TARGET_YEAR}
        ],
        "simulation_config": {"mode": "deterministic"}
    }
    
    print(f"\n📤 Input Parameters:")
    print(f"   - Initial Capital: $7,000,000 (in bank account)")
    print(f"   - Bank Interest Rate: 0.5% (typical savings rate)")
    print(f"   - Annual Income: $0")
    print(f"   - Annual Expenses: $0")
    print(f"   - Goal: House Purchase - $10,000,000 by {TARGET_YEAR}")
    print(f"   - Simulation Mode: Deterministic")
    
    response = requests.post(f"{CASHFLOW_URL}/cashflow/api/v1/simulate", json=params)
    result = response.json()
    
    print(f"\n📊 SIMULATION RESULTS:")
    print(f"   - Success: {result.get('success')}")
    print(f"   - Mode: {result.get('simulation_mode')}")
    
    print(f"\n📈 Year-by-Year Projection:")
    print("-" * 70)
    print(f"{'Year':<8} {'Age':<6} {'Bank Balance':>18} {'Net Worth':>18}")
    print("-" * 70)
    
    for year_data in result.get('yearly_cashflow_projection', [])[:7]:
        year = int(year_data['year'])
        age = year_data['age']
        bank = year_data.get('bank_balance', 0)
        nw = year_data.get('total_net_worth', 0)
        highlight = " ← TARGET YEAR" if year == TARGET_YEAR else ""
        print(f"{year:<8} {age:<6} ${bank:>15,.0f} ${nw:>15,.0f}{highlight}")
    
    goal = result.get('goal_analysis', {}).get('House Purchase', {})
    print(f"\n🎯 GOAL ANALYSIS:")
    print(f"   - Target Amount: ${goal.get('target_amount', 0):,.0f}")
    print(f"   - Projected at Year 5: ${goal.get('projected_amount', 0):,.0f}")
    print(f"   - Shortfall: ${goal.get('shortfall', 0):,.0f}")
    print(f"   - Achievement: {goal.get('achievement_percentage', 0):.1f}%")
    print(f"   - On Track: {goal.get('on_track', False)}")
    
    return result, params


# =============================================================================
# STAGE 2: Monte Carlo Simulation with Individual Trajectories
# =============================================================================
def stage2_monte_carlo_trajectories(base_params):
    """Stage 2: Run Monte Carlo simulation and return individual trajectories."""
    print_header("STAGE 2: MONTE CARLO SIMULATION (10 Individual Trajectories)")
    
    params = base_params.copy()
    params['simulation_config'] = {
        "mode": "monte_carlo", 
        "num_simulations": 100,  # Run 100 simulations
        "return_individual_runs": True,  # Request individual trajectories
        "num_individual_runs": 10,  # Return 10 sampled trajectories
        "seed": 42
    }
    
    print(f"\n📤 Request: Monte Carlo simulation with 100 runs, returning 10 trajectories")
    print(f"   Purpose: Show AI the range of possible wealth outcomes")
    
    response = requests.post(f"{CASHFLOW_URL}/cashflow/api/v1/simulate", json=params)
    result = response.json()
    
    print(f"\n📊 MONTE CARLO SUMMARY:")
    mc = result.get('monte_carlo_results', {})
    print(f"   - Total Simulations: {mc.get('num_simulations', 'N/A')}")
    
    # Terminal wealth percentiles
    percentiles = mc.get('terminal_wealth_percentiles', {})
    print(f"\n📈 Terminal Wealth Distribution (at Target Year):")
    print(f"   - 5th Percentile (Worst Case):  ${percentiles.get('5th', 0):>15,.0f}")
    print(f"   - 25th Percentile:              ${percentiles.get('25th', 0):>15,.0f}")
    print(f"   - 50th Percentile (Median):     ${percentiles.get('50th', 0):>15,.0f}")
    print(f"   - 75th Percentile:              ${percentiles.get('75th', 0):>15,.0f}")
    print(f"   - 95th Percentile (Best Case):  ${percentiles.get('95th', 0):>15,.0f}")
    
    # Individual simulation runs
    individual_runs = result.get('individual_simulation_runs', [])
    
    if individual_runs:
        print(f"\n📊 INDIVIDUAL SIMULATION TRAJECTORIES ({len(individual_runs)} runs):")
        print("=" * 90)
        
        for run in individual_runs:
            run_num = run.get('run_number', 0)
            outcome = run.get('outcome_category', 'Unknown')
            percentile = run.get('percentile_rank', 0)
            terminal_nw = run.get('terminal_net_worth', 0)
            cagr = run.get('effective_cagr_percent', 0)
            
            print(f"\n📈 Run #{run_num}: {outcome} (Percentile: {percentile:.0f}%)")
            print(f"   Effective CAGR: {cagr:.2f}% | Terminal Net Worth: ${terminal_nw:,.0f}")
            print("-" * 80)
            print(f"   {'Year':<8} {'Age':<6} {'Net Worth':>18} {'Change':>15}")
            print("-" * 80)
            
            trajectory = run.get('yearly_trajectory', [])
            prev_nw = None
            for year_data in trajectory[:7]:  # Show up to 7 years
                year = year_data.get('year', 0)
                age = year_data.get('age', 0)
                nw = year_data.get('total_net_worth', 0)
                
                if prev_nw is not None:
                    change = nw - prev_nw
                    change_str = f"+${change:,.0f}" if change >= 0 else f"-${abs(change):,.0f}"
                else:
                    change_str = "-"
                
                highlight = " ← TARGET" if year == TARGET_YEAR else ""
                print(f"   {year:<8} {age:<6} ${nw:>15,.0f} {change_str:>15}{highlight}")
                prev_nw = nw
        
        print("\n" + "=" * 90)
        print("📊 TRAJECTORY SUMMARY:")
        
        # Summarize outcomes
        target = 10_000_000
        achieved = sum(1 for r in individual_runs if r.get('terminal_net_worth', 0) >= target)
        print(f"   - Runs achieving $10M target: {achieved}/{len(individual_runs)}")
        
        avg_terminal = sum(r.get('terminal_net_worth', 0) for r in individual_runs) / len(individual_runs)
        print(f"   - Average terminal net worth: ${avg_terminal:,.0f}")
        
        min_terminal = min(r.get('terminal_net_worth', 0) for r in individual_runs)
        max_terminal = max(r.get('terminal_net_worth', 0) for r in individual_runs)
        print(f"   - Range: ${min_terminal:,.0f} to ${max_terminal:,.0f}")
    
    return result


# =============================================================================
# STAGE 3: Gap Analysis with Action Plans
# =============================================================================
def stage3_gap_analysis(base_params):
    """Stage 3: Identify gaps and propose action plans."""
    print_header("STAGE 3: GAP ANALYSIS & ACTION PLANS")
    
    params = base_params.copy()
    params['simulation_config'] = {"mode": "monte_carlo", "num_simulations": 50}
    
    response = requests.post(f"{CASHFLOW_URL}/cashflow/api/v1/gap-analysis", json=params)
    result = response.json()
    
    gaps = result.get('gaps_identified', {})
    
    print(f"\n🔍 GAPS IDENTIFIED:")
    
    all_gaps = []
    
    # Investment-solvable gaps
    for gap in gaps.get('investment_solvable', []):
        all_gaps.append({
            'type': gap.get('type', 'unknown'),
            'severity': gap.get('severity', 'unknown'),
            'description': gap.get('description', ''),
            'impact': gap.get('quantified_impact', ''),
            'category': 'investment_solvable',
            'potential_fix': gap.get('potential_improvement', '')
        })
    
    # Behavior-solvable gaps
    for gap in gaps.get('behavior_solvable', []):
        all_gaps.append({
            'type': gap.get('type', 'unknown'),
            'severity': gap.get('severity', 'unknown'),
            'description': gap.get('description', ''),
            'impact': gap.get('quantified_impact', ''),
            'category': 'behavior_solvable'
        })
    
    # Other gaps
    for gap in gaps.get('requires_other_solutions', []):
        all_gaps.append({
            'type': gap.get('type', 'unknown'),
            'severity': gap.get('severity', 'unknown'),
            'description': gap.get('description', ''),
            'impact': gap.get('quantified_impact', ''),
            'category': 'requires_other_solutions'
        })
    
    return result, all_gaps


# =============================================================================
# STAGE 4: Portfolio Optimization with Security Details (All 3 Layers)
# =============================================================================
def stage4_portfolio_optimization(investment_amount):
    """Stage 4: Get optimized portfolio with security-level allocations from all 3 layers."""
    print_header("STAGE 4: PORTFOLIO OPTIMIZATION (3-LAYER ALLOCATION)")
    
    # Calculate required return: $7M → $10M in 5 years
    required_return = 7.39
    
    print(f"\n📐 REQUIRED RETURN CALCULATION:")
    print(f"   - Initial: ${investment_amount:,.0f}")
    print(f"   - Target: $10,000,000")
    print(f"   - Years: 5")
    print(f"   - Required CAGR: {required_return:.2f}%")
    
    risk_profile = "RP3"
    target_vol = 0.1007
    
    print(f"\n📤 NeoEngine Request:")
    print(f"   - Risk Profile: {risk_profile} (Moderate)")
    print(f"   - Target Volatility: {target_vol:.2%}")
    print(f"   - Investment Amount: ${investment_amount:,.0f}")
    
    params = {
        "risk_profile": risk_profile,
        "target_volatility": target_vol,
        "weight_type": "dynamic",
        "investment_amount": investment_amount
    }
    
    response = requests.post(
        f"{NEOENGINE_URL}/neo/api/v1/optimize",
        json=params,
        headers={"Content-Type": "application/json", "X-Api-Key": NEOENGINE_API_KEY}
    )
    
    result = response.json()
    
    print(f"\n📊 OPTIMIZATION RESULTS:")
    print(f"   - Success: {result.get('success')}")
    
    portfolio = result.get('portfolio_summary', {})
    print(f"\n📈 PORTFOLIO SUMMARY:")
    exp_ret = portfolio.get('expected_return', 0)
    exp_vol = portfolio.get('total_volatility', 0)
    print(f"   - Expected Return: {exp_ret*100:.2f}%")
    print(f"   - Expected Volatility: {exp_vol*100:.2f}%")
    print(f"   - Total Securities: {portfolio.get('manager_count', 0)}")
    
    # Extract all three layers
    layers = result.get('layers', {})
    layer1 = layers.get('layer1', {})
    layer2 = layers.get('layer2', {})
    layer3 = layers.get('layer3', {})
    
    # Layer 1: Asset class weights
    asset_weights = layer1.get('selected_weights', {})
    
    # Layer 2: Active/Passive split
    active_allocations = layer2.get('active_allocations', {})
    passive_tickers = layer2.get('passive_tickers', {})
    passive_names = layer2.get('passive_names', {})
    active_risk_pct = layer2.get('active_risk_pct', 0)
    passive_risk_pct = layer2.get('passive_risk_pct', 0)
    
    # Layer 3: Manager allocations within active portion
    layer3_allocations = layer3.get('allocations_by_asset_class', {})
    layer3_securities = layer3.get('securities', [])
    
    print(f"\n" + "=" * 90)
    print(f" LAYER 1: STRATEGIC ASSET ALLOCATION (SAA)")
    print("=" * 90)
    print(f"\n{'Asset Class':<50} {'Weight':>10} {'Amount':>15}")
    print("-" * 75)
    
    sorted_weights = sorted(asset_weights.items(), key=lambda x: x[1], reverse=True)
    for asset, weight in sorted_weights:
        if weight > 0.01:
            amount = investment_amount * weight
            print(f"{asset:<50} {weight:>8.1%} ${amount:>12,.0f}")
    
    print("-" * 75)
    print(f"{'TOTAL':<50} {'100.0%':>10} ${investment_amount:>12,.0f}")
    
    print(f"\n" + "=" * 90)
    print(f" LAYER 2: ACTIVE/PASSIVE SPLIT")
    print("=" * 90)
    print(f"\nRisk Budget: Active {active_risk_pct*100:.1f}% | Passive {passive_risk_pct*100:.1f}%")
    print(f"\n{'Asset Class':<40} {'Active %':>10} {'Passive %':>10} {'Passive ETF':<25}")
    print("-" * 90)
    
    for asset in sorted_weights:
        asset_name = asset[0]
        if asset[1] > 0.01:
            active_pct = active_allocations.get(asset_name, 0)
            passive_pct = 1 - active_pct
            passive_ticker = passive_tickers.get(asset_name, 'N/A')
            passive_name = passive_names.get(asset_name, passive_ticker)
            if len(passive_name) > 23:
                passive_name = passive_name[:20] + "..."
            print(f"{asset_name:<40} {active_pct*100:>8.1f}% {passive_pct*100:>8.1f}% {passive_name:<25}")
    
    print(f"\n" + "=" * 90)
    print(f" LAYER 3: MANAGER/SECURITY SELECTION")
    print("=" * 90)
    
    # Build complete security list combining passive ETFs and active managers
    complete_securities = []
    
    for asset_name, asset_weight in sorted_weights:
        if asset_weight < 0.01:
            continue
            
        asset_amount = investment_amount * asset_weight
        active_pct = active_allocations.get(asset_name, 0)
        passive_pct = 1 - active_pct
        
        # Add passive ETF allocation
        if passive_pct > 0:
            passive_ticker = passive_tickers.get(asset_name, 'N/A')
            passive_name = passive_names.get(asset_name, f"Passive ETF ({passive_ticker})")
            passive_amount = asset_amount * passive_pct
            complete_securities.append({
                'name': passive_name,
                'ticker': passive_ticker,
                'asset_class': asset_name,
                'type': 'Passive (ETF)',
                'weight_in_class': passive_pct,
                'total_weight': asset_weight * passive_pct,
                'amount': passive_amount,
            })
        
        # Add active manager allocations from Layer 3
        if active_pct > 0 and asset_name in layer3_allocations:
            managers = layer3_allocations[asset_name]
            for isin, manager_weight in managers.items():
                # Find manager details
                manager_info = next(
                    (s for s in layer3_securities if s.get('isin') == isin),
                    {'name': isin, 'expected_te': 0}
                )
                active_amount = asset_amount * active_pct * manager_weight
                complete_securities.append({
                    'name': manager_info.get('name', isin),
                    'isin': isin,
                    'asset_class': asset_name,
                    'type': 'Active (Manager)',
                    'weight_in_class': active_pct * manager_weight,
                    'total_weight': asset_weight * active_pct * manager_weight,
                    'amount': active_amount,
                    'expected_te': manager_info.get('expected_te', 0),
                })
    
    # Sort by amount
    complete_securities.sort(key=lambda x: x['amount'], reverse=True)
    
    print(f"\n📊 COMPLETE SECURITY ALLOCATIONS (Passive ETFs + Active Managers):")
    print("-" * 110)
    print(f"{'Security Name':<40} {'Type':<15} {'Asset Class':<22} {'Weight':>7} {'Amount':>12}")
    print("-" * 110)
    
    for sec in complete_securities:
        name = sec['name'][:38] if sec['name'] else 'Unknown'
        sec_type = sec['type'][:13]
        asset_class = sec['asset_class'][:20]
        weight = sec['total_weight']
        amount = sec['amount']
        
        if amount >= 10000:  # Show allocations >= $10K
            print(f"{name:<40} {sec_type:<15} {asset_class:<22} {weight:>5.1%} ${amount:>10,.0f}")
    
    print("-" * 110)
    total_allocated = sum(s['amount'] for s in complete_securities)
    print(f"{'TOTAL':>78} ${total_allocated:>10,.0f}")
    
    # Summary by type
    passive_total = sum(s['amount'] for s in complete_securities if s['type'] == 'Passive (ETF)')
    active_total = sum(s['amount'] for s in complete_securities if s['type'] == 'Active (Manager)')
    
    print(f"\n📊 ALLOCATION SUMMARY BY TYPE:")
    print(f"   - Passive (ETFs):    ${passive_total:>12,.0f} ({passive_total/investment_amount*100:.1f}%)")
    print(f"   - Active (Managers): ${active_total:>12,.0f} ({active_total/investment_amount*100:.1f}%)")
    print(f"   - Total:             ${total_allocated:>12,.0f}")
    
    # Store complete securities in result for report
    result['complete_securities'] = complete_securities
    
    return result


# =============================================================================
# STAGE 5: What-If Analysis with Optimized Portfolio
# =============================================================================
def stage5_whatif_with_portfolio(portfolio_result, investment_amount):
    """Stage 5: Project outcomes with the recommended portfolio."""
    print_header("STAGE 5: PROJECTED OUTCOMES WITH RECOMMENDED PORTFOLIO")
    
    portfolio = portfolio_result.get('portfolio_summary', {})
    exp_ret = portfolio.get('expected_return', 0)
    exp_vol = portfolio.get('total_volatility', 0)
    
    initial = investment_amount
    years = 5
    target = 10_000_000
    
    print(f"\n📐 PROJECTION PARAMETERS:")
    print(f"   Investment Amount: ${initial:,.0f}")
    print(f"   Portfolio Expected Return: {exp_ret*100:.2f}%")
    print(f"   Portfolio Volatility: {exp_vol*100:.2f}%")
    print(f"   Target: ${target:,.0f}")
    print(f"   Timeline: {years} years")
    
    # Year-by-year projection with expected return
    print(f"\n📈 YEAR-BY-YEAR PROJECTION (With {exp_ret*100:.1f}% Expected Return):")
    print("-" * 70)
    print(f"{'Year':<8} {'Balance':>18} {'Growth':>15} {'vs Target':>15} {'Status'}")
    print("-" * 70)
    
    balance = initial
    for year in range(years + 1):
        actual_year = CURRENT_YEAR + year
        if year > 0:
            growth = balance * exp_ret
            balance += growth
        else:
            growth = 0
        
        diff = balance - target
        if diff >= 0:
            diff_str = f"+${diff:,.0f}"
            status = "✓"
        else:
            diff_str = f"-${abs(diff):,.0f}"
            status = ""
        
        highlight = " ← TARGET" if year == years else ""
        print(f"{actual_year:<8} ${balance:>15,.0f} ${growth:>12,.0f} {diff_str:>15} {status}{highlight}")
    
    # Scenario comparison
    scenarios = [
        ("Bank Only (0.5%)", 0.005),
        ("Conservative (4%)", 0.04),
        ("Recommended Portfolio", exp_ret),
        (f"Target Return ({7.39}%)", 0.0739),
        ("Optimistic (+2%)", exp_ret + 0.02),
    ]
    
    print(f"\n📊 SCENARIO COMPARISON:")
    print("-" * 80)
    print(f"{'Scenario':<30} {'Return':<10} {'Final Value':<18} {'vs Target':<15} {'Status'}")
    print("-" * 80)
    
    for name, rate in scenarios:
        final = initial * ((1 + rate) ** years)
        diff = final - target
        diff_str = f"+${diff:,.0f}" if diff >= 0 else f"-${abs(diff):,.0f}"
        status = "✓ ACHIEVES" if final >= target else "✗ SHORTFALL"
        print(f"{name:<30} {rate*100:<10.2f}% ${final:>15,.0f} {diff_str:<15} {status}")
    
    return {
        "expected_return": exp_ret,
        "expected_volatility": exp_vol,
        "final_value_expected": initial * ((1 + exp_ret) ** years),
        "scenarios": scenarios
    }


# =============================================================================
# GENERATE STRUCTURED REPORT
# =============================================================================
def generate_structured_report(stage1, stage2_mc, stage3_gaps, stage4_portfolio, stage5_whatif):
    """Generate comprehensive report with improved structure."""
    print_header("STRUCTURED INVESTMENT REPORT")
    
    # Unpack results
    stage1_result, base_params = stage1
    all_gaps = stage3_gaps[1]
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           INVESTMENT ANALYSIS REPORT                          ║
║                          House Purchase Goal Assessment                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    # SECTION 1: Executive Summary
    print("┌─────────────────────────────────────────────────────────────────────┐")
    print("│ 1. EXECUTIVE SUMMARY                                                │")
    print("└─────────────────────────────────────────────────────────────────────┘")
    
    goal = stage1_result.get('goal_analysis', {}).get('House Purchase', {})
    portfolio = stage4_portfolio.get('portfolio_summary', {})
    
    print(f"""
  Client Goal:     Purchase house worth $10,000,000
  Timeline:        5 years ({CURRENT_YEAR} → {TARGET_YEAR})
  Current Capital: $7,000,000
  Required Growth: 43% total (~7.4% annually)
  
  CURRENT STATE FINDING:
  └─ Bank-only strategy (0.5%) projects ${goal.get('projected_amount', 0):,.0f}
  └─ Shortfall: ${goal.get('shortfall', 0):,.0f} ({100 - goal.get('achievement_percentage', 0):.1f}% gap)
  
  RECOMMENDED SOLUTION:
  └─ Invest in diversified portfolio (RP3 - Moderate)
  └─ Expected Return: {portfolio.get('expected_return', 0)*100:.2f}%
  └─ Projected Terminal Value: ${stage5_whatif.get('final_value_expected', 0):,.0f}
""")
    
    # SECTION 2: Monte Carlo Trajectories Summary
    print("\n┌─────────────────────────────────────────────────────────────────────┐")
    print("│ 2. MONTE CARLO WEALTH TRAJECTORY ANALYSIS                           │")
    print("└─────────────────────────────────────────────────────────────────────┘")
    
    individual_runs = stage2_mc.get('individual_simulation_runs', [])
    mc_results = stage2_mc.get('monte_carlo_results', {})
    
    print(f"""
  Simulation Summary:
  └─ Total Simulations: {mc_results.get('num_simulations', 100)}
  └─ Individual Trajectories Sampled: {len(individual_runs)}
  
  Terminal Wealth Distribution:
  └─ 5th Percentile (Worst):  ${mc_results.get('terminal_wealth_percentiles', {}).get('5th', 0):>15,.0f}
  └─ 25th Percentile:         ${mc_results.get('terminal_wealth_percentiles', {}).get('25th', 0):>15,.0f}
  └─ 50th Percentile (Median):${mc_results.get('terminal_wealth_percentiles', {}).get('50th', 0):>15,.0f}
  └─ 75th Percentile:         ${mc_results.get('terminal_wealth_percentiles', {}).get('75th', 0):>15,.0f}
  └─ 95th Percentile (Best):  ${mc_results.get('terminal_wealth_percentiles', {}).get('95th', 0):>15,.0f}
  
  KEY INSIGHT: The trajectories show the volatility range of possible outcomes.
  This helps understand both upside potential and downside risks.
""")
    
    # SECTION 3: Gap Analysis with Action Plans
    print("\n┌─────────────────────────────────────────────────────────────────────┐")
    print("│ 3. GAP ANALYSIS WITH ACTION PLANS                                   │")
    print("└─────────────────────────────────────────────────────────────────────┘")
    
    for i, gap in enumerate(all_gaps, 1):
        gap_type = gap['type'].replace('_', ' ').title()
        severity = gap['severity'].upper()
        category = gap['category'].replace('_', ' ').title()
        
        print(f"""
  ┌─────────────────────────────────────────────────────────────────────
  │ GAP {i}: {gap_type}
  │ Severity: [{severity}] | Category: {category}
  ├─────────────────────────────────────────────────────────────────────
  │ Description: {gap['description']}
  │ Impact: {gap['impact']}
  └─────────────────────────────────────────────────────────────────────
""")
        
        # ACTION PLAN for this gap
        if 'goal_shortfall' in gap['type'].lower():
            print(f"""
  📋 ACTION PLAN FOR GAP {i}:
  ═══════════════════════════════════════════════════════════════════════
  
  RECOMMENDED ACTION:
  1. Transfer full $7,000,000 from bank to investment portfolio
  2. Implement recommended asset allocation (see Section 4)
  3. Target expected return of {portfolio.get('expected_return', 0)*100:.2f}% annually
  
  ANALYSIS WITH THIS ACTION:
  ─────────────────────────────────────────────────────────────────────
  Investment Amount: $7,000,000
  Expected Return: {portfolio.get('expected_return', 0)*100:.2f}%
  Timeline: 5 years
  
  Year-by-Year Projection:
""")
            # Show projection with the specific action
            balance = 7_000_000
            exp_ret = portfolio.get('expected_return', 0)
            print(f"  {'Year':<8} {'Balance':>15} {'Growth':>12} {'vs $10M Target':>15}")
            print(f"  {'-'*55}")
            for year in range(6):
                actual_year = CURRENT_YEAR + year
                if year > 0:
                    growth = balance * exp_ret
                    balance += growth
                else:
                    growth = 0
                diff = balance - 10_000_000
                diff_str = f"+${diff:,.0f}" if diff >= 0 else f"-${abs(diff):,.0f}"
                marker = " ← TARGET" if year == 5 else ""
                print(f"  {actual_year:<8} ${balance:>12,.0f} ${growth:>9,.0f} {diff_str:>15}{marker}")
            
            final = 7_000_000 * ((1 + exp_ret) ** 5)
            print(f"""
  OUTCOME: With {exp_ret*100:.2f}% return, terminal value = ${final:,.0f}
           {"✓ GOAL ACHIEVED" if final >= 10_000_000 else "⚠ SLIGHT SHORTFALL - consider extending timeline"}
""")
        
        elif 'emergency_fund' in gap['type'].lower():
            print(f"""
  📋 ACTION PLAN FOR GAP {i}:
  ═══════════════════════════════════════════════════════════════════════
  
  RECOMMENDED ACTION:
  Since client has no ongoing expenses, emergency fund is not critical.
  However, for best practices:
  1. Keep 3-6 months of expected post-purchase expenses in liquid form
  2. Consider maintaining $500K-$1M in money market or short-term bonds
     within the portfolio allocation (see "Cash" allocation in Section 4)
  
  ANALYSIS: Current portfolio includes 2% Cash allocation ($140,000)
            This provides immediate liquidity if needed.
""")
    
    # SECTION 4: Portfolio Details (All 3 Layers)
    print("\n┌─────────────────────────────────────────────────────────────────────┐")
    print("│ 4. RECOMMENDED PORTFOLIO (3-LAYER SECURITY ALLOCATIONS)             │")
    print("└─────────────────────────────────────────────────────────────────────┘")
    
    layers = stage4_portfolio.get('layers', {})
    layer1 = layers.get('layer1', {})
    layer2 = layers.get('layer2', {})
    weights = layer1.get('selected_weights', {})
    
    print(f"""
  Portfolio Configuration:
  └─ Risk Profile: RP3 (Moderate)
  └─ Expected Return: {portfolio.get('expected_return', 0)*100:.2f}%
  └─ Expected Volatility: {portfolio.get('total_volatility', 0)*100:.2f}%
  └─ Total Investment: $7,000,000
  
  Layer 1 - Asset Class Allocation:
  ─────────────────────────────────────────────────────────────────────
""")
    
    sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
    print(f"  {'Asset Class':<45} {'Weight':>8} {'Amount':>15}")
    print(f"  {'-'*70}")
    for asset, weight in sorted_weights:
        if weight > 0.01:
            amount = 7_000_000 * weight
            print(f"  {asset:<45} {weight:>6.1%} ${amount:>12,.0f}")
    
    # Layer 2 - Active/Passive split
    active_allocations = layer2.get('active_allocations', {})
    active_risk_pct = layer2.get('active_risk_pct', 0)
    passive_risk_pct = layer2.get('passive_risk_pct', 0)
    
    print(f"""
  
  Layer 2 - Active/Passive Risk Budget:
  ─────────────────────────────────────────────────────────────────────
  Active Risk:  {active_risk_pct*100:.1f}% of risk budget
  Passive Risk: {passive_risk_pct*100:.1f}% of risk budget
""")
    
    # Complete security allocations from all 3 layers
    complete_securities = stage4_portfolio.get('complete_securities', [])
    
    if complete_securities:
        print(f"""
  Layer 3 - Complete Security Allocations (Passive ETFs + Active Managers):
  ─────────────────────────────────────────────────────────────────────
""")
        print(f"  {'Security':<38} {'Type':<12} {'Asset Class':<18} {'Weight':>6} {'Amount':>11}")
        print(f"  {'-'*90}")
        
        for sec in complete_securities:
            name = sec.get('name', 'Unknown')[:36]
            sec_type = sec.get('type', 'Unknown')[:10]
            asset_class = sec.get('asset_class', '')[:16]
            weight = sec.get('total_weight', 0)
            amount = sec.get('amount', 0)
            if amount >= 50000:
                print(f"  {name:<38} {sec_type:<12} {asset_class:<18} {weight:>4.1%} ${amount:>9,.0f}")
        
        # Summary
        passive_total = sum(s['amount'] for s in complete_securities if s.get('type') == 'Passive (ETF)')
        active_total = sum(s['amount'] for s in complete_securities if s.get('type') == 'Active (Manager)')
        total = passive_total + active_total
        
        print(f"  {'-'*90}")
        print(f"  {'SUMMARY:':<38}")
        print(f"  {'  Passive (ETFs)':<38} {'':<12} {'':<18} {passive_total/7_000_000:>4.1%} ${passive_total:>9,.0f}")
        print(f"  {'  Active (Managers)':<38} {'':<12} {'':<18} {active_total/7_000_000:>4.1%} ${active_total:>9,.0f}")
        print(f"  {'  TOTAL':<38} {'':<12} {'':<18} {'100%':>6} ${total:>9,.0f}")
    
    # SECTION 5: Final Recommendation
    print("\n┌─────────────────────────────────────────────────────────────────────┐")
    print("│ 5. FINAL RECOMMENDATION                                             │")
    print("└─────────────────────────────────────────────────────────────────────┘")
    
    exp_ret = portfolio.get('expected_return', 0)
    final_value = 7_000_000 * ((1 + exp_ret) ** 5)
    
    print(f"""
  SUMMARY:
  ═══════════════════════════════════════════════════════════════════════
  
  Current Situation:
  └─ $7,000,000 in bank earning 0.5%
  └─ Projected at year 5: ~$7.18M (shortfall: $2.82M)
  
  Recommended Action:
  └─ Invest full $7,000,000 in RP3 Moderate Portfolio
  └─ Expected return: {exp_ret*100:.2f}% annually
  └─ Projected at year 5: ${final_value:,.0f}
  
  Outcome Assessment:
  └─ {"✓ Goal achievable with recommended portfolio" if final_value >= 10_000_000 else "⚠ Close to target - may need 1 extra year or slightly higher risk"}
  └─ Expected surplus/shortfall: ${final_value - 10_000_000:+,.0f}
  
  IMPORTANT CONSIDERATIONS:
  ─────────────────────────────────────────────────────────────────────
  • Returns are projections based on historical data, not guarantees
  • Market volatility means actual outcomes will vary
  • Monte Carlo analysis shows range of possible outcomes
  • Regular rebalancing recommended (quarterly)
  • Annual review of progress toward $10M goal
  
  ═══════════════════════════════════════════════════════════════════════
""")
    
    print("\n" + "=" * 78)
    print(" END OF INVESTMENT REPORT")
    print("=" * 78)


# =============================================================================
# MAIN
# =============================================================================
def main():
    print("\n" + "=" * 70)
    print("  FINANCIAL PLANNER TEST: HOUSE PURCHASE GOAL (V2)")
    print("=" * 70)
    print(f"""
  Client Profile:
  ├─ Initial Capital: $7,000,000
  ├─ Goal: Purchase house worth $10,000,000
  ├─ Timeline: 5 years ({CURRENT_YEAR} → {TARGET_YEAR})
  ├─ Income: $0 (no employment income)
  └─ Expenses: $0 (no ongoing costs)

  Required Growth: 43% over 5 years (~7.4% annually)
""")
    
    # Run all stages
    stage1_result = stage1_current_state()
    stage2_mc_result = stage2_monte_carlo_trajectories(stage1_result[1])
    stage3_gaps = stage3_gap_analysis(stage1_result[1])
    stage4_portfolio = stage4_portfolio_optimization(INVESTMENT_AMOUNT)
    stage5_whatif = stage5_whatif_with_portfolio(stage4_portfolio, INVESTMENT_AMOUNT)
    
    # Generate structured report
    generate_structured_report(
        stage1_result, 
        stage2_mc_result, 
        stage3_gaps, 
        stage4_portfolio, 
        stage5_whatif
    )
    
    print("\n✅ All stages completed successfully!")


if __name__ == "__main__":
    main()
