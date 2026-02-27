"""Client profile agent that focuses on understanding needs/gaps via cashflow analysis."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

from google.genai import types

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SOLUTION_AGENT_DIR = _REPO_ROOT / "solution-agent-service"
if str(_SOLUTION_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(_SOLUTION_AGENT_DIR))

from advisor_agent import AdvisorAgent, AdvisorConfig


class ClientProfileAgent(AdvisorAgent):
    """Cashflow-first agent for client understanding and gap identification."""

    def analyze_client_profile(
        self,
        client_payload: Dict[str, Any],
        advisor_request: str = "",
    ) -> Dict[str, Any]:
        """Run cashflow-only agent loop and return structured profile/gap analysis."""
        self._validate_client_payload(client_payload)

        loop_result = self._run_tool_loop(
            client_payload=client_payload,
            advisor_request=advisor_request,
        )
        state = loop_result["state"]

        context = {
            "client_payload": client_payload,
            "advisor_request": advisor_request,
            "tool_memory": self._build_tool_memory_context(state),
            "tool_audit": state.tool_audit,
            "finalize_signal": loop_result.get("finalize_signal"),
        }

        prompt_template = self._read_prompt("core_profile_prompt.txt")
        user_prompt = (
            f"{prompt_template}\n\n"
            "Use this JSON context as source-of-truth:\n"
            f"{json.dumps(context, indent=2, ensure_ascii=True)}"
        )

        response, model_used = self._generate_with_fallback(
            contents=[types.Content(role="user", parts=[types.Part(text=user_prompt)])],
            system_instruction=(
                "You are a client profile analysis agent. Produce one JSON object only."
            ),
            use_tools=False,
            temperature=0.2,
        )

        raw_text = (response.text or "").strip()
        if not raw_text:
            extracted_text, _ = self._extract_parts(response)
            raw_text = "\n".join(extracted_text).strip()

        profile_analysis = self._parse_json_object(raw_text)
        self._validate_profile_analysis(profile_analysis)

        return {
            "success": True,
            "model_used": model_used,
            "profile_analysis": profile_analysis,
            "context": context,
            "tool_loop_model_used": loop_result.get("model_used", "unknown"),
            "finalize_signal": loop_result.get("finalize_signal"),
        }

    def _tool_declaration(self) -> types.Tool:
        """Cashflow-only tool declaration for client profile analysis."""
        return types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="runCashflowModel",
                    description=(
                        "Run numeric cashflow simulation. Returns quantitative projections only; "
                        "the AI must do interpretation and gap reasoning."
                    ),
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "simulation_mode": types.Schema(
                                type=types.Type.STRING,
                                enum=["deterministic", "monte_carlo"],
                                description="Simulation mode. Use deterministic first, then monte_carlo.",
                            ),
                            "num_simulations": types.Schema(
                                type=types.Type.INTEGER,
                                description="Number of simulations for monte_carlo mode.",
                            ),
                            "seed": types.Schema(
                                type=types.Type.INTEGER,
                                description="Optional random seed for simulation reproducibility.",
                            ),
                            "return_individual_runs": types.Schema(
                                type=types.Type.BOOLEAN,
                                description="If true, request individual run trajectories in monte_carlo mode.",
                            ),
                            "num_individual_runs": types.Schema(
                                type=types.Type.INTEGER,
                                description="Number of individual runs to return when enabled.",
                            ),
                            "payload_override": types.Schema(
                                type=types.Type.OBJECT,
                                description=(
                                    "Deep-merge override for the cashflow params payload. "
                                    "Use this to modify any account type or nested field "
                                    "(bank, brokerage, 401k, ira, housing, debt, insurance, goals, etc.)."
                                ),
                            ),
                            "bank_balance_override": types.Schema(
                                type=types.Type.NUMBER,
                                description="Optional bank balance override for scenario testing.",
                            ),
                            "investment_balance_override": types.Schema(
                                type=types.Type.NUMBER,
                                description="Optional brokerage balance override for scenario testing.",
                            ),
                        },
                    ),
                )
            ]
        )

    def _build_initial_prompt(self, client_payload: Dict[str, Any], advisor_request: str) -> str:
        """Create initial prompt for profile-understanding loop."""
        request_text = advisor_request.strip() or "No additional request constraints provided."
        return (
            "Analyze the following client profile and identify financial needs/gaps.\n\n"
            "Objectives:\n"
            "1) Build clear client understanding from profile/transcript context.\n"
            "2) Use cashflow modeling (deterministic + probabilistic) for gap diagnosis.\n"
            "3) Identify gaps by category: investment-solvable, behavioral, structural/external.\n"
            "4) Produce concise, actionable diagnostic output (not policy construction).\n\n"
            "Additional request from advisor/user:\n"
            f"{request_text}\n\n"
            "Client payload JSON:\n"
            f"{json.dumps(client_payload, indent=2, ensure_ascii=True)}"
        )

    def _validate_profile_analysis(self, payload: Dict[str, Any]) -> None:
        """Validate profile-analysis output schema."""
        required_top = [
            "client_understanding_summary",
            "identified_needs",
            "gaps_by_category",
            "scenario_findings",
            "tool_execution_log",
        ]
        missing = [field for field in required_top if field not in payload]
        if missing:
            raise ValueError(
                f"Client profile analysis JSON missing required fields: {', '.join(missing)}"
            )

        if not isinstance(payload.get("identified_needs"), list):
            raise ValueError("Client profile analysis requires identified_needs array")

        gaps = payload.get("gaps_by_category")
        if not isinstance(gaps, dict):
            raise ValueError("Client profile analysis requires gaps_by_category object")

        for key in ["investment-solvable", "behavioral", "structural/external"]:
            if key not in gaps:
                raise ValueError(f"gaps_by_category.{key} is required")
            value = gaps.get(key)
            if isinstance(value, str):
                if value != "None":
                    raise ValueError(
                        f"gaps_by_category.{key} string value must be exactly 'None'"
                    )
                continue
            if not isinstance(value, list):
                raise ValueError(
                    f"gaps_by_category.{key} must be an array or the string 'None'"
                )
            for idx, row in enumerate(value):
                if isinstance(row, str):
                    # Backward-compatible acceptance for older prompt outputs.
                    if not row.strip():
                        raise ValueError(f"gaps_by_category.{key}[{idx}] must not be empty")
                    continue
                if not isinstance(row, dict):
                    raise ValueError(
                        f"gaps_by_category.{key}[{idx}] must be an object with gap/discussion"
                    )
                gap_text = str(row.get("gap", "") or "").strip()
                discussion = str(row.get("discussion", "") or "").strip()
                if not gap_text:
                    raise ValueError(f"gaps_by_category.{key}[{idx}].gap is required")
                if not discussion:
                    raise ValueError(
                        f"gaps_by_category.{key}[{idx}].discussion is required"
                    )


def build_client_profile_agent(config: AdvisorConfig) -> ClientProfileAgent:
    """Build client profile agent using the dedicated prompt directory."""
    prompts_dir = Path(__file__).resolve().parent / "prompts"
    return ClientProfileAgent(config=config, prompts_dir=prompts_dir)
