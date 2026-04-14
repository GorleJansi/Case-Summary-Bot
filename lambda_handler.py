"""
AWS Lambda entry point.
Wraps the FastAPI app with Mangum so API Gateway events are
translated into ASGI requests that FastAPI can handle.

Also handles async "summary" events that the bot fires to itself
so the webhook can return immediately while the heavy pipeline
(ServiceNow fetch → LLM call → card update) runs in a separate
Lambda invocation with no API Gateway timeout.
"""

import os
import sys

# Bootstrap vendor/ path BEFORE any third-party imports.
_vendor_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor")
if _vendor_dir not in sys.path:
    sys.path.insert(0, _vendor_dir)

from mangum import Mangum
from app import app, _summarize_and_flip  # import the FastAPI instance + pipeline

# Mangum adapter: converts API Gateway/ALB events → FastAPI
_mangum = Mangum(app, lifespan="off")


def handler(event, context):
    """
    Entrypoint that Lambda calls.

    Two kinds of events arrive here:
      1. API Gateway HTTP event  → delegate to Mangum (FastAPI)
      2. Async summary event     → run the heavy pipeline directly
         {
           "_async_summary": true,
           "room_id": "...",
           "case_number": "CS0001026",
           "card_message_id": "..." | null
         }
    """
    # ── Async summary pipeline (self-invoked) ─────────────────────────────
    if event.get("_async_summary"):
        room_id         = event["room_id"]
        case_number     = event["case_number"]
        card_message_id = event.get("card_message_id")
        print(f"[ASYNC] ⏩ Running summary pipeline for {case_number}")
        _summarize_and_flip(room_id, case_number, card_message_id)
        return {"status": "ok", "case_number": case_number}

    # ── Normal HTTP event from API Gateway ────────────────────────────────
    return _mangum(event, context)
