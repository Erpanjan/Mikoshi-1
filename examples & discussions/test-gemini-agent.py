#!/usr/bin/env python3
"""
Test Gemini Agent with Tool Calling

This script demonstrates the full Financial Planner Agent workflow using
Gemini AI with function calling to orchestrate:
1. Cashflow Model API - for financial simulations and gap analysis
2. NeoEngine API - for portfolio optimization

Usage:
    python3 test-gemini-agent.py
"""

import os
import json
import requests
from google import genai
from google.genai import types

# Load API key from .env or environment
GEMINI_API_KEY = os.environ.get('GOOGLE_GENAI_API_KEY') or "AIzaSyCIBK7uweadnb1oTnMVes4bTFA7EvjeXSY"
CASHFLOW_URL = "http://localhost:8001"
NEOENGINE_URL = "http://localhost:8000"
NEOENGINE_API_KEY = "8c8c612b37eea10e13c46a3ced0fd0b86ad1024e5e88d0dc007b23f93cced897"

# Initialize Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

# Define tools for Gemini
TOOLS = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="runCashflowSimulation",
                description="""Run a multi-year cashflow simulation for financial planning.
                
This tool simulates a client's financial trajectory over time, projecting:
- Year-by-year income, expenses, and net worth
- Account balances (bank, brokerage, 401k, IRA)
- Goal achievement likelihood
- Financial gaps and risks

Use this tool to:
1. Understand the client's current financial trajectory
2. Identify gaps between projected outcomes and goals
3. Analyze year-by-year patterns to find root causes of issues

The simulation can run in deterministic mode (single path) or monte_carlo mode (risk analysis).
""",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "client_age": types.Schema(type=types.Type.INTEGER, description="Client's current age"),
                        "retirement_age": types.Schema(type=types.Type.INTEGER, description="Target retirement age"),
                        "annual_income": types.Schema(type=types.Type.NUMBER, description="Annual salary income"),
                        "annual_expenses": types.Schema(type=types.Type.NUMBER, description="Annual expenses"),
                        "bank_balance": types.Schema(type=types.Type.NUMBER, description="Bank account balance"),
                        "investment_balance": types.Schema(type=types.Type.NUMBER, description="Brokerage account balance"),
                        "retirement_401k_balance": types.Schema(type=types.Type.NUMBER, description="401k balance"),
                        "retirement_401k_contrib_percent": types.Schema(type=types.Type.NUMBER, description="401k contribution %"),
                        "ira_balance": types.Schema(type=types.Type.NUMBER, description="IRA balance"),
                        "housing_type": types.Schema(type=types.Type.STRING, description="rent or own"),
                        "monthly_housing_cost": types.Schema(type=types.Type.NUMBER, description="Monthly rent/mortgage"),
                        "has_disability_insurance": types.Schema(type=types.Type.BOOLEAN, description="Has disability insurance"),
                        "has_life_insurance": types.Schema(type=types.Type.BOOLEAN, description="Has life insurance"),
                        "simulation_mode": types.Schema(type=types.Type.STRING, description="deterministic or monte_carlo"),
                    },
                    required=["client_age", "retirement_age", "annual_income", "annual_expenses"]
                )
            ),
            types.FunctionDeclaration(
                name="optimizePortfolio",
                description="""Optimize investment portfolio using NeoEngine 3-layer optimization.
                
This tool creates an optimized asset allocation based on:
- Risk profile (RP1 to RP5, conservative to aggressive)
- Target volatility
- Forward-looking Capital Market Assumptions

The optimization produces:
- Layer 1: Strategic Asset Allocation across 15 asset classes
- Layer 2: Active vs Passive allocation decisions
- Layer 3: Manager selection recommendations

Risk Profiles:
- RP1: Very conservative (5.25% vol) - retirees, very low risk tolerance
- RP2: Conservative (7.76% vol) - near-retirees, low risk tolerance
- RP3: Moderate (10.07% vol) - mid-career, moderate risk tolerance
- RP4: Aggressive (12.30% vol) - early career, high risk tolerance
- RP5: Very aggressive (14.47% vol) - young investors, very long horizon
""",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "risk_profile": types.Schema(type=types.Type.STRING, description="RP1-RP5"),
                        "target_volatility": types.Schema(type=types.Type.NUMBER, description="Target volatility"),
                    },
                    required=["risk_profile"]
                )
            )
        ]
    )
]

# Test client data
CLIENT_DATA = {
    "name": "Sarah Chen",
    "age": 32,
    "retirement_age": 60,
    "annual_income": 120000,
    "annual_expenses": 72000,
    "bank_balance": 25000,
    "investment_balance": 50000,
    "retirement_401k_balance": 80000,
    "retirement_401k_contrib_percent": 8,
    "company_match_percent": 4,
    "ira_balance": 20000,
    "housing_type": "rent",
    "monthly_housing_cost": 2500,
    "has_disability_insurance": False,
    "has_life_insurance": True,
    "life_insurance_coverage": 200000,
    "goals": [
        {"name": "Child College Fund", "amount": 80000, "year": 2039},
        {"name": "Retirement", "amount": 2000000, "year": 2054}
    ]
}


def execute_cashflow_simulation(args):
    """Execute cashflow simulation via API."""
    print(f"\n  📊 Executing cashflow simulation...")
    
    params = {
        "client_profile": {
            "name": "Client",
            "age": args.get("client_age", 35),
            "retirement_age": args.get("retirement_age", 65),
            "life_expectancy": 90
        },
        "accounts": {
            "bank": {"balance": args.get("bank_balance", 0)},
            "brokerage": {"balance": args.get("investment_balance", 0)},
            "401k": {
                "pretax_balance": args.get("retirement_401k_balance", 0),
                "contrib_percent": args.get("retirement_401k_contrib_percent", 0),
                "company_match_percent": 4
            },
            "ira": {"balance": args.get("ira_balance", 0), "type": "roth"}
        },
        "income": {
            "salary": args.get("annual_income", 0),
            "yearly_increase": 3.0
        },
        "expenses": {
            "base_spending": args.get("annual_expenses", 0),
            "yearly_increase": 3.0,
            "housing": {
                "type": args.get("housing_type", "rent"),
                "monthly_rent": args.get("monthly_housing_cost", 0)
            }
        },
        "goals": [],
        "asset_allocation": {},
        "has_disability_insurance": args.get("has_disability_insurance", False),
        "has_life_insurance": args.get("has_life_insurance", False),
        "simulation_config": {
            "mode": args.get("simulation_mode", "deterministic")
        }
    }
    
    response = requests.post(
        f"{CASHFLOW_URL}/cashflow/api/v1/gap-analysis",
        json=params,
        headers={"Content-Type": "application/json"},
        timeout=60
    )
    
    if response.status_code != 200:
        return {"error": response.text}
    
    result = response.json()
    
    # Summarize for the model
    summary = {
        "success": True,
        "projection_summary": result.get("projection_summary", {}),
        "gap_summary": result.get("gap_summary", {}),
        "investment_solvable_gaps": [
            {
                "type": g["type"],
                "description": g["description"],
                "severity": g["severity"],
                "impact": g.get("quantified_impact", "")
            }
            for g in result.get("gaps_identified", {}).get("investment_solvable", [])
        ],
        "behavior_solvable_gaps": [
            {
                "type": g["type"],
                "description": g["description"],
                "severity": g["severity"]
            }
            for g in result.get("gaps_identified", {}).get("behavior_solvable", [])[:3]
        ],
        "protection_gaps": result.get("gaps_identified", {}).get("requires_other_solutions", [])
    }
    
    print(f"  ✅ Found {summary['gap_summary'].get('total_gaps', 0)} gaps")
    return summary


def execute_portfolio_optimization(args):
    """Execute portfolio optimization via NeoEngine API."""
    print(f"\n  📈 Executing portfolio optimization (Risk Profile: {args.get('risk_profile')})...")
    
    vol_map = {"RP1": 0.0525, "RP2": 0.0776, "RP3": 0.1007, "RP4": 0.1230, "RP5": 0.1447}
    risk_profile = args.get("risk_profile", "RP3")
    
    params = {
        "risk_profile": risk_profile,
        "target_volatility": args.get("target_volatility", vol_map.get(risk_profile, 0.1)),
        "weight_type": "dynamic"
    }
    
    response = requests.post(
        f"{NEOENGINE_URL}/neo/api/v1/optimize",
        json=params,
        headers={
            "Content-Type": "application/json",
            "X-Api-Key": NEOENGINE_API_KEY
        },
        timeout=60
    )
    
    if response.status_code != 200:
        return {"error": response.text}
    
    result = response.json()
    
    # Summarize allocation
    weights = result.get("layers", {}).get("layer1", {}).get("selected_weights", {})
    sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
    
    summary = {
        "success": True,
        "risk_profile": risk_profile,
        "target_volatility": params["target_volatility"],
        "achieved_volatility": result.get("portfolio_summary", {}).get("total_volatility", 0),
        "top_allocations": {k: f"{v:.1%}" for k, v in sorted_weights[:8] if v > 0.01},
        "equity_total": sum(v for k, v in weights.items() if "Equity" in k or "equity" in k.lower()),
        "fixed_income_total": sum(v for k, v in weights.items() if "Bond" in k or "Treasury" in k)
    }
    
    print(f"  ✅ Portfolio optimized: {summary['equity_total']:.0%} equity, {summary['fixed_income_total']:.0%} fixed income")
    return summary


def execute_function(name, args):
    """Execute a function call from Gemini."""
    if name == "runCashflowSimulation":
        return execute_cashflow_simulation(args)
    elif name == "optimizePortfolio":
        return execute_portfolio_optimization(args)
    else:
        return {"error": f"Unknown function: {name}"}


def run_agent():
    """Run the Gemini agent with tool calling."""
    print("\n" + "=" * 60)
    print("  GEMINI FINANCIAL PLANNER AGENT")
    print("=" * 60)
    
    # System instruction for the agent
    system_instruction = """You are an expert Financial Planner Agent. Your job is to:
1. Analyze a client's financial situation using the cashflow simulation tool
2. Identify and categorize financial gaps
3. Propose optimized investment solutions using the portfolio optimization tool
4. Explain WHY each recommendation addresses specific gaps

IMPORTANT: 
- ALWAYS run the cashflow simulation first to understand the client's situation
- After seeing the gaps, determine the appropriate risk profile based on time horizon
- Call the portfolio optimization tool with the chosen risk profile
- Provide a final summary explaining how the solution addresses the gaps

For risk profile selection:
- 25+ years to retirement → RP4 or RP5
- 15-25 years → RP3
- 10-15 years → RP2
- <10 years → RP1
"""

    # Initial prompt
    user_prompt = f"""Analyze this client's financial situation and create an investment plan:

Client: {CLIENT_DATA['name']}, Age {CLIENT_DATA['age']}
- Retirement goal: Age {CLIENT_DATA['retirement_age']}
- Annual income: ${CLIENT_DATA['annual_income']:,}
- Annual expenses: ${CLIENT_DATA['annual_expenses']:,}
- Bank balance: ${CLIENT_DATA['bank_balance']:,}
- Investment balance: ${CLIENT_DATA['investment_balance']:,}
- 401k balance: ${CLIENT_DATA['retirement_401k_balance']:,} (contributing {CLIENT_DATA['retirement_401k_contrib_percent']}%)
- IRA balance: ${CLIENT_DATA['ira_balance']:,}
- Housing: {CLIENT_DATA['housing_type']}, ${CLIENT_DATA['monthly_housing_cost']}/month
- Has disability insurance: {CLIENT_DATA['has_disability_insurance']}
- Has life insurance: {CLIENT_DATA['has_life_insurance']} (${CLIENT_DATA['life_insurance_coverage']:,})
- Goals: {', '.join(f"{g['name']} (${g['amount']:,} by {g['year']})" for g in CLIENT_DATA['goals'])}

Please:
1. Run a cashflow simulation to understand the trajectory
2. Analyze the gaps identified
3. Optimize a portfolio based on the appropriate risk profile
4. Provide a final investment plan with WHY rationale
"""

    print(f"\n📝 Client: {CLIENT_DATA['name']}")
    print(f"   Age: {CLIENT_DATA['age']}, Retirement: {CLIENT_DATA['retirement_age']}")
    print(f"   Goals: College Fund ($80k), Retirement ($2M)")
    
    # Initialize conversation
    contents = [types.Content(role="user", parts=[types.Part(text=user_prompt)])]
    
    # Agent loop
    max_iterations = 5
    for iteration in range(max_iterations):
        print(f"\n{'─' * 60}")
        print(f"Agent Iteration {iteration + 1}")
        print('─' * 60)
        
        # Call Gemini - try gemini-2.5-flash, fall back to others
        import time
        models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash-lite", "gemini-flash-latest"]
        
        response = None
        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        tools=TOOLS,
                        system_instruction=system_instruction,
                        temperature=0.7
                    )
                )
                break  # Success, exit loop
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    print(f"\n⏳ Rate limited on {model_name}, waiting 15 seconds...")
                    time.sleep(15)
                elif "404" in str(e) or "NOT_FOUND" in str(e):
                    print(f"\n⚠️ Model {model_name} not available, trying next...")
                    continue
                else:
                    raise
        
        if response is None:
            print("\n❌ All models failed or rate limited. Please try again later.")
            break
        
        # Check for function calls
        function_calls = []
        text_parts = []
        
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    function_calls.append(part.function_call)
                if hasattr(part, 'text') and part.text:
                    text_parts.append(part.text)
        
        # Print any text response (full output, no truncation)
        if text_parts:
            print(f"\n🤖 Agent says:")
            for text in text_parts:
                print(text)
        
        # If no function calls, we're done
        if not function_calls:
            print("\n✅ Agent completed analysis")
            break
        
        # Execute function calls
        function_responses = []
        for fc in function_calls:
            print(f"\n🔧 Calling tool: {fc.name}")
            result = execute_function(fc.name, dict(fc.args))
            function_responses.append(
                types.Part(function_response=types.FunctionResponse(
                    name=fc.name,
                    response=result
                ))
            )
        
        # Add assistant response and function results to conversation
        assistant_parts = []
        for fc in function_calls:
            assistant_parts.append(types.Part(function_call=fc))
        
        contents.append(types.Content(role="model", parts=assistant_parts))
        contents.append(types.Content(role="user", parts=function_responses))
    
    print("\n" + "=" * 60)
    print("  AGENT WORKFLOW COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    run_agent()
