from __future__ import annotations

import os
from typing import Any, Dict, Tuple

from flask import Flask, jsonify, request


app = Flask(__name__)


def _extract_numeric(payload: Any, fallback: float) -> float:
    """Best-effort numeric extraction from nested payload values."""
    if isinstance(payload, (int, float)):
        return float(payload)
    if isinstance(payload, dict):
        for value in payload.values():
            extracted = _extract_numeric(value, fallback)
            if extracted != fallback:
                return extracted
    if isinstance(payload, list):
        for value in payload:
            extracted = _extract_numeric(value, fallback)
            if extracted != fallback:
                return extracted
    return fallback


def _simulate_stub(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Lightweight compatibility response for advisor integration.
    Keeps keys stable so advisor metrics extraction works.
    """
    accounts = payload.get("accounts", {}) if isinstance(payload, dict) else {}
    bank_balance = _extract_numeric(accounts.get("bank", {}), 0.0)
    brokerage_balance = _extract_numeric(accounts.get("brokerage", {}), 0.0)
    total_investable = bank_balance + brokerage_balance

    # Deterministic placeholder metrics for local orchestration.
    projected_value = max(0.0, total_investable * 1.08)
    shortfall = 0.0
    success_probability = 1.0

    return {
        "success": True,
        "simulation_mode": (
            payload.get("simulation_config", {}).get("mode", "deterministic")
            if isinstance(payload, dict)
            else "deterministic"
        ),
        "summary": {
            "goal_shortfall": shortfall,
            "goal_success_probability": success_probability,
            "projected_terminal_value": projected_value,
            "ending_balance": projected_value,
            "shortfall": shortfall,
            "success_probability": success_probability,
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
    return jsonify(_simulate_stub(payload)), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8001"))
    app.run(host="0.0.0.0", port=port, debug=False)
