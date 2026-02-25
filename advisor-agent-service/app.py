"""Flask API for advisor agent orchestration."""

from __future__ import annotations

import json
import os
import sys
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import requests
from flask import Flask, Response, jsonify, request

try:
    from dotenv import load_dotenv

    # Consolidated env loading:
    # 1) repo root .env (shared source of truth)
    # 2) local advisor .env (optional override)
    service_dir = Path(__file__).resolve().parent
    root_env_path = service_dir.parent / ".env"
    local_env_path = service_dir / ".env"
    if root_env_path.exists():
        load_dotenv(root_env_path, override=False)
    if local_env_path.exists():
        load_dotenv(local_env_path, override=False)
except ImportError:
    pass

_SERVICE_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SERVICE_DIR.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from advisor_agent import AdvisorAgent, AdvisorConfig
from policy_ui_transform.generator import PolicyUiGenerator

app = Flask(__name__)

_ADVISOR_AGENT: Optional[AdvisorAgent] = None
_POLICY_UI_GENERATOR: Optional[PolicyUiGenerator] = None
_CONSULTATION_INGESTS: Dict[str, Dict[str, Any]] = {}
_INGEST_LOCK = threading.Lock()

_INGEST_STORE_PATH = Path(
    os.getenv(
        "ADVISOR_INGEST_STORE_PATH",
        str(_SERVICE_DIR / "logs" / "consultation_ingests.ndjson"),
    )
)


def _load_ingests_from_disk() -> None:
    """Hydrate in-memory ingest cache from NDJSON store."""
    if not _INGEST_STORE_PATH.exists():
        return

    loaded_rows: Dict[str, Dict[str, Any]] = {}
    try:
        for raw_line in _INGEST_STORE_PATH.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(row, dict):
                continue
            ingest_id = str(row.get("ingest_id", "") or "").strip()
            if ingest_id:
                loaded_rows[ingest_id] = row
    except OSError:
        # Non-fatal: API still works with in-memory ingest cache.
        pass

    if loaded_rows:
        with _INGEST_LOCK:
            _CONSULTATION_INGESTS.update(loaded_rows)


def _append_ingest_to_disk(ingest_payload: Dict[str, Any]) -> None:
    """Append ingest payload to NDJSON store for restart resilience."""
    _INGEST_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = json.dumps(ingest_payload, ensure_ascii=True)
    with _INGEST_LOCK:
        with _INGEST_STORE_PATH.open("a", encoding="utf-8") as handle:
            handle.write(record + "\n")


_load_ingests_from_disk()


def _get_ingested_consultation(ingest_id: str) -> Optional[Dict[str, Any]]:
    """Fetch consultation ingest payload by ID."""
    if not ingest_id:
        return None
    with _INGEST_LOCK:
        return _CONSULTATION_INGESTS.get(ingest_id)


def _build_client_payload_with_consultation_context(
    body: Dict[str, Any]
) -> Tuple[Optional[Dict[str, Any]], str, Optional[Tuple[Any, int]]]:
    """Build advisor client payload with optional consultation context."""
    advisor_request = str(body.get("advisor_request", "") or "")
    consultation_ingest_id = str(body.get("consultation_ingest_id", "") or "").strip()
    provided_transcript = body.get("consultation_transcript")

    client_payload = dict(body)
    client_payload.pop("advisor_request", None)
    client_payload.pop("consultation_ingest_id", None)
    # Keep final-policy context transcript-first to avoid low-quality derived summaries
    # diluting the model input.
    client_payload.pop("consultation_summary", None)

    if consultation_ingest_id:
        ingested = _get_ingested_consultation(consultation_ingest_id)
        if not ingested:
            return None, advisor_request, (
                jsonify(
                    {
                        "success": False,
                        "error": "consultation_ingest_id not found",
                        "consultation_ingest_id": consultation_ingest_id,
                    }
                ),
                404,
            )

        client_payload["consultation_transcript"] = ingested.get("transcript", {})
        client_payload["consultation_ingest_ref"] = {
            "ingest_id": consultation_ingest_id,
            "session_id": ingested.get("session_id"),
            "created_at": ingested.get("created_at"),
        }
    else:
        if isinstance(provided_transcript, dict):
            client_payload["consultation_transcript"] = provided_transcript

    return client_payload, advisor_request, None


def get_advisor_agent() -> AdvisorAgent:
    """Lazily initialize advisor agent from environment config."""
    global _ADVISOR_AGENT
    if _ADVISOR_AGENT is None:
        config = AdvisorConfig.from_env()
        prompts_dir = Path(__file__).resolve().parent / "prompts"
        _ADVISOR_AGENT = AdvisorAgent(config=config, prompts_dir=prompts_dir)
    return _ADVISOR_AGENT


def get_policy_ui_generator() -> PolicyUiGenerator:
    """Lazily initialize standalone UI policy transformer."""
    global _POLICY_UI_GENERATOR
    if _POLICY_UI_GENERATOR is None:
        config = AdvisorConfig.from_env()
        ui_model = (
            os.getenv("ADVISOR_UI_GEMINI_MODEL", config.gemini_model).strip()
            or config.gemini_model
        )
        _POLICY_UI_GENERATOR = PolicyUiGenerator(
            gemini_api_key=config.gemini_api_key,
            gemini_model=ui_model,
            gemini_timeout_ms=config.gemini_timeout_ms,
            prompts_dir=_REPO_ROOT / "policy_ui_transform" / "prompts",
        )
    return _POLICY_UI_GENERATOR


def require_api_key() -> Tuple[bool, Optional[Dict[str, Any]]]:
    """Validate optional advisor API key if configured."""
    configured_key = os.getenv("ADVISOR_API_KEY", "").strip()
    if not configured_key:
        return True, None

    received_key = request.headers.get("X-Api-Key", "").strip()
    if received_key != configured_key:
        return False, {"success": False, "error": "Invalid or missing advisor API key"}

    return True, None


def _get_elevenlabs_config() -> Tuple[str, str, str, str]:
    """Resolve ElevenLabs config from environment."""
    api_key = str(os.getenv("ELEVENLABS_API_KEY", "") or "").strip()
    base_url = str(os.getenv("ELEVENLABS_BASE_URL", "https://api.elevenlabs.io") or "").strip().rstrip("/")
    consultation_agent_id = str(
        os.getenv("ELEVENLABS_CONSULTATION_AGENT_ID", os.getenv("ELEVENLABS_INITIAL_AGENT_ID", "")) or ""
    ).strip()
    presentation_agent_id = str(
        os.getenv("ELEVENLABS_PRESENTATION_AGENT_ID", "") or ""
    ).strip()
    return api_key, base_url, consultation_agent_id, presentation_agent_id


def _create_elevenlabs_signed_url_response(agent_id: str, missing_agent_env_name: str) -> Tuple[Any, int]:
    """Create standardized signed-url response payload for a given ElevenLabs agent."""
    api_key, base_url, _, _ = _get_elevenlabs_config()
    if not api_key:
        return jsonify({"success": False, "error": "ELEVENLABS_API_KEY is not configured"}), 500
    if not agent_id:
        return jsonify({"success": False, "error": f"{missing_agent_env_name} is not configured"}), 500
    if not base_url:
        return jsonify({"success": False, "error": "ELEVENLABS_BASE_URL is not configured"}), 500

    signed_url_endpoint = f"{base_url}/v1/convai/conversation/get_signed_url"
    try:
        response = requests.get(
            signed_url_endpoint,
            params={"agent_id": agent_id},
            headers={"xi-api-key": api_key},
            timeout=20,
        )
    except requests.RequestException as exc:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Failed to reach ElevenLabs signed URL endpoint",
                    "details": str(exc),
                }
            ),
            502,
        )

    if response.status_code >= 400:
        error_body: Any
        try:
            error_body = response.json()
        except ValueError:
            error_body = response.text
        return (
            jsonify(
                {
                    "success": False,
                    "error": "ElevenLabs signed URL request failed",
                    "status_code": response.status_code,
                    "details": error_body,
                }
            ),
            502,
        )

    payload = response.json() if response.content else {}
    signed_url = str(payload.get("signed_url", "") or "").strip()
    if not signed_url:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "ElevenLabs response did not include signed_url",
                    "details": payload,
                }
            ),
            502,
        )

    return (
        jsonify(
            {
                "success": True,
                "agent_id": agent_id,
                "signed_url": signed_url,
            }
        ),
        200,
    )


@app.route("/health", methods=["GET"])
def health() -> Any:
    """Service health endpoint."""
    return jsonify({"status": "healthy", "service": "advisor-agent-service"}), 200


@app.route("/advisor/api/v1/tool-health", methods=["GET"])
def tool_health() -> Any:
    """Check downstream tool connectivity."""
    ok, error = require_api_key()
    if not ok:
        return jsonify(error), 401

    try:
        agent = get_advisor_agent()
        status = agent.check_tool_access()
        is_healthy = status["cashflow"]["ok"] and status["neo_engine"]["ok"]
        http_status = 200 if is_healthy else 503
        return jsonify({"success": is_healthy, "tool_health": status}), http_status
    except Exception as exc:  # pylint: disable=broad-except
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Failed to run tool health check",
                    "details": str(exc),
                }
            ),
            500,
        )


@app.route("/advisor/api/v1/consultation-voice/signed-url", methods=["POST"])
def consultation_voice_signed_url() -> Any:
    """Create ElevenLabs signed URL for consultation voice session."""
    ok, error = require_api_key()
    if not ok:
        return jsonify(error), 401

    _, _, consultation_agent_id, _ = _get_elevenlabs_config()
    return _create_elevenlabs_signed_url_response(
        consultation_agent_id,
        "ELEVENLABS_CONSULTATION_AGENT_ID",
    )


@app.route("/advisor/api/v1/policy-voice/signed-url", methods=["POST"])
def policy_voice_signed_url() -> Any:
    """Create ElevenLabs signed URL for policy explanation voice session."""
    ok, error = require_api_key()
    if not ok:
        return jsonify(error), 401

    _, _, _, presentation_agent_id = _get_elevenlabs_config()
    return _create_elevenlabs_signed_url_response(
        presentation_agent_id,
        "ELEVENLABS_PRESENTATION_AGENT_ID",
    )


@app.route("/advisor/api/v1/generate-policy", methods=["POST"])
def generate_policy() -> Any:
    """Generate client financial planning policy via agentic loop."""
    ok, error = require_api_key()
    if not ok:
        return jsonify(error), 401

    try:
        body = request.get_json() or {}
        if not isinstance(body, dict) or not body:
            return jsonify({"success": False, "error": "Request JSON body is required"}), 400

        client_payload, advisor_request, error_response = _build_client_payload_with_consultation_context(body)
        if error_response is not None:
            return error_response

        agent = get_advisor_agent()
        result = agent.generate_policy(
            client_payload=client_payload,
            advisor_request=advisor_request,
        )
        policy_markdown = str(result.get("policy_markdown", "") or "").strip()
        if not policy_markdown:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Advisor generated an empty policy document",
                    }
                ),
                500,
            )

        return Response(policy_markdown, status=200, mimetype="text/markdown")

    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except Exception as exc:  # pylint: disable=broad-except
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Advisor agent execution failed",
                    "details": str(exc),
                }
            ),
            500,
        )


@app.route("/advisor/api/v1/generate-policy-json", methods=["POST"])
def generate_policy_json() -> Any:
    """Generate final UI policy JSON from Step-1 advisor policy + standalone UI transformation."""
    ok, error = require_api_key()
    if not ok:
        return jsonify(error), 401

    try:
        body = request.get_json() or {}
        if not isinstance(body, dict) or not body:
            return jsonify({"success": False, "error": "Request JSON body is required"}), 400

        client_payload, advisor_request, error_response = _build_client_payload_with_consultation_context(body)
        if error_response is not None:
            return error_response

        agent = get_advisor_agent()
        step1_result = agent.generate_step1_policy_json(
            client_payload=client_payload,
            advisor_request=advisor_request,
        )
        step1_policy = step1_result.get("step1_policy")
        if not isinstance(step1_policy, dict):
            return jsonify({"success": False, "error": "Advisor returned invalid Step-1 policy payload"}), 500

        ui_generator = get_policy_ui_generator()
        ui_result = ui_generator.generate_ui_policy_json(
            step1_policy=step1_policy,
            supporting_context=step1_result.get("context", {}),
        )
        raw_ui_policy = ui_result.get("ui_policy")
        if not isinstance(raw_ui_policy, dict):
            return jsonify({"success": False, "error": "UI transformer returned invalid policy payload"}), 500

        final_policy = agent.normalize_ui_policy_json(
            payload=raw_ui_policy,
            securities=step1_result.get("flat_securities", []),
            portfolio=step1_result.get("portfolio", {}),
        )

        return jsonify(final_policy), 200

    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except Exception as exc:  # pylint: disable=broad-except
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Advisor final policy generation failed",
                    "details": str(exc),
                }
            ),
            500,
        )


@app.route("/advisor/api/v1/generate-step1-policy-json", methods=["POST"])
def generate_step1_policy_json() -> Any:
    """Generate Step-1 policy JSON only (advisor policy generation output)."""
    ok, error = require_api_key()
    if not ok:
        return jsonify(error), 401

    try:
        body = request.get_json() or {}
        if not isinstance(body, dict) or not body:
            return jsonify({"success": False, "error": "Request JSON body is required"}), 400

        client_payload, advisor_request, error_response = _build_client_payload_with_consultation_context(body)
        if error_response is not None:
            return error_response

        agent = get_advisor_agent()
        result = agent.generate_step1_policy_json(
            client_payload=client_payload,
            advisor_request=advisor_request,
        )
        step1_policy = result.get("step1_policy")
        if not isinstance(step1_policy, dict):
            return jsonify({"success": False, "error": "Advisor returned invalid Step-1 policy payload"}), 500
        return jsonify(step1_policy), 200
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except Exception as exc:  # pylint: disable=broad-except
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Advisor Step-1 policy generation failed",
                    "details": str(exc),
                }
            ),
            500,
        )


@app.route("/advisor/api/v1/consultation-ingest", methods=["POST"])
def consultation_ingest() -> Any:
    """Ingest structured consultation transcript for advisor preprocessing."""
    ok, error = require_api_key()
    if not ok:
        return jsonify(error), 401

    body = request.get_json() or {}
    if not isinstance(body, dict):
        return jsonify({"success": False, "error": "Request JSON body is required"}), 400

    session_id = str(body.get("session_id", "") or "").strip()
    turns = body.get("turns")
    language = str(body.get("language", "en") or "en").strip()

    if not session_id:
        return jsonify({"success": False, "error": "session_id is required"}), 400
    if not isinstance(turns, list):
        return jsonify({"success": False, "error": "turns must be a list"}), 400

    normalized_turns = []
    for idx, turn in enumerate(turns):
        if not isinstance(turn, dict):
            return jsonify({"success": False, "error": f"turns[{idx}] must be an object"}), 400

        speaker = str(turn.get("speaker", "") or "").strip()
        text = str(turn.get("text", "") or "").strip()
        ts_start_ms = turn.get("ts_start_ms")

        if speaker not in {"agent", "client", "system"}:
            return jsonify({"success": False, "error": f"turns[{idx}].speaker is invalid"}), 400
        if not text:
            continue
        if not isinstance(ts_start_ms, (int, float)):
            return jsonify({"success": False, "error": f"turns[{idx}].ts_start_ms must be numeric"}), 400

        normalized_turns.append(
            {
                "speaker": speaker,
                "text": text,
                "ts_start_ms": int(ts_start_ms),
                "ts_end_ms": int(turn.get("ts_end_ms")) if isinstance(turn.get("ts_end_ms"), (int, float)) else None,
            }
        )

    agent_utterances = [t["text"] for t in normalized_turns if t["speaker"] == "agent"]

    ingest_id = str(uuid.uuid4())
    ingest_payload = {
        "ingest_id": ingest_id,
        "session_id": session_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "transcript": {
            "session_id": session_id,
            "started_at": body.get("started_at"),
            "ended_at": body.get("ended_at"),
            "completion_reason": body.get("completion_reason"),
            "turns": normalized_turns,
            "metadata": body.get("metadata", {}),
            "language": language,
        },
        "agent_preview": {
            "last_agent_message": agent_utterances[-1] if agent_utterances else "",
        },
    }
    with _INGEST_LOCK:
        _CONSULTATION_INGESTS[ingest_id] = ingest_payload
    try:
        _append_ingest_to_disk(ingest_payload)
    except OSError:
        # Keep response success even if persistence write fails.
        pass

    return (
        jsonify(
            {
                "success": True,
                "ingest_id": ingest_id,
                # Kept for response compatibility with existing frontend route shape.
                "consultation_summary": None,
            }
        ),
        200,
    )


@app.route("/advisor/api/v1/consultation-ingest/latest", methods=["GET"])
def consultation_ingest_latest() -> Any:
    """Fetch the latest ingested transcript payload."""
    ok, error = require_api_key()
    if not ok:
        return jsonify(error), 401

    latest_in_memory: Optional[Dict[str, Any]] = None
    with _INGEST_LOCK:
        ingests = list(_CONSULTATION_INGESTS.values())
    if ingests:
        latest_in_memory = max(
            ingests,
            key=lambda row: str(row.get("created_at", "") or ""),
        )

    latest = latest_in_memory
    if not latest:
        return jsonify({"success": False, "error": "No consultation ingests found"}), 404

    return jsonify({"success": True, "consultation_ingest": latest}), 200


@app.route("/advisor/api/v1/consultation-ingest/<ingest_id>", methods=["GET"])
def consultation_ingest_get(ingest_id: str) -> Any:
    """Fetch an ingested transcript payload by ingest ID."""
    ok, error = require_api_key()
    if not ok:
        return jsonify(error), 401

    ingest_id = str(ingest_id or "").strip()
    if not ingest_id:
        return jsonify({"success": False, "error": "ingest_id is required"}), 400

    payload = _get_ingested_consultation(ingest_id)
    if not payload:
        return jsonify({"success": False, "error": "consultation ingest not found"}), 404

    return jsonify({"success": True, "consultation_ingest": payload}), 200


if __name__ == "__main__":
    # Prefer an advisor-specific port to avoid colliding with the frontend server.
    port_str = os.getenv("ADVISOR_PORT")
    if not port_str:
        fallback_port = os.getenv("PORT", "").strip()
        port_str = fallback_port if fallback_port and fallback_port != "3000" else "8002"
    port = int(port_str) if port_str else 8002
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    print(f"Starting advisor-agent-service on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
