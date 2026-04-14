# 🤖 Case Summary Bot — AI-Powered ServiceNow Summarization for Webex

> **Author:** Jansi Gorle · Technical Consulting Engineer · CX  
> **Date:** April 2026 · Proof of Concept  
> **GitHub:** [github.com/GorleJansi/Case-Summary-Bot](https://github.com/GorleJansi/Case-Summary-Bot)

---

## 📌 What Is This?

**Case Summary Bot** is an AI-powered Webex chatbot that instantly summarizes ServiceNow support cases.

An engineer types a case number (e.g. `CS0001028`) in Webex → the bot fetches the full case history from ServiceNow, builds a chronological timeline, sends it to Cisco's CIRCUIT LLM, and delivers a structured AI summary — all in **5–8 seconds**.

> 💡 **One sentence:** _"Instead of spending 15–30 minutes reading through a long case, just ask the bot and get a summary in seconds."_

---

## 🎯 Problem We're Solving

| Pain Point | Impact |
|:-----------|:-------|
| ⏱️ Engineers spend **15–30 min** reading long case histories | Slower response times |
| 📄 Cases have **hundreds** of journal entries, emails, work notes | Information overload |
| 🔄 Constant context-switching between **ServiceNow ↔ Webex** | Lost productivity |
| 😓 Hard to get a **quick status update** for escalation meetings | Delayed escalations |
| 📉 Manual reading doesn't scale across **multiple cases** | Poor customer satisfaction |

---

## ✅ How It Works — The User Experience

```
   Step 1                  Step 2                  Step 3                  Step 4
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  👋 WELCOME     │   │  🔍 INPUT       │   │  ⏳ WORKING     │   │  📋 SUMMARY     │
│                 │   │                 │   │                 │   │                 │
│  Hi! I'm the   │   │  Enter a case   │   │  Generating     │   │  CS0001028      │
│  Case Summary   │──▶│  number:        │──▶│  summary for    │──▶│                 │
│  Bot 🤖         │   │                 │   │  CS0001028...   │   │  Problem:       │
│                 │   │  ┌───────────┐  │   │                 │   │  Users see 404  │
│  I generate     │   │  │CS0001028  │  │   │  Fetching from  │   │                 │
│  AI summaries   │   │  └───────────┘  │   │  ServiceNow &   │   │  Root Cause:    │
│  of ServiceNow  │   │                 │   │  calling AI...  │   │  CDN stale      │
│  cases.         │   │  [Summarize]    │   │                 │   │                 │
│                 │   │  [Cancel]       │   │  ⏱️ ~5-8 sec     │   │  Status:        │
│  [Get Started]  │   │                 │   │                 │   │  ✅ Resolved     │
└─────────────────┘   └─────────────────┘   └─────────────────┘   └─────────────────┘
    First contact        User enters case     Instant feedback       AI summary card
                                               (<2 seconds)         replaces in-place
```

**Key UX Details:**
- Cards **replace each other in-place** — no card spam in the chat
- Working card appears **instantly** (<2 seconds) so the user knows it's processing
- Summary card **swaps in** once the AI responds (5–8 seconds total)
- User can type just `CS0001028` or `summarize CS0001028` — both work

---

## 🏗️ Architecture

```
┌──────────────────┐
│   Engineer in     │
│   Webex (DM)      │
│   types CS0001028 │
└────────┬─────────┘
         │  Webex fires webhook (HTTP POST)
         ▼
┌──────────────────────────────────────────┐
│         AWS API Gateway (HTTP API v2)    │
│                                          │
│  Routes:                                 │
│    POST /webhook/webex       → Lambda    │
│    POST /webhook/webex/card-action       │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│             AWS Lambda                   │
│   Runtime: Python 3.13 | 256 MB | 120s  │
│                                          │
│   ┌─ EXECUTION 1 (fast, ~1-2s) ───────┐ │
│   │  Receive webhook                   │ │
│   │  Validate message                  │ │
│   │  Send "⏳ Generating..." card      │ │
│   │  Invoke ITSELF async              │ │
│   │  Return 200 to Webex instantly    │ │
│   └────────────────────────────────────┘ │
│                                          │
│   ┌─ EXECUTION 2 (heavy pipeline) ────┐ │
│   │  Fetch case from ServiceNow       │ │
│   │  Fetch journals + emails          │ │
│   │  Build chronological timeline     │ │
│   │  Call CIRCUIT LLM for summary     │ │
│   │  Replace working card → summary   │ │
│   └────────────────────────────────────┘ │
└──────┬───────────────┬───────────────────┘
       │               │
       ▼               ▼
┌──────────────┐ ┌─────────────────────┐
│ ServiceNow   │ │ Cisco CIRCUIT LLM   │
│ CSM REST API │ │ (gpt-5-nano)        │
│              │ │                     │
│ Tables:      │ │ OAuth2: id.cisco.com│
│ • cases      │ │ Chat: chat-ai.cisco │
│ • journals   │ │                     │
│ • emails     │ │ Structured summary  │
└──────────────┘ └─────────────────────┘
```

### 🔑 Why the Async Self-Invocation Pattern?

| Challenge | Solution |
|:----------|:---------|
| API Gateway has a **30-second timeout** | Lambda splits work into **two executions** |
| Full pipeline can take **10–20 seconds** | **Execution 1** returns to Webex in 1–2s |
| Webex would show "webhook failed" | **Execution 2** runs the heavy pipeline with a full **120s timeout** |

This pattern gives the user **instant feedback** while the heavy work happens in the background.

---

## 🔄 Request Flow — Step by Step

```
STEP 1 ──▶  👤 User sends "CS0001028" in Webex DM
            │
STEP 2 ──▶  💬 Webex fires HTTP POST webhook to API Gateway
            │   Body: { data: { id: "<message_id>", roomId: "<room_id>" } }
            │
STEP 3 ──▶  ⚡ Lambda EXECUTION 1 receives the event
            │   lambda_handler.handler() → Mangum → FastAPI
            │
STEP 4 ──▶  🔍 webex_webhook() runs 5 guard checks:
            │   ✓ Has message ID?  ✓ Not a thread reply?
            │   ✓ Not from a bot?  ✓ Can read message?  ✓ Not noise/echo?
            │
STEP 5 ──▶  🧭 _route_message() identifies "CS0001028" as a case number
            │
STEP 6 ──▶  📨 send_card() sends "⏳ Generating summary..." working card
            │
STEP 7 ──▶  🚀 _invoke_summary_async() invokes Lambda AGAIN (Event mode)
            │   boto3.client("lambda").invoke(InvocationType="Event")
            │   └─ Returns HTTP 200 to Webex immediately (~1-2s total)
            │
STEP 8 ──▶  ⚡ Lambda EXECUTION 2 starts (separate invocation)
            │   handler() sees _async_summary=true → calls _summarize_and_flip()
            │
STEP 9 ──▶  📊 Pipeline runs:
            │   a. get_case_by_number("CS0001028")    → ServiceNow case metadata
            │   b. get_case_journal_entries(sys_id)    → comments + work notes
            │   c. get_case_emails(sys_id)             → email threads
            │   d. build_timeline(journals, emails)    → sorted chronological list
            │   e. summarize_case_with_llm(case, tl)   → CIRCUIT LLM call
            │
STEP 10 ──▶ 📋 replace_card() swaps the ⏳ working card → ✅ summary card
            │   PATCH https://webexapis.com/v1/messages/{card_id}
            │
            └──▶ 👤 Engineer sees the AI summary (total: ~5-8 seconds)
```

---

## 🧠 LLM Prompt Engineering

The bot doesn't just dump data into the LLM. It crafts a **structured prompt** with strict rules:

### What Goes INTO the Prompt

```
┌─────────────────────────────────────────────────────────┐
│  SYSTEM PROMPT                                          │
│  "You are a support case analyst. Summarize the case    │
│   in a structured format..."                            │
├─────────────────────────────────────────────────────────┤
│  USER PROMPT                                            │
│                                                         │
│  Case: CS0001028                                        │
│  Priority: 1-Critical | State: New                      │
│  Account: Acme Corp | Group: Network Support            │
│                                                         │
│  Timeline:                                              │
│  1. [2026-01-15T10:00Z] customer: "Login shows 404"     │
│  2. [2026-01-15T11:30Z] engineer: "Checked CDN logs"    │
│  3. [2026-01-15T14:00Z] customer: "Working now, thanks" │
│  ... (all entries, chronologically sorted)              │
└─────────────────────────────────────────────────────────┘
```

### Rules Enforced in the Prompt

| Rule | Why |
|:-----|:----|
| ✅ **No PII** — no names, emails, or phone numbers | Data privacy compliance |
| ✅ **No hallucination** — only facts from the timeline | Trust & accuracy |
| ✅ **Deduplicate** similar entries | Cleaner output |
| ✅ **Under 200 words** | Concise, scannable summaries |
| ✅ **Structured sections** | Consistent format every time |

### What Comes OUT of the LLM

```
📌 Problem:
   Users see a 404 error on the Webex Connect login page

🔍 Root Cause:
   CDN edge node serving stale configuration after a deployment

🔧 What Was Done:
   • Analyzed HAR capture data from affected users
   • Identified stale cache on CDN edge nodes
   • Forced CDN cache purge across all regions

📊 Current Status:
   Issue resolved. Login page serving correctly.

⏭️ Next Steps:
   Monitoring for 24 hours. Will update CDN TTL configuration.
```

---

## 📁 Project Structure — 6 Source Files

```
cPaas-sNow-summarisation-agent/
│
├── lambda_handler.py      ←  Lambda entrypoint (43 lines)
│                              Routes HTTP events vs async summary events
│
├── app.py                 ←  Core application (940 lines)
│                              Webhooks, Adaptive Cards, routing, async invoke
│
├── config.py              ←  Environment variable loader (32 lines)
│                              Loads secrets from env vars + vendor/ path
│
├── servicenow_client.py   ←  ServiceNow REST client (80 lines)
│                              Fetches cases, journal entries, emails
│
├── summarizer.py          ←  CIRCUIT LLM integration (222 lines)
│                              OAuth2 token, prompt engineering, AI completion
│
├── formatter.py           ←  Timeline builder (79 lines)
│                              Merges & sorts journal + email entries
│
├── deploy.sh              ←  One-command build & deploy script
├── requirements.txt       ←  Python dependencies (16 packages)
└── .env                   ←  Secrets (never committed to git)
```

### How the Files Connect

```
lambda_handler.py
  │
  ├─── [HTTP event] ──▶ Mangum ──▶ FastAPI (app.py)
  │                                    │
  │                                    ├── webex_webhook()
  │                                    │     └── _route_message()
  │                                    │           ├── send_card(_working_card())
  │                                    │           └── _invoke_summary_async()
  │                                    │
  │                                    └── webex_card_action_webhook()
  │                                          └── (handles button clicks)
  │
  └─── [async event] ──▶ _summarize_and_flip()
                              │
                              ├── servicenow_client.py
                              │     ├── get_case_by_number()
                              │     ├── get_case_journal_entries()
                              │     └── get_case_emails()
                              │
                              ├── formatter.py
                              │     └── build_timeline()
                              │
                              ├── summarizer.py
                              │     ├── build_prompt()
                              │     ├── get_access_token()  ← OAuth2 from id.cisco.com
                              │     └── call_circuit_llm()  ← POST to chat-ai.cisco.com
                              │
                              └── replace_card(_summary_card())
```

---

## ⚙️ Tech Stack

| Layer | Technology | Why This Choice |
|:------|:-----------|:----------------|
| **Runtime** | Python 3.13 on AWS Lambda | Serverless, pay-per-use, no servers to manage |
| **Web Framework** | FastAPI + Mangum | Modern async framework + Lambda ASGI adapter |
| **API Gateway** | AWS HTTP API v2 | Auto-scaling webhook endpoint |
| **Chat Platform** | Webex Adaptive Cards v1.2 | Rich interactive UI directly in Webex |
| **Ticketing** | ServiceNow CSM REST API | Industry-standard ITSM, full REST access |
| **AI / LLM** | Cisco CIRCUIT (gpt-5-nano) | Internal AI gateway, Cisco Confidential safe |
| **Auth** | Cisco ID OAuth2 (client_credentials) | Automated token acquisition, no manual login |
| **Deployment** | One-command `deploy.sh` | `zip` → `aws lambda update-function-code` |

---

## 🏗️ Infrastructure Details

### AWS Hosting

| Resource | Details |
|:---------|:--------|
| Lambda Function | `cPaas-sNow-summarisation-agent` |
| Region | `us-east-1` |
| Runtime | Python 3.13 |
| Memory | 256 MB |
| Timeout | 120 seconds |
| Handler | `lambda_handler.handler` |
| API Gateway | `https://fe4puvvg5j.execute-api.us-east-1.amazonaws.com` |

### Webex Bot

| Item | Details |
|:-----|:--------|
| Bot Name | Case Summary Bot |
| Bot Email | `Case_Summary_Bot@webex.bot` |
| Registered at | [developer.webex.com/my-apps](https://developer.webex.com/my-apps) |
| Token Type | Non-expiring bot token |

### ServiceNow Instance

| Item | Details |
|:-----|:--------|
| Instance | `dev380388.service-now.com` |
| Type | Personal Developer Instance (PDI) |
| Tables Used | `sn_customerservice_case`, `sys_journal_field`, `sys_email` |
| Auth | Basic Auth (admin) |

### CIRCUIT LLM (Cisco Internal AI)

| Item | Details |
|:-----|:--------|
| Portal | [EGAI Portal](https://egai.cisco.com) (Cisco internal) |
| Model | `gpt-5-nano` (Free Fair Use tier) |
| Token Endpoint | `https://id.cisco.com/oauth2/default/v1/token` |
| Chat API | `https://chat-ai.cisco.com/openai/deployments` |
| Data Classification | Cisco Confidential |

---

## 🚀 Deployment

### One-Command Deploy

```bash
bash deploy.sh
```

### What `deploy.sh` Does

```
Step 1:  pip install → installs dependencies for Linux x86_64 into /tmp/lambda_linux_build/
Step 2:  cp → copies the 6 source files into the build directory
Step 3:  zip → creates /tmp/lambda_deploy.zip
Step 4:  aws lambda update-function-code → uploads the zip to Lambda
```

### IAM Permissions Required

| Permission | Why |
|:-----------|:----|
| `AWSLambdaBasicExecutionRole` | CloudWatch Logs for debugging |
| `lambda:InvokeFunction` (on itself) | Async self-invocation pattern |

---

## 🔧 Environment Variables

All secrets are stored as **Lambda environment variables** — never in code.

| Variable | Example | Purpose |
|:---------|:--------|:--------|
| `SERVICENOW_INSTANCE` | `dev380388.service-now.com` | ServiceNow hostname |
| `SERVICENOW_USERNAME` | `admin` | ServiceNow API user |
| `SERVICENOW_PASSWORD` | `••••••••` | ServiceNow API password |
| `WEBEX_BOT_TOKEN` | `••••••••` | Bot's access token for Webex API |
| `WEBEX_BOT_EMAIL` | `Case_Summary_Bot@webex.bot` | Bot identity (to avoid infinite loops) |
| `CIRCUIT_CLIENT_ID` | `••••••••` | OAuth2 client ID from Cisco ID |
| `CIRCUIT_CLIENT_SECRET` | `••••••••` | OAuth2 client secret |
| `CIRCUIT_APP_KEY` | `egai-prd-cx-...` | EGAI portal application key |
| `CIRCUIT_MODEL` | `gpt-5-nano` | LLM model name |

---

## 🛡️ Safety & Guard Rails

The bot has **multiple layers of protection** to prevent infinite loops, spam, and errors:

| Guard | Location | What It Prevents |
|:------|:---------|:-----------------|
| `is_bot_message()` | `app.py` | Bot responding to its own messages (infinite loop) |
| `_is_noise()` | `app.py` | Bot reacting to echoed card fallback text |
| Thread reply skip | `webex_webhook()` | Ignoring replies in threads (only DMs) |
| Missing message ID | `webex_webhook()` | Graceful handling of malformed webhooks |
| Retry logic | `_request()` | 3 retries with backoff for Webex API calls |
| Error cards | `_summarize_and_flip()` | If pipeline fails, shows error card instead of silence |
| Timeout | Lambda config | 120s max prevents runaway executions |

---

## 📊 Performance

| Metric | Value |
|:-------|:------|
| **Webhook response time** | ~1–2 seconds (user sees working card) |
| **Total summary time** | ~5–8 seconds (end-to-end) |
| **Lambda cold start** | ~2–3 seconds (first invocation after idle) |
| **Lambda warm** | <500ms (subsequent invocations) |
| **Lambda memory** | 256 MB |
| **Lambda timeout** | 120 seconds |
| **Cost per invocation** | ~$0.0001 (pay-per-use) |

---

## 🎬 Demo Script (for Videocast)

### Pre-Demo Setup
1. ☑️ Wake up ServiceNow PDI at [developer.servicenow.com](https://developer.servicenow.com)
2. ☑️ Open Webex desktop app
3. ☑️ Have case number ready: `CS0001028`

### Live Demo Steps

| Step | What You Do | What the Audience Sees |
|:-----|:------------|:----------------------|
| 1 | Open Webex → DM **Case Summary Bot** | Webex chat window |
| 2 | Bot sends welcome card automatically | 👋 Welcome card with "Get Started" |
| 3 | Click **Get Started** | 🔍 Input card with text field |
| 4 | Type `CS0001028` → click **Summarize** | ⏳ Working card appears instantly |
| 5 | Wait ~5 seconds | 📋 Summary card replaces working card |
| 6 | Read through the structured summary | Problem → Root Cause → Actions → Status |
| 7 | Click **Summarize another case** | 🔍 Input card appears again |

### Talking Points During Demo
- _"Notice how the working card appeared instantly — that's the async pattern"_
- _"The summary is structured: Problem, Root Cause, What Was Done, Current Status"_
- _"No PII in the output — the prompt enforces this"_
- _"This took 6 seconds vs 15–30 minutes of manual reading"_

---

## 🔮 Future Enhancements

| Enhancement | Description |
|:------------|:------------|
| 🔄 Multi-case batch | Summarize multiple cases at once |
| 📊 Dashboard | Web dashboard showing summary history & analytics |
| 👥 Microsoft Teams | Extend to Teams in addition to Webex |
| 🚨 Auto-escalation | Trigger alerts when LLM detects critical patterns |
| 📈 Trend analysis | Identify recurring issues across cases |
| 💾 Caching | Cache recent summaries to reduce API calls |
| 🌐 Multi-language | Support summaries in different languages |

---

## 📝 API Endpoints

| Method | Path | Description |
|:-------|:-----|:------------|
| `GET` | `/` | Health check — `{"message": "Case Summary Bot is running ✅"}` |
| `GET` | `/debug-env` | Config diagnostics (token present? bot email? room count) |
| `POST` | `/webhook/webex` | Webex message webhook receiver |
| `POST` | `/webhook/webex/card-action` | Webex Adaptive Card action webhook receiver |

---

## 🧪 Testing & Troubleshooting

### Quick Health Check

```bash
# Check if Lambda is responding
curl https://fe4puvvg5j.execute-api.us-east-1.amazonaws.com/

# Check bot identity
curl -s -H "Authorization: Bearer $WEBEX_BOT_TOKEN" \
  https://webexapis.com/v1/people/me | python3 -m json.tool

# Check Lambda logs (last 5 min)
aws logs tail /aws/lambda/cPaas-sNow-summarisation-agent \
  --since 5m --format short --region us-east-1
```

### Common Issues

| Symptom | Cause | Fix |
|:--------|:------|:----|
| ServiceNow returns HTML | PDI is hibernating | Wake it at developer.servicenow.com |
| ServiceNow returns 401 | Wrong password | Re-check credentials in Lambda env vars |
| CIRCUIT returns 401 | Wrong model name | Use `gpt-5-nano`, check EGAI portal |
| Bot doesn't respond | Webhooks not registered | Re-register via Webex API |
| Bot loops infinitely | Guard check failing | Add text to `BOT_FALLBACK_PHRASES` in `app.py` |

---

## 📜 Summary

**Case Summary Bot** turns a 15–30 minute manual task into a **5–8 second** automated one:

```
Before:  Engineer → opens ServiceNow → reads 50+ entries → writes notes → 15-30 min
After:   Engineer → types "CS0001028" in Webex → gets AI summary → 5-8 seconds
```

**Built with:** Python 3.13 · AWS Lambda · FastAPI · Webex Adaptive Cards · ServiceNow CSM API · Cisco CIRCUIT LLM

**Total codebase:** ~1,400 lines across 6 files · Fully serverless · Zero servers to maintain

---

> _Built by Jansi Gorle · Technical Consulting Engineer · CX · April 2026_
