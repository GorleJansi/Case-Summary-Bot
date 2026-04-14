import base64
import json
from typing import Any, Dict, List

import requests

from config import (
    CIRCUIT_APP_KEY,
    CIRCUIT_CHAT_BASE_URL,
    CIRCUIT_CLIENT_ID,
    CIRCUIT_CLIENT_SECRET,
    CIRCUIT_MODEL,
    CIRCUIT_TOKEN_URL,
)


class CircuitLLMError(Exception):
    """Raised when CIRCUIT token or chat completion fails."""


def _get_display_value(
    case_data: Dict[str, Any],
    field_name: str,
    default: str = "Not explicitly mentioned",
) -> str:
    value = case_data.get(field_name)

    if value is None or value == "":
        return default

    if isinstance(value, dict):
        if value.get("display_value"):
            return str(value["display_value"])
        if value.get("value"):
            return str(value["value"])
        return default

    return str(value)


def build_prompt(case_data: Dict[str, Any], timeline: List[Dict[str, Any]]) -> str:
    case_number = _get_display_value(case_data, "number", "Unknown")
    case_title = (
        _get_display_value(case_data, "case", "")
        or _get_display_value(case_data, "short_description", "")
        or "Not explicitly mentioned"
    )
    state = _get_display_value(case_data, "state")
    description = _get_display_value(case_data, "description")

    priority = _get_display_value(case_data, "priority")
    assignment_group = _get_display_value(case_data, "assignment_group")
    last_updated = _get_display_value(case_data, "sys_updated_on")

    lines = []
    for i, item in enumerate(timeline, start=1):
        timestamp = item.get("timestamp", "")
        speaker = item.get("speaker", "unknown")
        text = (item.get("text") or "").strip()
        lines.append(f"{i}. [{timestamp}] {speaker}: {text}")

    timeline_text = "\n".join(lines) if lines else "No journal activity found."

    return f"""Summarize this ServiceNow case for an engineer picking up the ticket.
They need to understand the situation in 30 seconds without reading the full timeline.

RULES:
1. Use ONLY facts from the data below. Never invent or assume.
2. Deduplicate: if the same thing is said multiple times, mention it once.
3. No email addresses, no personal names, no PII.
4. Keep each bullet to one short sentence.
5. If something is not stated, omit it entirely — do NOT write "Not explicitly mentioned".
6. Do NOT repeat the case number, priority, or dates — those are shown separately.

Case: {case_number} | Title: {case_title}
State: {state} | Priority: {priority}
Description: {description}

Timeline (oldest first):
{timeline_text}

Return EXACTLY this format (no markdown fences, no extra sections):

Problem:
<1-2 sentences: what is broken and who is affected>

Root Cause:
<1 sentence if identified in work notes, otherwise omit this section>

What Was Done:
- <each distinct action taken, from work notes only, deduplicated>

Current Status:
<1 sentence: where the ticket stands now>

Next Steps:
- <only if explicitly stated in the timeline>
""".strip()


def get_access_token() -> str:
    if not CIRCUIT_CLIENT_ID or not CIRCUIT_CLIENT_SECRET:
        raise CircuitLLMError("Missing CIRCUIT_CLIENT_ID or CIRCUIT_CLIENT_SECRET")

    creds = f"{CIRCUIT_CLIENT_ID}:{CIRCUIT_CLIENT_SECRET}"
    encoded = base64.b64encode(creds.encode("utf-8")).decode("utf-8")

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded}",
    }
    data = {"grant_type": "client_credentials"}

    response = requests.post(
        CIRCUIT_TOKEN_URL,
        headers=headers,
        data=data,
        timeout=30,
    )
    response.raise_for_status()

    payload = response.json()
    access_token = payload.get("access_token")
    if not access_token:
        raise CircuitLLMError(f"Token response missing access_token: {payload}")

    return access_token


def call_circuit_llm(prompt: str) -> str:
    if not CIRCUIT_APP_KEY:
        raise CircuitLLMError("Missing CIRCUIT_APP_KEY")

    access_token = get_access_token()
    url = f"{CIRCUIT_CHAT_BASE_URL}/{CIRCUIT_MODEL}/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "api-key": access_token,
    }

    body = {
        "messages": [
            {
                "role": "system",
                "content": (
                    "You produce concise, factual ticket summaries for support engineers. "
                    "Never repeat information. Never hallucinate. "
                    "If something is not in the data, leave it out entirely. "
                    "Keep the total summary under 200 words."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "user": json.dumps({"appkey": CIRCUIT_APP_KEY}),
        "temperature": 0.05,
        "max_tokens": 500,
    }

    response = requests.post(url, headers=headers, json=body, timeout=60)
    response.raise_for_status()

    payload = response.json()

    choices = payload.get("choices", [])
    if choices:
        message = choices[0].get("message", {})
        content = message.get("content")
        if content:
            return content.strip()

    if isinstance(payload.get("message"), dict):
        content = payload["message"].get("content")
        if content:
            return content.strip()

    raise CircuitLLMError(f"Unexpected LLM response format: {payload}")


def _prepend_case_context(summary_text: str, case_data: Dict[str, Any]) -> str:
    case_number = _get_display_value(case_data, "number", "Unknown")
    state = _get_display_value(case_data, "state")
    priority = _get_display_value(case_data, "priority")
    assignment_group = _get_display_value(case_data, "assignment_group")
    last_updated = _get_display_value(case_data, "sys_updated_on")

    # Compact metadata line
    meta_parts = []
    if priority and priority != "Not explicitly mentioned":
        meta_parts.append(f"Priority: {priority}")
    if state and state != "Not explicitly mentioned":
        meta_parts.append(f"State: {state}")
    if assignment_group and assignment_group != "Not explicitly mentioned":
        meta_parts.append(f"Group: {assignment_group}")
    if last_updated and last_updated != "Not explicitly mentioned":
        meta_parts.append(f"Updated: {last_updated}")
    meta_line = " | ".join(meta_parts)

    text = (summary_text or "").strip()

    # Remove any model-generated header like "Summary for CS..." 
    for prefix in ("Summary for", f"Summary for {case_number}", "Summary:"):
        if text.startswith(prefix):
            parts = text.split("\n", 1)
            text = parts[1].strip() if len(parts) > 1 else ""
            break

    final = f"{case_number} — {meta_line}\n\n{text}" if meta_line else f"{case_number}\n\n{text}"
    return final.strip()


def summarize_case_with_llm(case_data: Dict[str, Any], timeline: List[Dict[str, Any]]) -> str:
    try:
        prompt = build_prompt(case_data, timeline)
        raw_summary = call_circuit_llm(prompt)
        return _prepend_case_context(raw_summary, case_data)
    except Exception as e:
        print(f"LLM summarization error: {repr(e)}")
        return "Summary generation failed. Please try again."