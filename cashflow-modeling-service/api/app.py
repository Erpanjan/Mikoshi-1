from __future__ import annotations

import math
import os
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from flask import Flask, jsonify, request


app = Flask(__name__)


@dataclass
class SimulationInputs:
    age: int
    retirement_age: int
    life_expectancy: int
    salary: float
    bonus: float
    spouse_income: float
    income_growth: float
    annual_expenses: float
    expense_growth: float
    bank_balance: float
    brokerage_balance: float
    retirement_balance: float
    education_balance: float
    mortgage_balance: float
    monthly_housing_cost: float
    primary_401k_contrib_pct: float
    employer_match_pct: float
    effective_tax_rate: float
    emergency_reserve_months: float
    brokerage_return: float
    brokerage_volatility: float
    retirement_return: float
    retirement_volatility: float
    bank_return: float
    bank_volatility: float
    education_goal_amount: float
    education_goal_year: int | None


def _to_float(value: Any, default: float = 0.0) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return default
    return default


def _to_int(value: Any, default: int) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value.strip()))
        except ValueError:
            return default
    return default


def _nested_get(payload: Dict[str, Any], path: List[str], default: Any = None) -> Any:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict):
            return default
        if key not in current:
            return default
        current = current[key]
    return current


def _pick_first(payload: Dict[str, Any], paths: List[List[str]], default: Any = None) -> Any:
    for path in paths:
        value = _nested_get(payload, path, None)
        if value is not None:
            return value
    return default


def _parse_reserve_months(raw: Any) -> float:
    if isinstance(raw, str) and "-" in raw:
        parts = raw.split("-", 1)
        low = _to_float(parts[0], 6.0)
        high = _to_float(parts[1], low)
        return (low + high) / 2.0
    return _to_float(raw, 6.0)


def _normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    total = sum(max(0.0, weight) for weight in weights.values())
    if total <= 0:
        return {}
    return {key: max(0.0, weight) / total for key, weight in weights.items()}


def _allocation_assumptions(weights: Dict[str, float], default_return: float, default_vol: float) -> Tuple[float, float]:
    if not weights:
        return default_return, default_vol

    assumption_map = {
        "us equity": (0.09, 0.18),
        "us large cap": (0.09, 0.18),
        "us small cap": (0.10, 0.22),
        "international equity": (0.08, 0.20),
        "international developed": (0.08, 0.20),
        "emerging markets": (0.10, 0.28),
        "us treasury": (0.035, 0.06),
        "us bonds": (0.04, 0.06),
        "international bonds": (0.03, 0.08),
        "reit": (0.08, 0.20),
        "cash": (0.02, 0.01),
    }

    annual_return = 0.0
    variance = 0.0
    for raw_key, raw_weight in _normalize_weights(weights).items():
        key = raw_key.strip().lower()
        asset_return, asset_vol = assumption_map.get(key, (default_return, default_vol))
        annual_return += raw_weight * asset_return
        variance += (raw_weight * asset_vol) ** 2
    return annual_return, math.sqrt(variance)


def _extract_allocation(payload: Dict[str, Any], keys: List[str]) -> Dict[str, float]:
    allocation = payload.get("asset_allocation", {})
    if not isinstance(allocation, dict):
        return {}
    for key in keys:
        candidate = allocation.get(key)
        if isinstance(candidate, dict):
            return {str(k): _to_float(v, 0.0) / (100.0 if _to_float(v, 0.0) > 1 else 1.0) for k, v in candidate.items()}
    return {}


def _infer_assumptions(payload: Dict[str, Any]) -> SimulationInputs:
    client = payload.get("client_profile", {})
    income = payload.get("income", {})
    expenses = payload.get("expenses", {})
    accounts = payload.get("accounts", {})
    liabilities = payload.get("liabilities", {})
    preferences = payload.get("preferences", {})
    financials = payload.get("financials", {})
    financial_assets = financials.get("assets", {}) if isinstance(financials, dict) else {}
    financial_income = financials.get("income", {}) if isinstance(financials, dict) else {}
    financial_expenses = financials.get("expenses", {}) if isinstance(financials, dict) else {}
    financial_savings = financials.get("savings", {}) if isinstance(financials, dict) else {}
    client_alias = payload.get("client", {}) if isinstance(payload.get("client"), dict) else {}

    age = _to_int(_pick_first(payload, [["client_profile", "age"], ["client", "age"]], 35), 35)
    retirement_age = _to_int(
        _pick_first(payload, [["client_profile", "retirement_age"], ["client", "retirement_age"]], 65),
        65,
    )
    life_expectancy = _to_int(
        _pick_first(payload, [["client_profile", "life_expectancy"], ["client", "life_expectancy"]], 90),
        90,
    )

    salary = _to_float(
        _pick_first(
            payload,
            [["income", "salary"], ["financials", "income", "salary_primary"], ["financials", "income", "salary"]],
            0.0,
        )
    )
    bonus = _to_float(
        _pick_first(payload, [["income", "bonus"], ["financials", "income", "bonus"]], 0.0)
    )
    spouse_income = _to_float(
        _pick_first(
            payload,
            [["income", "spouse_income"], ["financials", "income", "salary_spouse"], ["financials", "income", "spouse_income"]],
            0.0,
        )
    )
    income_growth = _to_float(_pick_first(payload, [["income", "yearly_increase"]], 3.0)) / 100.0
    annual_expenses = _to_float(
        _pick_first(
            payload,
            [["expenses", "base_spending"], ["financials", "expenses", "annual_total"]],
            0.0,
        )
    )
    expense_growth = _to_float(_pick_first(payload, [["expenses", "yearly_increase"]], 3.0)) / 100.0

    bank_balance = _to_float(
        _pick_first(payload, [["accounts", "bank", "balance"], ["financials", "assets", "cash"]], 0.0)
    )
    brokerage_balance = _to_float(
        _pick_first(payload, [["accounts", "brokerage", "balance"], ["financials", "assets", "brokerage"]], 0.0)
    )
    retirement_balance = _to_float(
        _pick_first(
            payload,
            [
                ["accounts", "401k", "pretax_balance"],
                ["accounts", "401k", "balance"],
                ["financials", "assets", "qualified_401k"],
            ],
            0.0,
        )
    )
    retirement_balance += _to_float(_pick_first(payload, [["accounts", "ira", "balance"]], 0.0))
    education_balance = _to_float(_pick_first(payload, [["accounts", "529", "balance"]], 0.0))

    mortgage_balance = _to_float(
        _pick_first(payload, [["liabilities", "mortgage_balance"], ["expenses", "housing", "mortgage_balance"]], 0.0)
    )
    monthly_housing_cost = (
        _to_float(_pick_first(payload, [["expenses", "housing", "monthly_principal_interest"]], 0.0))
        + _to_float(_pick_first(payload, [["expenses", "housing", "monthly_property_tax_and_homeowners_insurance"]], 0.0))
    )

    primary_401k_contrib_pct = _to_float(
        _pick_first(
            payload,
            [["accounts", "401k", "contrib_percent"], ["financials", "savings", "contribution_401k_percent"]],
            10.0,
        )
    )
    if primary_401k_contrib_pct > 1:
        primary_401k_contrib_pct /= 100.0

    employer_match_pct = _to_float(
        _pick_first(
            payload,
            [["accounts", "401k", "company_match_percent"], ["financials", "savings", "match_401k_percent"]],
            4.0,
        )
    )
    if employer_match_pct > 1:
        employer_match_pct /= 100.0

    gross_income = salary + bonus + spouse_income
    annual_net_take_home = (
        _to_float(_pick_first(payload, [["income", "net_monthly_take_home_min"]], 0.0))
        + _to_float(_pick_first(payload, [["income", "net_monthly_take_home_max"]], 0.0))
    ) / 2.0 * 12.0
    if gross_income > 0 and annual_net_take_home > 0:
        effective_tax_rate = max(0.10, min(0.45, 1.0 - annual_net_take_home / gross_income))
    else:
        effective_tax_rate = 0.27 if gross_income < 300000 else 0.31

    emergency_reserve_months = _parse_reserve_months(
        _pick_first(payload, [["preferences", "maintain_emergency_reserve_months"]], 6.0)
    )

    brokerage_allocation = _extract_allocation(payload, ["taxable_brokerage_current", "brokerage_current"])
    retirement_allocation = _extract_allocation(payload, ["401k_current", "retirement_accounts_current"])

    brokerage_return, brokerage_volatility = _allocation_assumptions(brokerage_allocation, 0.07, 0.16)
    retirement_return, retirement_volatility = _allocation_assumptions(retirement_allocation, 0.06, 0.12)
    bank_return, bank_volatility = 0.02, 0.005

    education_goal_amount = 0.0
    education_goal_year: int | None = None
    goals = payload.get("goals", [])
    if isinstance(goals, list):
        for goal in goals:
            if not isinstance(goal, dict):
                continue
            if str(goal.get("type", "")).strip().lower() != "education":
                continue
            amount = _to_float(goal.get("target_amount"), 0.0)
            if amount <= 0:
                notes = str(goal.get("notes", "") or "").lower()
                amount = 180000.0 if "in-state" in notes else 220000.0
            year = goal.get("target_year")
            if year is None and age >= 0:
                dependent_age = 0
                dependents_detail = client.get("dependents_detail", [])
                if isinstance(dependents_detail, list) and dependents_detail:
                    dependent_age = _to_int(dependents_detail[0].get("age"), 0)
                year = 2026 + max(1, 18 - dependent_age)
            education_goal_amount += amount
            if education_goal_year is None and year is not None:
                education_goal_year = _to_int(year, 2026 + 18)

    return SimulationInputs(
        age=age,
        retirement_age=max(retirement_age, age + 1),
        life_expectancy=max(life_expectancy, retirement_age + 1),
        salary=salary,
        bonus=bonus,
        spouse_income=spouse_income,
        income_growth=income_growth,
        annual_expenses=max(annual_expenses, 0.0),
        expense_growth=expense_growth,
        bank_balance=max(bank_balance, 0.0),
        brokerage_balance=max(brokerage_balance, 0.0),
        retirement_balance=max(retirement_balance, 0.0),
        education_balance=max(education_balance, 0.0),
        mortgage_balance=max(mortgage_balance, 0.0),
        monthly_housing_cost=max(monthly_housing_cost, 0.0),
        primary_401k_contrib_pct=max(primary_401k_contrib_pct, 0.0),
        employer_match_pct=max(employer_match_pct, 0.0),
        effective_tax_rate=effective_tax_rate,
        emergency_reserve_months=max(emergency_reserve_months, 1.0),
        brokerage_return=brokerage_return,
        brokerage_volatility=brokerage_volatility,
        retirement_return=retirement_return,
        retirement_volatility=retirement_volatility,
        bank_return=bank_return,
        bank_volatility=bank_volatility,
        education_goal_amount=max(education_goal_amount, 0.0),
        education_goal_year=education_goal_year,
    )


def _annual_return(mean: float, volatility: float, rng: random.Random, stochastic: bool) -> float:
    if not stochastic:
        return mean
    return max(-0.85, rng.gauss(mean, volatility))


def _run_single_path(inputs: SimulationInputs, stochastic: bool, rng: random.Random) -> Dict[str, Any]:
    age = inputs.age
    bank = inputs.bank_balance
    brokerage = inputs.brokerage_balance
    retirement = inputs.retirement_balance
    education = inputs.education_balance
    salary = inputs.salary
    bonus = inputs.bonus
    spouse_income = inputs.spouse_income
    expenses = inputs.annual_expenses
    reserve_target = expenses / 12.0 * inputs.emergency_reserve_months if expenses > 0 else 0.0
    education_shortfall = 0.0
    yearly_snapshots: List[Dict[str, float]] = []

    current_year = 2026
    while age < inputs.life_expectancy:
        retired = age >= inputs.retirement_age
        gross_income = 0.0 if retired else salary + bonus + spouse_income
        employee_401k = 0.0 if retired else salary * inputs.primary_401k_contrib_pct
        employer_match = 0.0 if retired else salary * inputs.employer_match_pct
        net_income = gross_income * (1.0 - inputs.effective_tax_rate)
        spend_need = expenses
        annual_free_cash = net_income - spend_need

        bank += annual_free_cash
        retirement += employee_401k + employer_match

        if inputs.education_goal_year is not None and current_year == inputs.education_goal_year:
            required = inputs.education_goal_amount
            covered = min(education + bank + brokerage, required)
            draw = required

            use_education = min(education, draw)
            education -= use_education
            draw -= use_education

            use_bank = min(bank, draw)
            bank -= use_bank
            draw -= use_bank

            use_brokerage = min(brokerage, draw)
            brokerage -= use_brokerage
            draw -= use_brokerage

            education_shortfall += max(0.0, required - covered)

        if bank > reserve_target:
            brokerage += bank - reserve_target
            bank = reserve_target
        elif bank < 0:
            deficit = -bank
            bank = 0.0

            use_brokerage = min(brokerage, deficit)
            brokerage -= use_brokerage
            deficit -= use_brokerage

            use_retirement = min(retirement, deficit)
            retirement -= use_retirement
            deficit -= use_retirement

            if deficit > 0:
                bank = -deficit

        bank *= 1.0 + _annual_return(inputs.bank_return, inputs.bank_volatility, rng, stochastic)
        brokerage *= 1.0 + _annual_return(
            inputs.brokerage_return, inputs.brokerage_volatility, rng, stochastic
        )
        retirement *= 1.0 + _annual_return(
            inputs.retirement_return, inputs.retirement_volatility, rng, stochastic
        )
        education *= 1.0 + _annual_return(
            inputs.brokerage_return, inputs.brokerage_volatility, rng, stochastic
        )

        total_assets = bank + brokerage + retirement + education
        yearly_snapshots.append(
            {
                "age": float(age),
                "year": float(current_year),
                "bank": round(bank, 2),
                "brokerage": round(brokerage, 2),
                "retirement": round(retirement, 2),
                "education": round(education, 2),
                "total_assets": round(total_assets, 2),
                "gross_income": round(gross_income, 2),
                "expenses": round(expenses, 2),
            }
        )

        salary *= 1.0 + inputs.income_growth
        bonus *= 1.0 + inputs.income_growth
        spouse_income *= 1.0 + inputs.income_growth
        expenses *= 1.0 + inputs.expense_growth
        reserve_target = expenses / 12.0 * inputs.emergency_reserve_months
        current_year += 1
        age += 1

    ending_balance = bank + brokerage + retirement + education
    shortfall = max(0.0, -ending_balance) + education_shortfall
    return {
        "ending_balance": round(max(0.0, ending_balance), 2),
        "shortfall": round(shortfall, 2),
        "success": shortfall <= 0.0 and ending_balance >= 0.0,
        "yearly_snapshots": yearly_snapshots,
    }


def _simulate(payload: Dict[str, Any]) -> Dict[str, Any]:
    inputs = _infer_assumptions(payload)
    simulation_config = payload.get("simulation_config", {})
    if not isinstance(simulation_config, dict):
        simulation_config = {}

    mode = str(simulation_config.get("mode", "deterministic") or "deterministic").strip()
    num_simulations = max(1, _to_int(simulation_config.get("num_simulations"), 500))
    seed = _to_int(simulation_config.get("seed"), 42)
    stochastic = mode == "monte_carlo"

    if not stochastic:
        result = _run_single_path(inputs, stochastic=False, rng=random.Random(seed))
        return {
            "success": True,
            "simulation_mode": mode,
            "summary": {
                "goal_shortfall": result["shortfall"],
                "goal_success_probability": 1.0 if result["success"] else 0.0,
                "projected_terminal_value": result["ending_balance"],
                "ending_balance": result["ending_balance"],
                "shortfall": result["shortfall"],
                "success_probability": 1.0 if result["success"] else 0.0,
            },
            "details": {
                "inputs": inputs.__dict__,
                "yearly_snapshots": result["yearly_snapshots"],
            },
        }

    results = []
    success_count = 0
    terminal_values: List[float] = []
    shortfalls: List[float] = []
    for idx in range(num_simulations):
        path_result = _run_single_path(inputs, stochastic=True, rng=random.Random(seed + idx))
        results.append(path_result)
        terminal_values.append(path_result["ending_balance"])
        shortfalls.append(path_result["shortfall"])
        if path_result["success"]:
            success_count += 1

    terminal_values.sort()
    shortfalls.sort()
    median_index = len(terminal_values) // 2
    median_terminal = terminal_values[median_index]
    median_shortfall = shortfalls[median_index]
    success_probability = success_count / len(results)

    return {
        "success": True,
        "simulation_mode": mode,
        "summary": {
            "goal_shortfall": round(median_shortfall, 2),
            "goal_success_probability": round(success_probability, 4),
            "projected_terminal_value": round(median_terminal, 2),
            "ending_balance": round(median_terminal, 2),
            "shortfall": round(median_shortfall, 2),
            "success_probability": round(success_probability, 4),
        },
        "details": {
            "inputs": inputs.__dict__,
            "num_simulations": len(results),
            "terminal_value_percentiles": {
                "p10": terminal_values[max(0, int(len(terminal_values) * 0.10) - 1)],
                "p50": median_terminal,
                "p90": terminal_values[max(0, int(len(terminal_values) * 0.90) - 1)],
            },
            "shortfall_percentiles": {
                "p10": shortfalls[max(0, int(len(shortfalls) * 0.10) - 1)],
                "p50": median_shortfall,
                "p90": shortfalls[max(0, int(len(shortfalls) * 0.90) - 1)],
            },
        },
    }


@app.get("/health")
def health() -> Tuple[Any, int]:
    return jsonify({"ok": True, "service": "cashflow-model-api"}), 200


@app.post("/cashflow/api/v1/simulate")
def simulate() -> Tuple[Any, int]:
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"success": False, "error": "Request JSON body is required"}), 400
    if not isinstance(payload, dict):
        return jsonify({"success": False, "error": "Request JSON body must be an object"}), 400
    return jsonify(_simulate(payload)), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8001"))
    app.run(host="0.0.0.0", port=port, debug=False)
