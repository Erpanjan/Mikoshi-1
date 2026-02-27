# Solution Agent Service

Flask service that runs an agentic workflow using Gemini and two external tools:
- Cashflow modeling API
- Neo engine optimization API

The service now uses a two-agent pipeline:
- Client Profile Agent (cashflow-only): understands client context and identifies needs/gaps.
- Solution Agent (existing advisor logic): builds Step-1 financial planning policy.

## Key Design Choices

- Agent brain: `models/gemini-3-pro-preview` by default (`ADVISOR_GEMINI_MODEL` configurable).
- Three-step policy pipeline:
  1) Client Profile Agent runs a cashflow-only loop and outputs profile/gap analysis.
  2) Solution Agent runs a tool-enabled loop (cashflow + Neo) and produces Step-1 policy JSON.
  3) A standalone UI generation step calls Gemini again to convert Step-1 policy JSON into UI JSON.
- Neo tool inputs exposed to the model: only:
  - `target_volatility`
  - `active_risk_percentage`
- Neo internals are fixed by service config:
  - `risk_profile` (default `RP3`)
  - `weight_type` (default `dynamic`)
- Prompts are externalized under `prompts/` for easy edits.
- Neo output is compacted before entering model context to avoid context bloat.

## Files

- `app.py`: Flask API.
- `advisor_agent.py`: core agent loop, tool clients, compaction logic.
- `../client-profile-agent-service/client_profile_agent.py`: client profile agent implementation.
- `../client-profile-agent-service/prompts/`: prompts for profile analysis stage.
- `prompts/agent_system.txt`: system prompt used for tool-enabled advisor reasoning.
- `prompts/core_policy_prompt.txt`: Step-1 policy JSON template.
- `../policy_ui_transform/generator.py`: standalone policy->UI generation step.
- `../policy_ui_transform/prompts/system_prompt.txt`: system prompt for UI generation step.

## Setup

1. Use repo root `.env` as the source of truth.

Supported env names (advisor reads either form):
- Gemini key: `GOOGLE_GENAI_API_KEY` or `GEMINI_API_KEY`
- Neo URL: `NEOENGINE_API_URL` or `PYTHON_NEO_ENGINE_URL`
- Neo key: `NEOENGINE_API_KEY` or `NEO_ENGINE_API_KEY`
- Cashflow URL: `CASHFLOW_API_URL` or `CASHFLOW_MODEL_URL`
- Optional cashflow key: `CASHFLOW_API_KEY`

2. Install dependencies:

```bash
pip install -r solution-agent-service/requirements.txt
```

3. Run service:

```bash
cd solution-agent-service
python app.py
```

Service default port: `8002` (set `ADVISOR_PORT` to override).
If repo root `.env` has `PORT=3000` for frontend, advisor will still stay on `8002` unless `ADVISOR_PORT` is set.

## Endpoints

- `GET /health`
- `GET /advisor/api/v1/tool-health`
- `POST /advisor/api/v1/generate-policy-json`
- `POST /advisor/api/v1/generate-step1-policy-json`
- `POST /advisor/api/v1/consultation-ingest`
- `POST /advisor/api/v1/generate-policy`

## Request Example

```json
{
  "advisor_request": "Focus on retirement sufficiency and near-term liquidity.",
  "client_profile": {
    "name": "Sample Client",
    "age": 38,
    "retirement_age": 62,
    "life_expectancy": 90,
    "dependents": 2
  },
  "accounts": {
    "bank": { "balance": 45000 },
    "brokerage": { "balance": 120000 },
    "401k": { "pretax_balance": 180000, "contrib_percent": 10, "company_match_percent": 4 },
    "ira": { "balance": 40000, "type": "roth" }
  },
  "income": {
    "salary": 160000,
    "yearly_increase": 3.0
  },
  "expenses": {
    "base_spending": 90000,
    "yearly_increase": 3.0,
    "housing": { "type": "own", "mortgage_balance": 350000 }
  },
  "goals": [
    { "name": "Retirement", "target_amount": 3200000, "target_year": 2050 }
  ],
  "asset_allocation": {},
  "has_disability_insurance": false,
  "has_life_insurance": true,
  "life_insurance_coverage": 350000
}
```

## Response Shape

`POST /advisor/api/v1/generate-policy-json` returns one structured JSON payload used as single source of truth for menu/detail/execution UI.
`POST /advisor/api/v1/generate-policy` returns `text/markdown` directly on success (legacy/optional output format).
Error responses remain JSON.

## Notes

- `tool-health` is the quickest way to validate connectivity/auth to both tool APIs.
- If `ADVISOR_API_KEY` is set, include it as `X-Api-Key` header for advisor endpoints.
- Advisor defaults to a single model (`models/gemini-3-pro-preview`) for policy generation.
- Optional UI-step model override: `ADVISOR_UI_GEMINI_MODEL` (defaults to advisor model).
