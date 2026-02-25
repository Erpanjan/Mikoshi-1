#!/usr/bin/env python3
"""
Test script to demonstrate the Financial Planner Agent workflow.

This script simulates what the agent would do:
1. Run cashflow simulation to understand client trajectory
2. Analyze gaps using the gap analysis API
3. Call NeoEngine to optimize portfolio
4. Show how the solution addresses the gaps

Usage:
    python3 test-agent-flow.py
"""

import json
import requests

# Configuration
CASHFLOW_URL = "http://localhost:8001"
NEOENGINE_URL = "http://localhost:8000"
NEOENGINE_API_KEY = "8c8c612b37eea10e13c46a3ced0fd0b86ad1024e5e88d0dc007b23f93cced897"

# Test client data - Sarah Chen
CLIENT_DATA = {
    "client_profile": {
        "name": "Sarah Chen",
        "age": 32,
        "retirement_age": 60,
        "life_expectancy": 90
    },
    "accounts": {
        "bank": {"balance": 25000},
        "brokerage": {"balance": 50000},
        "401k": {"pretax_balance": 80000, "contrib_percent": 8, "company_match_percent": 4},
        "ira": {"balance": 20000, "type": "roth"}
    },
    "income": {
        "salary": 120000,
        "yearly_increase": 3.0
    },
    "expenses": {
        "base_spending": 72000,
        "yearly_increase": 3.0,
        "housing": {"type": "rent", "monthly_rent": 2500}
    },
    "goals": [
        {"name": "Child College Fund", "target_amount": 80000, "target_year": 2039},
        {"name": "Retirement", "target_amount": 2000000, "target_year": 2054}
    ],
    "asset_allocation": {},  # No current allocation specified
    "has_disability_insurance": False,
    "has_life_insurance": True,
    "life_insurance_coverage": 200000,
    "simulation_config": {
        "mode": "deterministic"
    }
}


def print_header(title):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def step1_analyze_current_situation():
    """Step 1: Run gap analysis to understand the client's situation."""
    print_header("STEP 1: Analyzing Client's Current Situation")
    
    response = requests.post(
        f"{CASHFLOW_URL}/cashflow/api/v1/gap-analysis",
        json=CLIENT_DATA,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return None
    
    result = response.json()
    
    # Print summary
    print(f"\n📊 Simulation Summary:")
    print(f"   - Years simulated: {result['projection_summary']['years_simulated']}")
    print(f"   - Retirement year: {result['projection_summary']['retirement_year']}")
    print(f"   - Terminal wealth: ${result['projection_summary']['terminal_wealth']:,.0f}")
    
    print(f"\n📋 Gaps Identified: {result['gap_summary']['total_gaps']}")
    print(f"   - Investment solvable: {result['gap_summary']['investment_solvable_count']}")
    print(f"   - Behavior solvable: {result['gap_summary']['behavior_solvable_count']}")
    print(f"   - Requires other solutions: {result['gap_summary']['requires_other_solutions_count']}")
    
    # Print investment-solvable gaps
    print("\n🎯 Investment-Solvable Gaps:")
    for gap in result['gaps_identified']['investment_solvable']:
        print(f"\n   [{gap['severity'].upper()}] {gap['type']}")
        print(f"   Description: {gap['description']}")
        print(f"   Impact: {gap['quantified_impact']}")
    
    # Print behavior-solvable gaps
    print("\n💰 Behavior-Solvable Gaps:")
    for gap in result['gaps_identified']['behavior_solvable'][:3]:  # Top 3
        print(f"\n   [{gap['severity'].upper()}] {gap['type']}")
        print(f"   Description: {gap['description']}")
    
    # Print other solutions needed
    print("\n🛡️ Requires Other Solutions:")
    for gap in result['gaps_identified']['requires_other_solutions']:
        print(f"\n   [{gap['severity'].upper()}] {gap['type']}")
        print(f"   Description: {gap['description']}")
        print(f"   Recommendation: {gap.get('recommendation', 'N/A')}")
    
    return result


def step2_determine_risk_profile(gap_result):
    """Step 2: Determine appropriate risk profile based on analysis."""
    print_header("STEP 2: Determining Risk Profile")
    
    # Agent reasoning (simulated)
    client_age = 32
    retirement_age = 60
    years_to_retirement = retirement_age - client_age
    
    print(f"\n🤔 Agent Reasoning:")
    print(f"   - Client age: {client_age}")
    print(f"   - Years to retirement: {years_to_retirement}")
    print(f"   - Current allocation: No equity (too conservative)")
    print(f"   - Gap severity: Critical shortfalls detected")
    
    # Determine risk profile
    if years_to_retirement > 25:
        risk_profile = "RP4"  # Aggressive
        reason = "Long time horizon allows for higher risk tolerance"
    elif years_to_retirement > 15:
        risk_profile = "RP3"  # Moderate
        reason = "Medium time horizon suggests balanced approach"
    else:
        risk_profile = "RP2"  # Conservative
        reason = "Shorter time horizon requires capital preservation"
    
    print(f"\n✅ Selected Risk Profile: {risk_profile}")
    print(f"   Reason: {reason}")
    
    return risk_profile


def step3_optimize_portfolio(risk_profile):
    """Step 3: Call NeoEngine to optimize portfolio."""
    print_header("STEP 3: Optimizing Portfolio via NeoEngine")
    
    volatility_map = {
        "RP1": 0.0525, "RP2": 0.0776, "RP3": 0.1007, 
        "RP4": 0.1230, "RP5": 0.1447
    }
    
    params = {
        "risk_profile": risk_profile,
        "target_volatility": volatility_map[risk_profile],
        "weight_type": "dynamic"
    }
    
    print(f"\n📤 Calling NeoEngine with:")
    print(f"   - Risk Profile: {params['risk_profile']}")
    print(f"   - Target Volatility: {params['target_volatility']:.2%}")
    
    response = requests.post(
        f"{NEOENGINE_URL}/neo/api/v1/optimize",
        json=params,
        headers={
            "Content-Type": "application/json",
            "X-Api-Key": NEOENGINE_API_KEY
        }
    )
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return None
    
    result = response.json()
    
    # Print portfolio allocation
    print(f"\n📊 Optimized Portfolio Allocation:")
    
    weights = result['layers']['layer1']['selected_weights']
    sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
    
    for asset, weight in sorted_weights[:10]:  # Top 10
        if weight > 0.01:  # Only show >1%
            print(f"   {asset}: {weight:.1%}")
    
    print(f"\n📈 Portfolio Metrics:")
    print(f"   - Expected Volatility: {result['portfolio_summary']['total_volatility']:.2%}")
    sharpe = result['portfolio_summary'].get('sharpe_ratio', 'N/A')
    if sharpe != 'N/A':
        print(f"   - Sharpe Ratio: {sharpe:.2f}")
    else:
        print(f"   - Sharpe Ratio: {sharpe}")
    
    return result


def step4_generate_investment_plan(gap_result, portfolio_result, risk_profile):
    """Step 4: Generate the investment plan with WHY rationale."""
    print_header("STEP 4: Investment Plan with WHY Rationale")
    
    print("\n" + "─" * 60)
    print("📄 INVESTMENT PLAN FOR SARAH CHEN")
    print("─" * 60)
    
    print("\n📝 EXECUTIVE SUMMARY")
    print("-" * 40)
    print("""
    Based on comprehensive analysis, Sarah's current financial trajectory
    shows significant gaps in achieving her goals. With 28 years until
    retirement and no current equity allocation, implementing an optimized
    investment strategy is critical.
    """)
    
    print("\n🔍 GAP ANALYSIS SUMMARY")
    print("-" * 40)
    
    # Investment gaps
    print("\n  INVESTMENT-SOLVABLE GAPS:")
    for gap in gap_result['gaps_identified']['investment_solvable']:
        print(f"\n    ❌ {gap['type'].replace('_', ' ').title()}")
        print(f"       WHY it's a problem: {gap['description']}")
        print(f"       HOW portfolio helps: {gap.get('potential_improvement', 'Improved returns')}")
    
    print("\n💼 RECOMMENDED PORTFOLIO")
    print("-" * 40)
    print(f"    Risk Profile: {risk_profile}")
    
    weights = portfolio_result['layers']['layer1']['selected_weights']
    equity_total = sum(w for a, w in weights.items() 
                       if 'Equity' in a or 'equity' in a.lower())
    fixed_income_total = sum(w for a, w in weights.items() 
                             if 'Bond' in a or 'Treasury' in a or 'Fixed Income' in a)
    
    print(f"    Equity: ~{equity_total:.0%}")
    print(f"    Fixed Income: ~{fixed_income_total:.0%}")
    print(f"    Alternatives: ~{1 - equity_total - fixed_income_total:.0%}")
    
    print("\n    WHY THIS ALLOCATION:")
    print(f"""
    1. Higher equity exposure ({equity_total:.0%}) addresses the current 0% allocation
       which is too conservative for a 28-year horizon
    
    2. Diversified across developed and emerging markets reduces concentration risk
       while capturing global growth opportunities
    
    3. Alternative investments (Gold, Bitcoin, Hedge Funds) provide inflation
       protection and uncorrelated returns
    """)
    
    print("\n📋 ACTION PLAN")
    print("-" * 40)
    
    actions = [
        {
            "when": "Immediately",
            "what": "Increase 401k contribution from 8% to 15%",
            "why": "Current savings rate is below recommended minimum; company match maximizes benefit"
        },
        {
            "when": "Within 30 days",
            "what": f"Rebalance brokerage account to {risk_profile} allocation",
            "why": "Current 0% equity allocation is too conservative for 28-year horizon"
        },
        {
            "when": "Within 60 days",
            "what": "Start monthly contributions to 529 plan for college fund",
            "why": "13 years to goal requires consistent contributions; tax advantages"
        },
        {
            "when": "Quarterly",
            "what": "Review and rebalance portfolio",
            "why": "Maintain target allocation as market moves"
        }
    ]
    
    for i, action in enumerate(actions, 1):
        print(f"\n    Step {i}: {action['when']}")
        print(f"    WHAT: {action['what']}")
        print(f"    WHY:  {action['why']}")
    
    print("\n⚠️ ADDITIONAL RECOMMENDATIONS")
    print("-" * 40)
    
    for gap in gap_result['gaps_identified']['requires_other_solutions']:
        print(f"\n    🛡️ {gap['solution_type'].replace('_', ' ').title()}")
        print(f"       Issue: {gap['description']}")
        print(f"       Action: {gap.get('recommendation', 'Consult insurance specialist')}")
    
    print("\n" + "─" * 60)
    print("End of Investment Plan")
    print("─" * 60)


def main():
    """Run the complete agent workflow demonstration."""
    print("\n" + "=" * 60)
    print("  FINANCIAL PLANNER AGENT - WORKFLOW DEMONSTRATION")
    print("=" * 60)
    print("\nClient: Sarah Chen, Age 32, Retirement at 60")
    print("Goals: Child College Fund ($80k), Retirement ($2M)")
    
    # Step 1: Analyze current situation
    gap_result = step1_analyze_current_situation()
    if not gap_result:
        print("\n❌ Failed to analyze client situation")
        return
    
    # Step 2: Determine risk profile
    risk_profile = step2_determine_risk_profile(gap_result)
    
    # Step 3: Optimize portfolio
    portfolio_result = step3_optimize_portfolio(risk_profile)
    if not portfolio_result:
        print("\n❌ Failed to optimize portfolio")
        return
    
    # Step 4: Generate investment plan
    step4_generate_investment_plan(gap_result, portfolio_result, risk_profile)
    
    print("\n✅ Agent workflow completed successfully!")
    print("\nNote: In the full agent, Gemini AI would orchestrate these steps")
    print("and provide more sophisticated reasoning and explanations.\n")


if __name__ == "__main__":
    main()
