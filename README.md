# cPaas-sNow-summarisation-agent

AI-powered ServiceNow case summarization bot for Webex.

An engineer sends a case number (e.g. `CS0001028`) to the bot in Webex → the bot fetches the case from ServiceNow, builds a timeline from journal entries, calls Cisco's CIRCUIT LLM to generate a concise summary, and delivers it back as an Adaptive Card.

---

## Architecture

```
┌──────────────┐   webhook    ┌───────────────────┐   async invoke    ┌───────────────────┐
│  Webex Bot   │ ──────────►  │  API Gateway (HTTP)│ ───────────────►  │  AWS Lambda        │
│  (user DM)   │              │  /webhook/webex    │   (Event mode)    │  (summary pipeline)│
└──────────────┘              │  /webhook/card-act │                   └────────┬──────┬────┘
       ▲                      └───────────────────┘                            │      │
       │                                                                       │      │
       │  Adaptive Card                                           ┌────────────┘      │
       │  (summary result)                                        ▼                   ▼
       │                                               ┌──────────────┐   ┌───────────────┐
       └───────────────────────────────────────────────│  ServiceNow  │   │  CIRCUIT LLM  │
                                                       │  (CSM API)   │   │  (gpt-5-nano) │
                                                       └──────────────┘   └───────────────┘
```

### Request Flow

1. **User sends a case number** in Webex DM → Webex fires a webhook to API Gateway
2. **Lambda (HTTP handler)** receives the webhook, validates it, sends a "Generating…" working card, and **invokes itself asynchronously**
3. **Lambda (async handler)** runs the heavy pipeline:
   - Fetches case metadata from ServiceNow CSM API
   - Fetches journal entries (comments + work notes)
   - Builds a chronological timeline
   - Calls CIRCUIT LLM for summarization
   - Sends the summary Adaptive Card back to the Webex room

The async pattern ensures **instant webhook response** (~1-2s) while the summary pipeline runs independently with a full 120-second timeout.

---

## Project Structure

```
cPaas-sNow-summarisation-agent/
│
├── lambda_handler.py      # Lambda entrypoint — routes HTTP events (Mangum) vs async summary events
├── app.py                 # FastAPI app — webhook handlers, Adaptive Card templates, routing logic
├── config.py              # Environment variable loader (also bootstraps vendor/ path)
├── servicenow_client.py   # ServiceNow REST API client (CSM cases, journal entries, emails)
├── summarizer.py          # CIRCUIT LLM integration — token acquisition, prompt engineering, completion
├── formatter.py           # Timeline builder — merges journal + email entries chronologically
│
├── .env                   # Local environment variables (DO NOT COMMIT)
├── .env.example           # Template with placeholder values
├── .gitignore             # Git ignore rules
├── requirements.txt       # Python dependencies
├── deploy.sh              # One-command build & deploy script
├── README.md              # This file
│
└── vendor/                # Third-party packages (auto-installed, git-ignored)
    ├── fastapi/
    ├── mangum/
    ├── pydantic/
    ├── requests/
    └── ...
```

### Source Files

| File | Lines | Description |
|------|-------|-------------|
| `lambda_handler.py` | 43 | Lambda entrypoint. Delegates HTTP events to Mangum/FastAPI. Handles async self-invocations for the summary pipeline. |
| `app.py` | 939 | Core application. Webex webhook handlers, Adaptive Card templates (welcome, input, working, summary), message routing, async Lambda invocation. |
| `config.py` | 24 | Loads all configuration from environment variables with sensible defaults. |
| `servicenow_client.py` | 80 | ServiceNow REST client. Queries CSM case records, journal entries (comments/work_notes), and email history. |
| `summarizer.py` | 222 | CIRCUIT LLM integration. OAuth2 token acquisition from Cisco ID, prompt construction, chat completion, response parsing. |
| `formatter.py` | 79 | Timeline builder. Merges and sorts journal entries and emails into a chronological sequence for the LLM prompt. |

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SERVICENOW_INSTANCE` | ✅ | ServiceNow hostname (e.g. `dev380388.service-now.com`) |
| `SERVICENOW_USERNAME` | ✅ | ServiceNow API user |
| `SERVICENOW_PASSWORD` | ✅ | ServiceNow API password |
| `WEBEX_BOT_TOKEN` | ✅ | Webex Bot access token |
| `WEBEX_BOT_EMAIL` | ✅ | Webex Bot email (e.g. `mybot@webex.bot`) |
| `CIRCUIT_CLIENT_ID` | ✅ | CIRCUIT OAuth2 client ID (from Cisco ID / Okta) |
| `CIRCUIT_CLIENT_SECRET` | ✅ | CIRCUIT OAuth2 client secret |
| `CIRCUIT_APP_KEY` | ✅ | CIRCUIT application key (from EGAI portal) |
| `CIRCUIT_MODEL` | | LLM model name (default: `gpt-4o-mini`) |
| `CIRCUIT_TOKEN_URL` | | OAuth2 token endpoint (default: `https://id.cisco.com/oauth2/default/v1/token`) |
| `CIRCUIT_CHAT_BASE_URL` | | CIRCUIT chat completions base URL (default: `https://chat-ai.cisco.com/openai/deployments`) |

---

## Deployment

### Prerequisites

- AWS CLI configured with appropriate credentials
- Python 3.13+
- An existing Lambda function and API Gateway HTTP API

### Build & Deploy

```bash
# 1. Install dependencies for Lambda (Linux x86_64)
pip install \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --only-binary=:all: \
  --target /tmp/lambda_linux_build \
  -r requirements.txt

# 2. Copy source files into the build directory
cp lambda_handler.py app.py config.py servicenow_client.py \
   summarizer.py formatter.py /tmp/lambda_linux_build/

# 3. Create deployment package
cd /tmp/lambda_linux_build
zip -r /tmp/lambda_deploy.zip . -x '__pycache__/*' '*.pyc'

# 4. Deploy to Lambda
aws lambda update-function-code \
  --function-name cPaas-sNow-summarisation-agent \
  --zip-file fileb:///tmp/lambda_deploy.zip
```

### Lambda Configuration

| Setting | Value |
|---------|-------|
| Runtime | Python 3.13 |
| Handler | `lambda_handler.handler` |
| Timeout | 120 seconds |
| Memory | 256 MB |

### IAM Permissions

The Lambda execution role needs:
- `AWSLambdaBasicExecutionRole` (CloudWatch Logs)
- `lambda:InvokeFunction` on itself (for async self-invocation)

### Webex Webhooks

Two webhooks must point to the API Gateway URL:

| Name | Target URL | Resource | Event |
|------|-----------|----------|-------|
| Messages | `https://<api-id>.execute-api.<region>.amazonaws.com/webhook/webex` | `messages` | `created` |
| Card Actions | `https://<api-id>.execute-api.<region>.amazonaws.com/webhook/webex/card-action` | `attachmentActions` | `created` |

---

## Usage

1. Open a DM with the Webex bot
2. The bot sends a **welcome card** on first contact
3. Enter a case number (e.g. `CS0001026`) or click **Get Started**
4. The bot shows a **"Generating summary…"** card instantly
5. A few seconds later, the summary card appears with:
   - **Case metadata** (priority, state, last updated)
   - **Problem** — what's broken
   - **Root Cause** — if identified
   - **What Was Done** — actions taken by engineers
   - **Current Status** — where things stand
   - **Next Steps** — if any are mentioned

You can also type `summarize CS0001026` or just the case number directly.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/debug-env` | Config & state diagnostics |
| `POST` | `/webhook/webex` | Webex message webhook receiver |
| `POST` | `/webhook/webex/card-action` | Webex Adaptive Card action webhook receiver |

---

## Tech Stack

- **Runtime**: Python 3.13 on AWS Lambda
- **Web Framework**: FastAPI + Mangum (ASGI→Lambda adapter)
- **Chat Platform**: Webex (Adaptive Cards)
- **Ticketing**: ServiceNow CSM (Customer Service Management)
- **AI/LLM**: Cisco CIRCUIT (Azure OpenAI via Cisco's internal gateway)
- **API Gateway**: AWS HTTP API (v2)
