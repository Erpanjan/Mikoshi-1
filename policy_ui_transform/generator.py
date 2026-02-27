"""Gemini-based conversion from Step-1 policy JSON to UI policy JSON."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from google import genai
from google.genai import types


class PolicyUiGenerator:
    """Dedicated step for generating UI payload JSON from Step-1 policy JSON."""

    def __init__(
        self,
        gemini_api_key: str,
        gemini_model: str,
        gemini_timeout_ms: int,
        prompts_dir: Path,
    ):
        if not gemini_api_key:
            raise ValueError("Gemini API key is required for PolicyUiGenerator")
        self.gemini_model = gemini_model
        self.prompts_dir = prompts_dir
        self.client = genai.Client(
            api_key=gemini_api_key,
            http_options=types.HttpOptions(timeout=gemini_timeout_ms),
        )
        # Temporary prompt logging to inspect exact Gemini request contexts.
        self._prompt_log_enabled = os.getenv("ADVISOR_TEMP_LOG_PROMPTS", "true").strip().lower() not in {
            "0",
            "false",
            "no",
            "off",
        }
        default_log_path = (
            self.prompts_dir.parent.parent / "solution-agent-service" / "logs" / "gemini_prompt_debug.ndjson"
        )
        self._prompt_log_path = Path(
            os.getenv("ADVISOR_TEMP_PROMPT_LOG_PATH", str(default_log_path))
        )

    def generate_ui_policy_json(
        self,
        step1_policy: Optional[Dict[str, Any]] = None,
        supporting_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run Gemini conversion from Step-1 policy JSON to UI JSON payload."""
        if not isinstance(step1_policy, dict):
            raise ValueError("step1_policy is required")

        system_prompt = self._read_prompt("system_prompt.txt")
        user_payload = {
            "step1_policy": step1_policy,
            "supporting_context": supporting_context or {},
        }
        user_prompt = (
            "Convert the provided Step-1 financial planning policy into UI JSON.\n"
            "Use step1_policy as source-of-truth. Use supporting_context only when needed.\n\n"
            f"{json.dumps(user_payload, indent=2, ensure_ascii=True)}"
        )
        self._append_prompt_log(
            {
                "stage": "ui_transform_generate_content",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "model": self.gemini_model,
                "system_instruction": system_prompt,
                "temperature": 0.2,
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": user_prompt}],
                    }
                ],
            }
        )

        response = self.client.models.generate_content(
            model=self.gemini_model,
            contents=[types.Content(role="user", parts=[types.Part(text=user_prompt)])],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2,
            ),
        )
        raw_text = (response.text or "").strip()
        if not raw_text:
            extracted_text, _ = self._extract_parts(response)
            raw_text = "\n".join(extracted_text).strip()

        payload = self._parse_json_object(raw_text)
        payload = self._normalize_menu_preview_summary(payload)
        return {
            "success": True,
            "model_used": self.gemini_model,
            "ui_policy": payload,
        }

    def _read_prompt(self, filename: str) -> str:
        path = self.prompts_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Prompt file not found: {path}")
        return path.read_text(encoding="utf-8")

    def _extract_parts(self, response: Any) -> Tuple[list[str], list[Any]]:
        texts: list[str] = []
        function_calls: list[Any] = []
        candidates = getattr(response, "candidates", None) or []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            if not content:
                continue
            for part in content.parts:
                text = getattr(part, "text", None)
                if text:
                    texts.append(text)
                function_call = getattr(part, "function_call", None)
                if function_call:
                    function_calls.append(function_call)
        if not texts and getattr(response, "text", None):
            texts.append(response.text)
        return texts, function_calls

    def _parse_json_object(self, raw_text: str) -> Dict[str, Any]:
        text = str(raw_text or "").strip()
        if not text:
            raise ValueError("UI generation returned empty JSON output")

        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            candidate = text[start : end + 1]
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass

        raise ValueError("UI generation returned invalid JSON output")

    def _append_prompt_log(self, payload: Dict[str, Any]) -> None:
        """Append prompt-debug payload as NDJSON; never raise to caller."""
        if not self._prompt_log_enabled:
            return
        try:
            self._prompt_log_path.parent.mkdir(parents=True, exist_ok=True)
            with self._prompt_log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, ensure_ascii=True, default=str) + "\n")
        except OSError:
            # Temporary diagnostics should never break policy generation.
            pass

    def _normalize_menu_preview_summary(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Constrain menu summary to concise preview form for menu-card rendering."""
        if not isinstance(payload, dict):
            return payload

        menu = payload.get("menu")
        if not isinstance(menu, dict):
            return payload

        summary = str(menu.get("summary", "") or "").strip()
        if not summary:
            return payload

        compact = " ".join(summary.split())
        sentences = [s.strip() for s in compact.replace("!", ".").replace("?", ".").split(".") if s.strip()]

        picked: list[str] = []
        for sentence in sentences:
            # De-prioritize dense numeric explanation in preview copy.
            digit_count = sum(ch.isdigit() for ch in sentence)
            if digit_count > 6 and len(sentences) > 1:
                continue
            picked.append(sentence)
            if len(picked) == 3:
                break

        if not picked:
            picked = sentences[:2] if sentences else [compact]

        concise = ". ".join(picked).strip()
        if concise and not concise.endswith("."):
            concise += "."

        if len(concise) > 260:
            concise = concise[:259].rstrip() + "…"

        menu["summary"] = concise
        payload["menu"] = menu
        return payload
