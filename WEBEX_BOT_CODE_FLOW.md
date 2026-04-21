# Webex Bot Case Summary — Complete Code-Level Flow

This document explains the **Webex Bot POC** in complete detail — every file, function, and what happens in the background at each step.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Project Structure](#project-structure)
4. [How Files Connect](#how-files-connect)
5. [Request Flow Diagram](#request-flow-diagram)
6. [Code-Level Flow — Step by Step](#code-level-flow--step-by-step)
7. [Key Functions Reference](#key-functions-reference)
8. [Adaptive Cards Templates](#adaptive-cards-templates)
9. [Environment Variables](#environment-variables)
10. [Deployment](#deployment)

---

## Overview

### What This Bot Does

1. User sends a message to the bot in Webex (DM or @mention in a space)
2. Bot receives the message via a webhook
3. If the message contains a case number (e.g., `CS0001027`):
   - Bot fetches case data from ServiceNow
   - Bot builds a chronological timeline of all activity
   - Bot calls Cisco CIRCUIT LLM to generate a summary
   - Bot sends back a formatted Adaptive Card with the summary

### User Experience

```
┌─────────────────────────────────────────────────────────────────┐
│  WEBEX TEAMS                                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  👤 User: CS0001027                                             │
│                                                                 │
│  🤖 Bot: ⏳ Generating summary for CS0001027...                 │
│         Fetching the case from ServiceNow and building the      │
│         timeline. This usually takes a few seconds...           │
│                                                                 │
│         ↓ (card updates automatically after 3-5 seconds)        │
│                                                                 │
│  🤖 Bot: ┌─────────────────────────────────────────┐            │
│         │ 📋 Summary — CS0001027                   │            │
│         │                                         │            │
│         │ CS0001027 -- Priority: High | State:    │            │
│         │ Resolved | Group: CX Team               │            │
│         │                                         │            │
│         │ **Problem:**                            │            │
│         │ Password reset links expiring due to    │            │
│         │ timezone mismatch and 15-min TTL...     │            │
│         │                                         │            │
│         │ **What Was Done:**                      │            │
│         │ - Reproduced issue in test environment  │            │
│         │ - Identified root cause: timezone bug   │            │
│         │ - Implemented UTC fix + 60-min TTL      │            │
│         │ - Deployed to production                │            │
│         │                                         │            │
│         │ **Current Status:**                     │            │
│         │ Issue resolved. Fix deployed.           │            │
│         │                                         │            │
│         │ [Summarize another] [Close]             │            │
│         └─────────────────────────────────────────┘            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                    OVERVIEW                                       │
└──────────────────────────────────────────────────────────────────────────────────┘

┌──────────┐     ┌──────────────┐     ┌─────────────────────────────────────────────┐
│  User    │     │   Webex      │     │              AWS Cloud                       │
│ (Webex)  │     │  Platform    │     │                                             │
└────┬─────┘     └──────┬───────┘     │  ┌──────────────┐    ┌──────────────────┐  │
     │                  │             │  │ API Gateway  │    │  AWS Lambda       │  │
     │ 1. Send message  │             │  │              │    │                   │  │
     │─────────────────>│             │  │  /webhook/   │───>│  lambda_handler   │  │
     │                  │             │  │  webex       │    │       │           │  │
     │                  │ 2. Webhook  │  │              │    │       ▼           │  │
     │                  │────────────────>│              │    │  FastAPI app.py  │  │
     │                  │             │  └──────────────┘    │       │           │  │
     │                  │             │                      │       │           │  │
     │                  │             └──────────────────────│───────│───────────┘  │
     │                  │                                    │       │              │
     │                  │                                    │       │              │
     │                  │             ┌──────────────────────│───────│──────────────┘
     │                  │             │                      │       │
     │                  │             │                      ▼       │
     │                  │             │  ┌───────────────────────────┴─────────┐
     │                  │             │  │                                     │
     │                  │             │  │  3. GET case + journals + emails    │
     │                  │             │  │─────────────────────────────────────│────┐
     │                  │             │  │                                     │    │
     │                  │             │  │  servicenow_client.py               │    │
     │                  │             │  │                                     │    │
     │                  │             │  └─────────────────────────────────────┘    │
     │                  │             │                      │                      │
     │                  │             │                      │                      │
     │                  │             │                      ▼                      │
     │                  │             │  ┌───────────────────────────┐              │
     │                  │             │  │  4. Build timeline        │              │
     │                  │             │  │     formatter.py          │              │
     │                  │             │  └───────────────────────────┘              │
     │                  │             │                      │                      │
     │                  │             │                      ▼                      │
     │                  │             │  ┌───────────────────────────┐              │
     │                  │             │  │  5. Call CIRCUIT LLM      │              │
     │                  │             │  │     summarizer.py ────────│──────────┐   │
     │                  │             │  └───────────────────────────┘          │   │
     │                  │             │                      │                  │   │
     │                  │             │                      ▼                  │   │
     │                  │             │  ┌───────────────────────────┐          │   │
     │                  │             │  │  6. Send Adaptive Card    │          │   │
     │                  │ 7. Card     │  │     POST /messages        │          │   │
     │<─────────────────│<───────────────│     to Webex API          │          │   │
     │                  │             │  └───────────────────────────┘          │   │
     │                  │             │                                         │   │
     │                  │             └─────────────────────────────────────────│───┘
     │                  │                                                       │
     │                  │                                                       │
┌────┴─────┐     ┌──────┴───────┐     ┌─────────────────────┐     ┌─────────────┴───┐
│  User    │     │   Webex      │     │    ServiceNow       │     │  Cisco CIRCUIT  │
│ (Webex)  │     │  Platform    │     │    (CSM Data)       │     │      LLM        │
└──────────┘     └──────────────┘     └─────────────────────┘     └─────────────────┘
```

---

## Project Structure

```
cPaas-sNow-summarisation-agent-final/
│
├── lambda_handler.py      # AWS Lambda entry point (Mangum adapter)
├── app.py                 # Main FastAPI app (940 lines)
│                          #   - Webex webhook handlers
│                          #   - Message routing logic
│                          #   - Adaptive Card templates
│                          #   - Summary pipeline orchestration
│
├── config.py              # Environment variables loader
│                          #   - ServiceNow credentials
│                          #   - Webex bot token
│                          #   - CIRCUIT LLM credentials
│
├── servicenow_client.py   # ServiceNow API integration
│                          #   - get_case_by_number()
│                          #   - get_case_journal_entries()
│                          #   - get_case_emails()
│
├── formatter.py           # Timeline builder
│                          #   - build_timeline()
│                          #   - clean_text()
│                          #   - to_iso()
│
├── summarizer.py          # CIRCUIT LLM integration
│                          #   - build_prompt()
│                          #   - get_access_token()
│                          #   - call_circuit_llm()
│                          #   - summarize_case_with_llm()
│
├── requirements.txt       # Python dependencies
├── deploy.sh              # AWS deployment script
└── .env                   # Environment variables (not in git)
```

---

## How Files Connect

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           FILE DEPENDENCY GRAPH                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

                              lambda_handler.py
                                     │
                    imports app, _summarize_and_flip
                                     │
                                     ▼
                                  app.py
                                     │
           ┌─────────────────────────┼─────────────────────────┐
           │                         │                         │
           ▼                         ▼                         ▼
    servicenow_client.py        formatter.py             summarizer.py
           │                         │                         │
           │                         │                         │
           └─────────────────────────┴─────────────────────────┘
                                     │
                                     ▼
                                config.py
                                     │
                                     ▼
                                  .env
```

### Import Chain

```python
# lambda_handler.py
from app import app, _summarize_and_flip

# app.py
from config import WEBEX_BOT_TOKEN, WEBEX_BOT_EMAIL
from servicenow_client import get_case_by_number, get_case_journal_entries, get_case_emails
from formatter import build_timeline
from summarizer import summarize_case_with_llm

# servicenow_client.py
from config import SERVICENOW_INSTANCE, SERVICENOW_USERNAME, SERVICENOW_PASSWORD

# summarizer.py
from config import CIRCUIT_CLIENT_ID, CIRCUIT_CLIENT_SECRET, CIRCUIT_APP_KEY, ...
```

---

## Request Flow Diagram

### Flow 1: User Sends a Case Number

```
┌──────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐    ┌────────────┐
│  User    │    │    Webex     │    │ AWS Lambda  │    │  ServiceNow  │    │  CIRCUIT   │
│ (Webex)  │    │   Platform   │    │  (FastAPI)  │    │     API      │    │    LLM     │
└────┬─────┘    └──────┬───────┘    └──────┬──────┘    └──────┬───────┘    └─────┬──────┘
     │                 │                   │                  │                  │
     │ 1. "CS0001027"  │                   │                  │                  │
     │────────────────>│                   │                  │                  │
     │                 │                   │                  │                  │
     │                 │ 2. POST /webhook/ │                  │                  │
     │                 │    webex          │                  │                  │
     │                 │──────────────────>│                  │                  │
     │                 │                   │                  │                  │
     │                 │                   │ 3. GET /messages │                  │
     │                 │                   │    /{message_id} │                  │
     │                 │                   │<─────────────────│                  │
     │                 │                   │    (fetch text)  │                  │
     │                 │                   │                  │                  │
     │                 │ 4. POST working   │                  │                  │
     │                 │    card           │                  │                  │
     │<────────────────│<──────────────────│                  │                  │
     │                 │                   │                  │                  │
     │                 │                   │ 5. Invoke Lambda │                  │
     │                 │                   │    async         │                  │
     │                 │                   │────────┐         │                  │
     │                 │                   │        │         │                  │
     │                 │ 6. Return 200     │<───────┘         │                  │
     │                 │<──────────────────│                  │                  │
     │                 │                   │                  │                  │
     │                 │                   │                  │                  │
     │                 │    ═══════════════│══════════════════│══════════════════│═══
     │                 │    ASYNC LAMBDA   │ (runs separately)│                  │
     │                 │    ═══════════════│══════════════════│══════════════════│═══
     │                 │                   │                  │                  │
     │                 │                   │ 7. GET case      │                  │
     │                 │                   │─────────────────>│                  │
     │                 │                   │                  │                  │
     │                 │                   │ 8. Case data     │                  │
     │                 │                   │<─────────────────│                  │
     │                 │                   │                  │                  │
     │                 │                   │ 9. GET journals  │                  │
     │                 │                   │─────────────────>│                  │
     │                 │                   │                  │                  │
     │                 │                   │ 10. Journals     │                  │
     │                 │                   │<─────────────────│                  │
     │                 │                   │                  │                  │
     │                 │                   │ 11. GET emails   │                  │
     │                 │                   │─────────────────>│                  │
     │                 │                   │                  │                  │
     │                 │                   │ 12. Emails       │                  │
     │                 │                   │<─────────────────│                  │
     │                 │                   │                  │                  │
     │                 │                   │ 13. Build timeline                  │
     │                 │                   │ 14. Build prompt │                  │
     │                 │                   │                  │                  │
     │                 │                   │ 15. POST /token  │                  │
     │                 │                   │─────────────────────────────────────>
     │                 │                   │                  │                  │
     │                 │                   │ 16. Access token │                  │
     │                 │                   │<─────────────────────────────────────
     │                 │                   │                  │                  │
     │                 │                   │ 17. POST /chat/  │                  │
     │                 │                   │    completions   │                  │
     │                 │                   │─────────────────────────────────────>
     │                 │                   │                  │                  │
     │                 │                   │ 18. AI summary   │                  │
     │                 │                   │<─────────────────────────────────────
     │                 │                   │                  │                  │
     │                 │ 19. PATCH card    │                  │                  │
     │                 │    (replace with  │                  │                  │
     │<────────────────│<──────────────────│   summary card)  │                  │
     │                 │                   │                  │                  │
```

---

## Code-Level Flow — Step by Step

This section traces **exactly** what happens in the code when a user sends `CS0001027` to the bot.

---

### Step 0 — Lambda Receives the Event

**File:** `lambda_handler.py`
**Function:** `handler(event, context)`

```python
def handler(event, context):
    # Two kinds of events:
    # 1. API Gateway HTTP event → delegate to Mangum (FastAPI)
    # 2. Async summary event → run pipeline directly
    
    if event.get("_async_summary"):
        # This is a self-invoked async event — run the heavy pipeline
        _summarize_and_flip(room_id, case_number, card_message_id)
        return {"status": "ok"}
    
    # Normal HTTP event from API Gateway
    return _mangum(event, context)
```

**What happens:**
- AWS API Gateway receives the webhook POST from Webex
- API Gateway triggers Lambda with an HTTP event
- Mangum adapter converts the event to an ASGI request for FastAPI

---

### Step 1 — Webhook Receives the Message

**File:** `app.py`
**Function:** `webex_webhook(request: Request)`
**Route:** `POST /webhook/webex`

```python
@app.post("/webhook/webex")
async def webex_webhook(request: Request):
    body = await request.json()
    data = body.get("data", {})
    
    message_id = data.get("id")        # ID of the message
    room_id    = data.get("roomId")    # Room where message was sent
```

**What the webhook payload looks like:**
```json
{
  "resource": "messages",
  "event": "created",
  "data": {
    "id": "Y2lzY29...",           // message_id
    "roomId": "Y2lzY29...",       // room_id
    "personEmail": "user@cisco.com"
  },
  "actorId": "Y2lzY29..."
}
```

**Important:** The webhook payload does NOT contain the actual message text — only the `message_id`. We must fetch the text separately.

---

### Step 2 — Guard Checks (Skip Noise)

**File:** `app.py`
**Still inside:** `webex_webhook()`

```python
# Guard 1: Required fields
if not message_id or not room_id:
    return {"status": "ignored", "reason": "Missing message_id or room_id"}

# Guard 2: Skip thread replies
if parent_id:
    return {"status": "ignored", "reason": "Thread reply"}

# Guard 3: Skip if outer email is clearly the bot
if outer_email and is_bot_message(outer_email):
    return {"status": "ignored", "reason": "Bot event"}
```

**Why guards are important:**
- Without guards, the bot can get into infinite loops (responding to itself)
- Webex fires webhooks for ALL messages, including the bot's own messages
- Thread replies can cause duplicate processing

---

### Step 3 — Fetch the Full Message from Webex

**File:** `app.py`
**Function:** `get_webex_message(message_id)`

```python
message = get_webex_message(message_id)

# Inside get_webex_message():
def get_webex_message(message_id: str):
    resp = requests.get(
        f"https://webexapis.com/v1/messages/{message_id}",
        headers={"Authorization": f"Bearer {WEBEX_BOT_TOKEN}"}
    )
    return resp.json()
```

**What we get back:**
```json
{
  "id": "Y2lzY29...",
  "roomId": "Y2lzY29...",
  "personEmail": "jgorle@cisco.com",
  "text": "CS0001027",
  "created": "2026-04-21T10:30:00.000Z"
}
```

Now we have the actual message text: `"CS0001027"`

---

### Step 4 — More Guard Checks

**File:** `app.py`
**Still inside:** `webex_webhook()`

```python
fetched_email = message.get("personEmail", "").lower()
text = message.get("text", "").strip()

# Guard 4: Skip bot's own messages
if is_bot_message(fetched_email):
    return {"status": "ignored", "reason": "Bot event"}

# Guard 5: Skip echoed card fallback text
if _is_noise(text):
    return {"status": "ignored", "reason": "Noise / bot echo"}
```

**What `is_bot_message()` checks:**
```python
def is_bot_message(email: str) -> bool:
    if email == WEBEX_BOT_EMAIL.lower():
        return True
    if email.endswith(".bot"):
        return True
    if "@webex.bot" in email:
        return True
    return False
```

---

### Step 5 — Route the Message

**File:** `app.py`
**Function:** `_route_message(room_id, text, user_email)`

```python
return _route_message(room_id, text, user_email=fetched_email)

# Inside _route_message():
def _route_message(room_id: str, text: str, user_email: str = ""):
    text_stripped = text.strip()
    text_lower = text_stripped.lower()
    
    # 5a. Welcome (first contact)
    _maybe_send_welcome(room_id, user_email)
    
    # 5b. Exit commands
    if text_lower in {"exit", "quit", "close"}:
        send_text(room_id, "Closed ✅ ...")
        return {"status": "ok"}
    
    # 5c. Bare case number (e.g. "CS0001027")
    if is_bare_case_number(text_stripped):
        case_number = text_stripped.upper()
        # Show working card immediately
        card_id = send_card(room_id, _working_card(case_number))
        # Fire async Lambda invocation
        _invoke_summary_async(room_id, case_number, card_id)
        return {"status": "ok", "case_number": case_number}
    
    # 5d. "summarize CS..." command
    if text_lower.startswith("summarize"):
        direct_case = extract_case_number(text_stripped)
        if direct_case:
            card_id = send_card(room_id, _working_card(direct_case))
            _invoke_summary_async(room_id, direct_case, card_id)
            return {"status": "ok", "case_number": direct_case}
    
    # 5e. Fallback — show input form
    send_card(room_id, _input_card())
    return {"status": "ok"}
```

**Routing priority:**
1. `exit` / `quit` / `close` → send goodbye text
2. `CS0001027` (bare case number) → generate summary
3. `summarize CS0001027` → generate summary
4. Anything else → show input form card

---

### Step 6 — Send Working Card (Instant Feedback)

**File:** `app.py`
**Function:** `send_card(room_id, card_content)`

```python
card_id = send_card(room_id, _working_card(case_number))

# Inside send_card():
def send_card(room_id: str, card_content: dict) -> str:
    resp = requests.post(
        "https://webexapis.com/v1/messages",
        headers={"Authorization": f"Bearer {WEBEX_BOT_TOKEN}"},
        json={
            "roomId": room_id,
            "text": "Generating summary…",  # fallback for old clients
            "attachments": [{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": card_content
            }]
        }
    )
    return resp.json().get("id")  # card_id for later replacement
```

**Working card looks like:**
```
⏳ Generating summary for CS0001027…
Fetching the case from ServiceNow and building the timeline.
This usually takes a few seconds — the card will update automatically.
```

---

### Step 7 — Fire Async Lambda Invocation

**File:** `app.py`
**Function:** `_invoke_summary_async(room_id, case_number, card_message_id)`

```python
_invoke_summary_async(room_id, case_number, card_id)

# Inside _invoke_summary_async():
def _invoke_summary_async(room_id: str, case_number: str, card_message_id: str):
    payload = {
        "_async_summary": True,
        "room_id": room_id,
        "case_number": case_number,
        "card_message_id": card_message_id
    }
    
    boto3.client("lambda").invoke(
        FunctionName=_FUNCTION_NAME,
        InvocationType="Event",  # async — returns immediately
        Payload=json.dumps(payload)
    )
```

**Why async?**
- API Gateway has a 29-second timeout
- The full pipeline (ServiceNow + LLM) can take 10-30 seconds
- By invoking Lambda asynchronously, the webhook returns 200 immediately
- The heavy work runs in a separate Lambda execution with full 120-second timeout

---

### Step 8 — Webhook Returns 200

**File:** `app.py`
**Function:** `webex_webhook()` returns

```python
return {"status": "ok", "case_number": case_number}
```

**At this point:**
- The user sees the "working card" with the loading message
- The webhook has returned 200 to Webex (within 3 seconds)
- A new Lambda invocation is running the heavy pipeline in the background

---

### Step 9 — Async Lambda Handles the Summary Pipeline

**File:** `lambda_handler.py`
**Function:** `handler()` with `_async_summary` event

```python
def handler(event, context):
    if event.get("_async_summary"):
        room_id = event["room_id"]
        case_number = event["case_number"]
        card_message_id = event.get("card_message_id")
        
        # Run the heavy pipeline
        _summarize_and_flip(room_id, case_number, card_message_id)
        return {"status": "ok"}
```

---

### Step 10 — Run the Summary Pipeline

**File:** `app.py`
**Function:** `_summarize_and_flip(room_id, case_number, card_message_id)`

```python
def _summarize_and_flip(room_id: str, case_number: str, card_message_id: str):
    try:
        # Run full pipeline
        result = get_summary(case_number)
        summary = format_reply(result)
        sum_card = _summary_card(case_number, summary)
        
        # Replace the working card with summary card
        if card_message_id:
            replace_card(card_message_id, sum_card)
        else:
            send_card(room_id, sum_card)
            
    except Exception as exc:
        # Never fail silently — tell the user something went wrong
        send_text(room_id, f"❌ Something went wrong generating the summary for {case_number}.")
```

---

### Step 11 — Get Summary (Main Pipeline)

**File:** `app.py`
**Function:** `get_summary(case_number)`

```python
def get_summary(case_number: str) -> dict:
    # 11a. Fetch case record
    case_record = get_case_by_number(case_number)
    if not case_record:
        return {"case_number": case_number, "summary": "❌ Case not found"}
    
    # 11b. Resolve sys_id
    sys_id = case_record.get("sys_id")
    if isinstance(sys_id, dict):
        sys_id = sys_id.get("value")
    
    # 11c. Fetch journal + email history
    journal_entries = get_case_journal_entries(sys_id)
    email_entries = get_case_emails(sys_id)
    
    # 11d. Build timeline
    timeline = build_timeline(journal_entries, email_entries)
    
    # 11e. Call LLM
    llm_summary = summarize_case_with_llm(case_record, timeline)
    
    return {"case_number": case_number, "summary": llm_summary}
```

---

### Step 12 — Fetch Case from ServiceNow

**File:** `servicenow_client.py`
**Function:** `get_case_by_number(case_number)`

```python
def get_case_by_number(case_number: str):
    url = f"https://{SERVICENOW_INSTANCE}/api/now/table/sn_customerservice_case"
    params = {
        "sysparm_query": f"number={case_number}",
        "sysparm_fields": "sys_id,number,short_description,description,state,priority,...",
        "sysparm_limit": "1",
        "sysparm_display_value": "all"
    }
    
    resp = requests.get(url, auth=(USERNAME, PASSWORD), params=params)
    results = resp.json().get("result", [])
    return results[0] if results else None
```

**What we get back:**
```json
{
  "sys_id": "abc123...",
  "number": "CS0001027",
  "short_description": "Password reset link expired",
  "description": "User reports password reset link showing Page Expired...",
  "state": "Resolved",
  "priority": "2 - High",
  "assignment_group": "CX Support"
}
```

---

### Step 13 — Fetch Journal Entries

**File:** `servicenow_client.py`
**Function:** `get_case_journal_entries(sys_id)`

```python
def get_case_journal_entries(sys_id: str) -> list:
    url = f"https://{SERVICENOW_INSTANCE}/api/now/table/sys_journal_field"
    params = {
        "sysparm_query": f"element_id={sys_id}^elementINcomments,work_notes^ORDERBYsys_created_on",
        "sysparm_fields": "sys_created_on,element,value,sys_created_by"
    }
    
    resp = requests.get(url, auth=AUTH, params=params)
    return resp.json().get("result", [])
```

**What we get back (example):**
```json
[
  {
    "sys_created_on": "2026-04-13 10:00:00",
    "element": "comments",
    "value": "My password reset link expired with Page Expired error",
    "sys_created_by": "user@company.com"
  },
  {
    "sys_created_on": "2026-04-13 14:30:00",
    "element": "work_notes",
    "value": "Investigating the issue. Reproduced in test environment.",
    "sys_created_by": "support@cisco.com"
  }
]
```

---

### Step 14 — Fetch Emails

**File:** `servicenow_client.py`
**Function:** `get_case_emails(sys_id)`

```python
def get_case_emails(sys_id: str) -> list:
    url = f"https://{SERVICENOW_INSTANCE}/api/now/table/sys_email"
    params = {
        "sysparm_query": f"instance={sys_id}^target_table=sn_customerservice_case^ORDERBYsys_created_on",
        "sysparm_fields": "sys_created_on,type,subject,body_text"
    }
    
    resp = requests.get(url, auth=AUTH, params=params)
    return resp.json().get("result", [])
```

---

### Step 15 — Build Timeline

**File:** `formatter.py`
**Function:** `build_timeline(journal_entries, email_entries)`

```python
def build_timeline(journal_entries, email_entries):
    timeline = []
    
    # Process journal entries
    for item in journal_entries:
        timeline.append({
            "type": "comment" if item["element"] == "comments" else "work_note",
            "speaker": "customer" if item["element"] == "comments" else "support_engineer",
            "timestamp": to_iso(item["sys_created_on"]),
            "text": clean_text(item["value"])
        })
    
    # Process emails
    for email in email_entries:
        timeline.append({
            "type": "email",
            "speaker": "customer",
            "timestamp": to_iso(email["sys_created_on"]),
            "text": clean_text(email.get("body_text", ""))
        })
    
    # Sort chronologically
    timeline.sort(key=lambda x: x["timestamp"])
    return timeline
```

**What `clean_text()` does:**
```python
def clean_text(text: str) -> str:
    if not text:
        return ""
    return " ".join(text.replace("\r", " ").replace("\n", " ").split())
```

---

### Step 16 — Build LLM Prompt

**File:** `summarizer.py`
**Function:** `build_prompt(case_data, timeline)`

```python
def build_prompt(case_data, timeline):
    # Format timeline as numbered list
    lines = []
    for i, item in enumerate(timeline, start=1):
        lines.append(f"{i}. [{item['timestamp']}] {item['speaker']}: {item['text']}")
    timeline_text = "\n".join(lines)
    
    return f"""Summarize this ServiceNow case for an engineer picking up the ticket.
They need to understand the situation in 30 seconds without reading the full timeline.

RULES:
1. Use ONLY facts from the data below. Never invent or assume.
2. Deduplicate: if the same thing is said multiple times, mention it once.
3. No email addresses, no personal names, no PII.
4. Keep each bullet to one short sentence.
5. If something is not stated, omit it entirely.

Case: {case_data['number']} | Title: {case_data.get('short_description', '')}
State: {case_data.get('state', '')} | Priority: {case_data.get('priority', '')}
Description: {case_data.get('description', '')}

Timeline (oldest first):
{timeline_text}

Return EXACTLY this format:

Problem:
<1-2 sentences: what is broken and who is affected>

Root Cause:
<1 sentence if identified, otherwise omit>

What Was Done:
- <each distinct action taken>

Current Status:
<1 sentence: where the ticket stands now>
"""
```

---

### Step 17 — Get OAuth Token from Cisco

**File:** `summarizer.py`
**Function:** `get_access_token()`

```python
def get_access_token() -> str:
    # Base64 encode client_id:client_secret
    creds = f"{CIRCUIT_CLIENT_ID}:{CIRCUIT_CLIENT_SECRET}"
    encoded = base64.b64encode(creds.encode()).decode()
    
    response = requests.post(
        CIRCUIT_TOKEN_URL,  # https://id.cisco.com/oauth2/default/v1/token
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded}"
        },
        data={"grant_type": "client_credentials"}
    )
    
    return response.json()["access_token"]
```

---

### Step 18 — Call CIRCUIT LLM

**File:** `summarizer.py`
**Function:** `call_circuit_llm(prompt)`

```python
def call_circuit_llm(prompt: str) -> str:
    access_token = get_access_token()
    url = f"{CIRCUIT_CHAT_BASE_URL}/{CIRCUIT_MODEL}/chat/completions"
    # Example: https://chat-ai.cisco.com/openai/deployments/gpt-5-nano/chat/completions
    
    body = {
        "messages": [
            {
                "role": "system",
                "content": "You produce concise, factual ticket summaries for support engineers. Never repeat information. Never hallucinate."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "user": json.dumps({"appkey": CIRCUIT_APP_KEY}),
        "temperature": 0.05,
        "max_tokens": 500
    }
    
    response = requests.post(
        url,
        headers={
            "Content-Type": "application/json",
            "api-key": access_token
        },
        json=body
    )
    
    return response.json()["choices"][0]["message"]["content"]
```

---

### Step 19 — Parse and Format Summary

**File:** `summarizer.py`
**Function:** `summarize_case_with_llm(case_data, timeline)`

```python
def summarize_case_with_llm(case_data, timeline):
    prompt = build_prompt(case_data, timeline)
    raw_summary = call_circuit_llm(prompt)
    return _prepend_case_context(raw_summary, case_data)

def _prepend_case_context(summary_text, case_data):
    # Build metadata line
    meta_parts = []
    if case_data.get("priority"):
        meta_parts.append(f"Priority: {case_data['priority']}")
    if case_data.get("state"):
        meta_parts.append(f"State: {case_data['state']}")
    if case_data.get("assignment_group"):
        meta_parts.append(f"Group: {case_data['assignment_group']}")
    
    meta_line = " | ".join(meta_parts)
    
    return f"{case_data['number']} — {meta_line}\n\n{summary_text}"
```

---

### Step 20 — Replace Working Card with Summary Card

**File:** `app.py`
**Function:** `replace_card(message_id, card_content)`

```python
def replace_card(message_id: str, card_content: dict):
    requests.patch(
        f"https://webexapis.com/v1/messages/{message_id}",
        headers={"Authorization": f"Bearer {WEBEX_BOT_TOKEN}"},
        json={
            "text": f"Summary — {case_number}",
            "attachments": [{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": card_content
            }]
        }
    )
```

**The working card transforms into the summary card** — no new message, just an in-place update!

---

## Full Call Chain Summary

```
User sends "CS0001027" in Webex
     │
     ▼
Webex fires webhook to API Gateway
     │
     ▼
lambda_handler.handler(event, context)
     │
     ▼
_mangum(event, context)  →  FastAPI
     │
     ▼
webex_webhook(request)                           ← Step 1-4: Receive & guard
     │
     ├── get_webex_message(message_id)           ← Step 3: Fetch message text
     │
     └── _route_message(room_id, text)           ← Step 5: Route
            │
            ├── send_card(_working_card)         ← Step 6: Instant feedback
            │
            └── _invoke_summary_async()          ← Step 7: Fire async Lambda
                   │
                   ▼
            lambda_handler.handler({_async_summary: true})   ← Step 9
                   │
                   ▼
            _summarize_and_flip(room_id, case_number, card_id)  ← Step 10
                   │
                   ▼
            get_summary(case_number)                         ← Step 11
                   │
                   ├── get_case_by_number()                  ← Step 12: servicenow_client.py
                   ├── get_case_journal_entries()            ← Step 13
                   ├── get_case_emails()                     ← Step 14
                   │
                   ▼
            build_timeline(journals, emails)                 ← Step 15: formatter.py
                   │
                   ▼
            summarize_case_with_llm(case_data, timeline)     ← Step 16-18: summarizer.py
                   │
                   ├── build_prompt()                        ← Step 16
                   ├── get_access_token()                    ← Step 17
                   └── call_circuit_llm()                    ← Step 18
                          │
                          ▼
            replace_card(card_id, _summary_card)             ← Step 20
                   │
                   ▼
            User sees summary card in Webex ✅
```

---

## Key Functions Reference

| File | Function | Purpose |
|------|----------|---------|
| `lambda_handler.py` | `handler()` | Lambda entry point — routes HTTP vs async events |
| `app.py` | `webex_webhook()` | Handles incoming Webex messages |
| `app.py` | `webex_card_action_webhook()` | Handles Adaptive Card button clicks |
| `app.py` | `_route_message()` | Routes text to appropriate handler |
| `app.py` | `get_summary()` | Main pipeline orchestrator |
| `app.py` | `_summarize_and_flip()` | Async pipeline + card replacement |
| `app.py` | `send_card()` | POST new Adaptive Card to Webex |
| `app.py` | `replace_card()` | PATCH existing card in-place |
| `app.py` | `_invoke_summary_async()` | Fire-and-forget Lambda invocation |
| `servicenow_client.py` | `get_case_by_number()` | Fetch case record from ServiceNow |
| `servicenow_client.py` | `get_case_journal_entries()` | Fetch comments + work notes |
| `servicenow_client.py` | `get_case_emails()` | Fetch email history |
| `formatter.py` | `build_timeline()` | Merge & sort all activity chronologically |
| `formatter.py` | `clean_text()` | Strip HTML, collapse whitespace |
| `summarizer.py` | `build_prompt()` | Craft the LLM prompt |
| `summarizer.py` | `get_access_token()` | OAuth2 client credentials flow |
| `summarizer.py` | `call_circuit_llm()` | POST to CIRCUIT chat completions |
| `summarizer.py` | `summarize_case_with_llm()` | Full LLM pipeline |

---

## Adaptive Cards Templates

### Welcome Card

```python
def _welcome_card(user_email: str = "") -> dict:
    return {
        "type": "AdaptiveCard",
        "version": "1.2",
        "body": [
            {"type": "TextBlock", "text": "👋 Hi! I'm the Case Summary Bot 🤖", "weight": "Bolder"},
            {"type": "TextBlock", "text": "I can generate AI-powered summaries of your ServiceNow cases..."},
            {"type": "TextBlock", "text": "👇 Click Get Started to open the input form."}
        ],
        "actions": [
            {"type": "Action.Submit", "title": "Get Started", "data": {"action": "open_input_card"}}
        ]
    }
```

### Input Card

```python
def _input_card() -> dict:
    return {
        "type": "AdaptiveCard",
        "body": [
            {"type": "TextBlock", "text": "🔍 Case Summary Bot"},
            {"type": "Input.Text", "id": "case_number", "placeholder": "e.g. CS0001051"}
        ],
        "actions": [
            {"type": "Action.Submit", "title": "Summarize", "data": {"action": "summarize_case"}},
            {"type": "Action.Submit", "title": "Cancel", "data": {"action": "exit_menu"}}
        ]
    }
```

### Working Card

```python
def _working_card(case_number: str) -> dict:
    return {
        "type": "AdaptiveCard",
        "body": [
            {"type": "TextBlock", "text": f"⏳ Generating summary for {case_number}…"},
            {"type": "TextBlock", "text": "Fetching the case from ServiceNow and building the timeline..."}
        ]
    }
```

### Summary Card

```python
def _summary_card(case_number: str, summary_text: str) -> dict:
    sections = _parse_summary_sections(summary_text)
    # Builds formatted card with bold headers for each section
    return {
        "type": "AdaptiveCard",
        "body": [...],  # Formatted sections
        "actions": [
            {"type": "Action.Submit", "title": "Summarize another", "data": {"action": "open_input_card"}},
            {"type": "Action.Submit", "title": "Close", "data": {"action": "close_summary"}}
        ]
    }
```

---

## Environment Variables

### `.env` file

```bash
# ServiceNow
SERVICENOW_INSTANCE=dev380388.service-now.com
SERVICENOW_USERNAME=admin
SERVICENOW_PASSWORD=********

# Webex Bot
WEBEX_BOT_TOKEN=NzQ2YzM5ZDctODVhMi00NTk...
WEBEX_BOT_EMAIL=case-summary-bot@webex.bot

# Cisco CIRCUIT LLM
CIRCUIT_CLIENT_ID=0oatuvf1hxeWbWSbT5d7
CIRCUIT_CLIENT_SECRET=Dni7MPubYXGnMiQgZNHb...
CIRCUIT_APP_KEY=egai-prd-cx-123212180-summarize-1774871716656
CIRCUIT_MODEL=gpt-5-nano
CIRCUIT_TOKEN_URL=https://id.cisco.com/oauth2/default/v1/token
CIRCUIT_CHAT_BASE_URL=https://chat-ai.cisco.com/openai/deployments
```

### `config.py` loader

```python
import os
from dotenv import load_dotenv

load_dotenv()

SERVICENOW_INSTANCE   = os.getenv("SERVICENOW_INSTANCE")
SERVICENOW_USERNAME   = os.getenv("SERVICENOW_USERNAME")
SERVICENOW_PASSWORD   = os.getenv("SERVICENOW_PASSWORD")

WEBEX_BOT_TOKEN       = os.getenv("WEBEX_BOT_TOKEN")
WEBEX_BOT_EMAIL       = os.getenv("WEBEX_BOT_EMAIL")

CIRCUIT_CLIENT_ID     = os.getenv("CIRCUIT_CLIENT_ID")
CIRCUIT_CLIENT_SECRET = os.getenv("CIRCUIT_CLIENT_SECRET")
CIRCUIT_APP_KEY       = os.getenv("CIRCUIT_APP_KEY")
CIRCUIT_MODEL         = os.getenv("CIRCUIT_MODEL", "gpt-5-nano")
CIRCUIT_TOKEN_URL     = os.getenv("CIRCUIT_TOKEN_URL", "https://id.cisco.com/oauth2/default/v1/token")
CIRCUIT_CHAT_BASE_URL = os.getenv("CIRCUIT_CHAT_BASE_URL", "https://chat-ai.cisco.com/openai/deployments")
```

---

## Deployment

### AWS Lambda + API Gateway

```bash
# 1. Install dependencies to vendor/
pip install -r requirements.txt -t vendor/

# 2. Create deployment package
zip -r deployment.zip . -x "*.git*" -x "*.env*" -x "__pycache__/*"

# 3. Upload to Lambda
aws lambda update-function-code \
    --function-name case-summary-bot \
    --zip-file fileb://deployment.zip

# 4. Set environment variables in Lambda console
# 5. Configure API Gateway trigger
# 6. Register Webex webhook pointing to API Gateway URL
```

### Webex Webhook Registration

```bash
curl -X POST "https://webexapis.com/v1/webhooks" \
  -H "Authorization: Bearer {BOT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Case Summary Bot - Messages",
    "targetUrl": "https://abc123.execute-api.us-east-1.amazonaws.com/webhook/webex",
    "resource": "messages",
    "event": "created"
  }'
```

---

## Summary

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| Lambda Entry | `lambda_handler.py` | 52 | AWS Lambda adapter + async handler |
| Main App | `app.py` | 940 | FastAPI webhooks, routing, cards |
| Config | `config.py` | 33 | Environment variable loader |
| ServiceNow | `servicenow_client.py` | 80 | Case/journal/email API calls |
| Formatter | `formatter.py` | 80 | Timeline builder |
| Summarizer | `summarizer.py` | 223 | LLM prompt + CIRCUIT integration |
| **Total** | | **~1400** | |

---

**Author:** Jansi Gorle  
**Team:** CX (Customer Experience)  
**Date:** April 2026
