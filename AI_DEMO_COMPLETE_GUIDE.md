# 🤖 AI Case Summarization — Complete Demo Guide

> **"AI and More for Breakfast" Session — Live Demo by Jansi Gorle**  
> **Date:** 22 April 2026 | **Duration:** 5-7 minutes

---

## 📋 Table of Contents

1. [Problem We're Solving](#-problem-were-solving)
2. [Two Solutions Overview](#-two-solutions-overview)
3. [Solution 1: Webex Bot](#-solution-1-webex-bot-external-integration)
4. [Solution 2: Native ServiceNow Button](#-solution-2-native-servicenow-button)
5. [Architecture Diagrams](#-architecture-diagrams)
6. [Tech Stack](#-tech-stack)
7. [Key Code Walkthrough](#-key-code-walkthrough)
8. [Demo Flow Script](#-demo-flow-script-5-7-minutes)
9. [Talking Points](#-talking-points)
10. [Environment Setup](#-environment-setup-reference)

---

## 🎯 Problem We're Solving

### The Pain Point

Support engineers waste **10-15 minutes per case** reading through:
- 30+ journal entries (comments & work notes)
- Email threads
- Activity history
- Attachments

**Just to understand:** What's the issue? What was tried? What's the current status?

### The Impact

| Metric | Before AI | After AI |
|--------|-----------|----------|
| Time to understand a case | 10-15 minutes | **30 seconds** |
| Context switching | Open multiple tabs | **One click** |
| Knowledge transfer | Read everything | **Instant summary** |
| Engineer onboarding | Days to learn cases | **Immediate context** |

### Real Example

**Case CS0001027** has:
- 39 journal entries
- Multiple email threads
- 3-day timeline

❌ **Without AI:** Engineer reads all 39 entries (15 min)  
✅ **With AI:** Click button → 4-section summary (30 sec)

---

## 🔄 Two Solutions Overview

We built **TWO** approaches to solve this — giving flexibility based on user preference:

| Aspect | Solution 1: Webex Bot | Solution 2: ServiceNow Button |
|--------|----------------------|------------------------------|
| **Interface** | Webex chat | Native ServiceNow form |
| **Trigger** | Send message "CS0001027" | Click "AI Summary" button |
| **Best For** | Mobile, quick lookups | Working inside ServiceNow |
| **Infrastructure** | AWS Lambda (external) | ServiceNow Script Include (native) |
| **Response** | Adaptive Card in chat | Modal popup on form |

---

## 🤖 Solution 1: Webex Bot (External Integration)

### How It Works — User Experience

```
┌─────────────────────────────────────────────────────────────────┐
│  WEBEX TEAMS                                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  👤 User: CS0001027                                             │
│                                                                 │
│  🤖 Bot: [Adaptive Card]                                        │
│         ┌─────────────────────────────────────────┐             │
│         │ 📋 CS0001027 — Case Summary             │             │
│         │                                         │             │
│         │ Priority: High | State: Resolved        │             │
│         │ Group: CPaaS Support                    │             │
│         │                                         │             │
│         │ Problem:                                │             │
│         │ Webex Connect password reset links      │             │
│         │ expiring due to timezone mismatch...    │             │
│         │                                         │             │
│         │ What Was Done:                          │             │
│         │ • Identified root cause: 15-min TTL     │             │
│         │ • Implemented UTC fix                   │             │
│         │ • Deployed to production                │             │
│         │                                         │             │
│         │ [🔄 Refresh] [📎 View in ServiceNow]    │             │
│         └─────────────────────────────────────────┘             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Request Flow — Step by Step

```
┌──────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐    ┌────────────┐
│  User    │    │    Webex     │    │ AWS Lambda  │    │  ServiceNow  │    │  CIRCUIT   │
│ (Webex)  │    │   Platform   │    │  (FastAPI)  │    │     API      │    │    LLM     │
└────┬─────┘    └──────┬───────┘    └──────┬──────┘    └──────┬───────┘    └─────┬──────┘
     │                 │                   │                  │                  │
     │ 1. "CS0001027"  │                   │                  │                  │
     │────────────────>│                   │                  │                  │
     │                 │                   │                  │                  │
     │                 │ 2. Webhook POST   │                  │                  │
     │                 │──────────────────>│                  │                  │
     │                 │                   │                  │                  │
     │                 │                   │ 3. GET /case     │                  │
     │                 │                   │─────────────────>│                  │
     │                 │                   │                  │                  │
     │                 │                   │ 4. Case data +   │                  │
     │                 │                   │<─────────────────│                  │
     │                 │                   │    journals      │                  │
     │                 │                   │                  │                  │
     │                 │                   │ 5. Build prompt + call LLM         │
     │                 │                   │─────────────────────────────────────>
     │                 │                   │                  │                  │
     │                 │                   │ 6. AI Summary    │                  │
     │                 │                   │<─────────────────────────────────────
     │                 │                   │                  │                  │
     │                 │ 7. Adaptive Card  │                  │                  │
     │                 │<──────────────────│                  │                  │
     │                 │                   │                  │                  │
     │ 8. Display      │                   │                  │                  │
     │<────────────────│                   │                  │                  │
     │                 │                   │                  │                  │
```

### Project Structure

```
cPaas-sNow-summarisation-agent-final/
├── app.py                 # Main FastAPI app + Webex webhook handlers
├── config.py              # Environment variables & configuration
├── servicenow_client.py   # ServiceNow API calls (cases, journals, emails)
├── formatter.py           # Timeline builder (sorts/formats journal entries)
├── summarizer.py          # CIRCUIT LLM integration + prompt engineering
├── lambda_handler.py      # AWS Lambda entry point (Mangum adapter)
├── requirements.txt       # Python dependencies
├── deploy.sh              # AWS deployment script
└── .env                   # Credentials (not in git)
```

### Key Files Explained

#### `config.py` — Configuration Hub
```python
# ServiceNow credentials
SERVICENOW_INSTANCE = os.getenv("SERVICENOW_INSTANCE")  # dev380388.service-now.com
SERVICENOW_USERNAME = os.getenv("SERVICENOW_USERNAME")  # admin
SERVICENOW_PASSWORD = os.getenv("SERVICENOW_PASSWORD")  # ****

# Webex Bot
WEBEX_BOT_TOKEN = os.getenv("WEBEX_BOT_TOKEN")
WEBEX_BOT_EMAIL = os.getenv("WEBEX_BOT_EMAIL")

# Cisco CIRCUIT LLM
CIRCUIT_CLIENT_ID     = os.getenv("CIRCUIT_CLIENT_ID")
CIRCUIT_CLIENT_SECRET = os.getenv("CIRCUIT_CLIENT_SECRET")
CIRCUIT_APP_KEY       = os.getenv("CIRCUIT_APP_KEY")
CIRCUIT_MODEL         = os.getenv("CIRCUIT_MODEL", "gpt-5-nano")
CIRCUIT_TOKEN_URL     = "https://id.cisco.com/oauth2/default/v1/token"
CIRCUIT_CHAT_BASE_URL = "https://chat-ai.cisco.com/openai/deployments"
```

#### `servicenow_client.py` — Data Fetching
```python
def get_case_by_number(case_number: str):
    """Fetch case record from ServiceNow CSM."""
    url = f"https://{SERVICENOW_INSTANCE}/api/now/table/sn_customerservice_case"
    params = {
        "sysparm_query": f"number={case_number}",
        "sysparm_fields": "sys_id,number,short_description,description,state,priority...",
        "sysparm_display_value": "all"
    }
    response = requests.get(url, auth=(USERNAME, PASSWORD), params=params)
    return response.json()["result"][0]

def get_case_journal_entries(sys_id: str):
    """Fetch comments and work notes from sys_journal_field."""
    url = f"https://{SERVICENOW_INSTANCE}/api/now/table/sys_journal_field"
    params = {
        "sysparm_query": f"element_id={sys_id}^elementINcomments,work_notes^ORDERBYsys_created_on"
    }
    return requests.get(url, auth=AUTH, params=params).json()["result"]

def get_case_emails(sys_id: str):
    """Fetch emails linked to the case."""
    # Similar pattern for sys_email table
```

#### `formatter.py` — Timeline Builder
```python
def build_timeline(journal_entries, email_entries):
    """Merge and sort all case activity chronologically."""
    timeline = []
    
    # Process journal entries (comments, work notes)
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
            "text": clean_text(email["body_text"])
        })
    
    # Sort chronologically
    timeline.sort(key=lambda x: x["timestamp"])
    return timeline
```

#### `summarizer.py` — LLM Integration (Most Important!)
```python
def build_prompt(case_data, timeline):
    """Craft the prompt for CIRCUIT LLM."""
    
    # Format timeline as numbered list
    timeline_text = "\n".join([
        f"{i}. [{item['timestamp']}] {item['speaker']}: {item['text']}"
        for i, item in enumerate(timeline, 1)
    ])
    
    return f"""Summarize this ServiceNow case for an engineer picking up the ticket.
They need to understand the situation in 30 seconds without reading the full timeline.

RULES:
1. Use ONLY facts from the data below. Never invent or assume.
2. Deduplicate: if the same thing is said multiple times, mention it once.
3. No email addresses, no personal names, no PII.
4. Keep each bullet to one short sentence.
5. If something is not stated, omit it entirely.

Case: {case_data['number']} | Title: {case_data['short_description']}
State: {case_data['state']} | Priority: {case_data['priority']}
Description: {case_data['description']}

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

def call_circuit_llm(prompt):
    """Call Cisco CIRCUIT LLM API."""
    
    # Step 1: Get OAuth2 access token
    token_response = requests.post(
        CIRCUIT_TOKEN_URL,
        headers={"Authorization": f"Basic {base64_encode(CLIENT_ID:CLIENT_SECRET)}"},
        data={"grant_type": "client_credentials"}
    )
    access_token = token_response.json()["access_token"]
    
    # Step 2: Call chat completions
    url = f"{CIRCUIT_CHAT_BASE_URL}/{CIRCUIT_MODEL}/chat/completions"
    response = requests.post(url, 
        headers={"api-key": access_token},
        json={
            "messages": [
                {"role": "system", "content": "You produce concise, factual ticket summaries..."},
                {"role": "user", "content": prompt}
            ],
            "user": json.dumps({"appkey": CIRCUIT_APP_KEY}),
            "temperature": 0.05,
            "max_tokens": 500
        }
    )
    return response.json()["choices"][0]["message"]["content"]
```

#### `app.py` — Webex Webhook Handler
```python
@app.post("/webhook/webex")
async def webex_webhook(request: Request):
    """Handle incoming Webex messages."""
    data = await request.json()
    room_id = data["data"]["roomId"]
    message_id = data["data"]["id"]
    
    # Fetch the actual message text
    message = get_webex_message(message_id)
    text = message["text"].strip()
    
    # Check if it's a case number (CS0001234 or INC0001234)
    case_match = re.search(r'(CS|INC)\d{7}', text, re.IGNORECASE)
    
    if case_match:
        case_number = case_match.group(0).upper()
        
        # Fetch case data
        case_data = get_case_by_number(case_number)
        journals = get_case_journal_entries(case_data["sys_id"])
        emails = get_case_emails(case_data["sys_id"])
        
        # Build timeline and summarize
        timeline = build_timeline(journals, emails)
        summary = summarize_case_with_llm(case_data, timeline)
        
        # Send adaptive card response
        send_adaptive_card(room_id, case_number, summary)
    
    return {"status": "ok"}
```

---

## 🖥️ Solution 2: Native ServiceNow Button

### How It Works — User Experience

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ServiceNow — Case CS0001027                                         [× Close] │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  [Discuss] [Follow] [Close Case] [Update] [✨ AI Summary] [Accept] [Delete]     │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                         │   │
│  │  ✨ AI Summary — CS0001027                                    [×]       │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │   │
│  │  │ ✨ Powered by CIRCUIT LLM              39 entries analyzed      │   │   │
│  │  └─────────────────────────────────────────────────────────────────┘   │   │
│  │                                                                         │   │
│  │  Issue:                                                                 │   │
│  │  Webex Connect password reset links expire with a Page Expired          │   │
│  │  error due to token expiry from a timezone mismatch in validation       │   │
│  │  plus a 15-minute TTL, persisting for this customer.                    │   │
│  │                                                                         │   │
│  │  Action Taken:                                                          │   │
│  │  • Reproduced the issue in a test environment and identified the        │   │
│  │    root cause: 15-minute TTL and email delays combined with a           │   │
│  │    timezone bug introduced in patch v3.8.2.                             │   │
│  │  • Implemented a fix to use UTC for token generation and validation     │   │
│  │    and increased TTL to 60 minutes; deployed to production.             │   │
│  │  • Performed a manual password reset for the affected user.             │   │
│  │  • Verified end-to-end reset flow after the fix.                        │   │
│  │  • Notified the user of the fix and status.                             │   │
│  │                                                                         │   │
│  │  Resolution:                                                            │   │
│  │  Root cause fixed; token validation now uses UTC with a 60-minute       │   │
│  │  TTL, fix deployed to production, and the reset flow is working.        │   │
│  │                                                                         │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  Number: CS0001027                Channel: Web                                  │
│  State: Resolved                  Priority: High                                │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Request Flow — Step by Step

```
┌──────────────┐    ┌─────────────────┐    ┌────────────────┐    ┌────────────┐
│   Browser    │    │  UI Action      │    │ Script Include │    │  CIRCUIT   │
│  (User)      │    │  (Client JS)    │    │ (Server JS)    │    │    LLM     │
└──────┬───────┘    └────────┬────────┘    └───────┬────────┘    └─────┬──────┘
       │                     │                     │                   │
       │ 1. Click            │                     │                   │
       │ "AI Summary"        │                     │                   │
       │────────────────────>│                     │                   │
       │                     │                     │                   │
       │ 2. Show loading     │                     │                   │
       │<────────────────────│                     │                   │
       │    popup            │                     │                   │
       │                     │                     │                   │
       │                     │ 3. GlideAjax call   │                   │
       │                     │ getSummary(sys_id)  │                   │
       │                     │────────────────────>│                   │
       │                     │                     │                   │
       │                     │                     │ 4. GlideRecord    │
       │                     │                     │ fetch case +      │
       │                     │                     │ journals + emails │
       │                     │                     │                   │
       │                     │                     │ 5. Build prompt   │
       │                     │                     │────────────────────>
       │                     │                     │                   │
       │                     │                     │ 6. AI response    │
       │                     │                     │<───────────────────
       │                     │                     │                   │
       │                     │ 7. JSON result      │                   │
       │                     │<────────────────────│                   │
       │                     │                     │                   │
       │ 8. Display styled   │                     │                   │
       │<────────────────────│                     │                   │
       │    modal popup      │                     │                   │
       │                     │                     │                   │
```

### ServiceNow Components

```
ServiceNow PDI (dev380388.service-now.com)
│
├── System Properties (6 properties)
│   ├── x_case_summary.circuit_client_id
│   ├── x_case_summary.circuit_client_secret
│   ├── x_case_summary.circuit_app_key
│   ├── x_case_summary.circuit_model         → gpt-5-nano
│   ├── x_case_summary.circuit_token_url     → https://id.cisco.com/oauth2/default/v1/token
│   └── x_case_summary.circuit_chat_base_url → https://chat-ai.cisco.com/openai/deployments
│
├── Script Include: CaseSummaryAI
│   ├── Client callable: ✅
│   ├── Methods:
│   │   ├── getSummary(sys_id, table)      → Called via GlideAjax
│   │   ├── _getCaseData(sys_id)           → GlideRecord query
│   │   ├── _getJournalEntries(sys_id)     → Comments + work notes
│   │   ├── _getEmails(sys_id)             → sys_email records
│   │   ├── _buildTimeline()               → Merge & sort chronologically
│   │   ├── _buildPrompt()                 → Craft LLM prompt
│   │   ├── _callCircuitLLM()              → RESTMessageV2 to CIRCUIT
│   │   ├── _getAccessToken()              → OAuth2 client credentials
│   │   └── _parseSections()               → Parse Issue/Action/Resolution
│   └── Lines: ~430
│
└── UI Action: AI Summary
    ├── Table: sn_customerservice_case
    ├── Client: ✅
    ├── Form button: ✅
    ├── Onclick: generateAISummary()
    ├── Functions:
    │   ├── generateAISummary()            → Main entry point
    │   ├── _showAISummaryPanel()          → Styled modal (like AI Assist)
    │   └── _showErrorDialog()             → Error handling
    └── Lines: ~236
```

### Key Code — Script Include (Server-Side)

#### `CaseSummaryAI.js` — Core Pipeline
```javascript
var CaseSummaryAI = Class.create();
CaseSummaryAI.prototype = Object.extendsObject(AbstractAjaxProcessor, {

    // Called from UI Action via GlideAjax
    getSummary: function() {
        var sysId = this.getParameter('sysparm_sys_id');
        var table = this.getParameter('sysparm_table') || 'sn_customerservice_case';
        
        try {
            var result = this._runPipeline(sysId, table);
            return JSON.stringify(result);
        } catch (e) {
            return JSON.stringify({ success: false, error: e.message });
        }
    },

    _runPipeline: function(sysId, table) {
        // 1. Fetch case data
        var caseData = this._getCaseData(sysId, table);
        
        // 2. Fetch journal entries (comments + work notes)
        var journalEntries = this._getJournalEntries(sysId);
        
        // 3. Fetch emails
        var emailEntries = this._getEmails(sysId, table);
        
        // 4. Build unified timeline
        var timeline = this._buildTimeline(journalEntries, emailEntries);
        
        // 5. Build prompt
        var prompt = this._buildPrompt(caseData, timeline);
        
        // 6. Call CIRCUIT LLM
        var rawSummary = this._callCircuitLLM(prompt);
        
        // 7. Parse sections
        var sections = this._parseSections(rawSummary);
        
        return {
            success: true,
            summary: rawSummary,
            sections: sections,
            case_number: caseData.number,
            timeline_count: timeline.length
        };
    },

    _callCircuitLLM: function(prompt) {
        // Get credentials from System Properties
        var clientId     = gs.getProperty('x_case_summary.circuit_client_id');
        var clientSecret = gs.getProperty('x_case_summary.circuit_client_secret');
        var appKey       = gs.getProperty('x_case_summary.circuit_app_key');
        var model        = gs.getProperty('x_case_summary.circuit_model');
        
        // Get OAuth2 token
        var accessToken = this._getAccessToken(clientId, clientSecret);
        
        // Call CIRCUIT LLM
        var chatUrl = 'https://chat-ai.cisco.com/openai/deployments/' + model + '/chat/completions';
        
        var sm = new sn_ws.RESTMessageV2();
        sm.setEndpoint(chatUrl);
        sm.setHttpMethod('POST');
        sm.setRequestHeader('Content-Type', 'application/json');
        sm.setRequestHeader('api-key', accessToken);
        sm.setRequestBody(JSON.stringify({
            messages: [
                { role: 'system', content: 'You produce concise, factual ticket summaries...' },
                { role: 'user', content: prompt }
            ],
            user: JSON.stringify({ appkey: appKey }),
            temperature: 0.05,
            max_tokens: 600
        }));
        
        var response = sm.execute();
        var payload = JSON.parse(response.getBody());
        return payload.choices[0].message.content;
    },

    _getAccessToken: function(clientId, clientSecret) {
        var encoded = GlideStringUtil.base64Encode(clientId + ':' + clientSecret);
        
        var sm = new sn_ws.RESTMessageV2();
        sm.setEndpoint('https://id.cisco.com/oauth2/default/v1/token');
        sm.setHttpMethod('POST');
        sm.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
        sm.setRequestHeader('Authorization', 'Basic ' + encoded);
        sm.setRequestBody('grant_type=client_credentials');
        
        var response = sm.execute();
        var payload = JSON.parse(response.getBody());
        return payload.access_token;
    },

    type: 'CaseSummaryAI'
});
```

### Key Code — UI Action (Client-Side)

#### `ai_summary_button.js` — Button Handler
```javascript
function generateAISummary() {
    var sysId = g_form.getUniqueValue();
    var table = g_form.getTableName();
    var recordNum = g_form.getValue('number');
    
    // Show loading dialog
    var loadingDialog = new GlideModal('glide_modal_confirm', false, 500);
    loadingDialog.setTitle('🤖 AI Summary — ' + recordNum);
    loadingDialog.renderWithContent(
        '<div style="text-align:center; padding:50px;">' +
            '<div class="spinner"></div>' +
            '<p>Generating AI Summary...</p>' +
            '<p style="color:#888;">Fetching journals, building timeline, calling CIRCUIT LLM</p>' +
        '</div>'
    );
    
    // Call Script Include via GlideAjax
    var ga = new GlideAjax('CaseSummaryAI');
    ga.addParam('sysparm_name', 'getSummary');
    ga.addParam('sysparm_sys_id', sysId);
    ga.addParam('sysparm_table', table);
    ga.getXMLAnswer(function(response) {
        loadingDialog.destroy();
        
        var result = JSON.parse(response);
        if (result.success) {
            _showAISummaryPanel(recordNum, result);
        } else {
            _showErrorDialog(recordNum, result.error);
        }
    });
    
    return false;
}

function _showAISummaryPanel(recordNum, result) {
    var sections = result.sections;
    
    var html = '<div style="font-family:SourceSansPro,Arial,sans-serif;">' +
        // Header (purple gradient like AI Assist)
        '<div style="background:linear-gradient(135deg, #6366f1, #0078d7); color:white; padding:14px 20px;">' +
            '<span>✨</span> <strong>Powered by CIRCUIT LLM</strong>' +
            '<span style="float:right;">' + result.timeline_count + ' entries analyzed</span>' +
        '</div>' +
        
        // Issue section
        '<div style="padding:20px;">' +
            '<h4>Issue:</h4>' +
            '<p>' + sections['Issue'] + '</p>' +
            
            '<h4>Action Taken:</h4>' +
            '<ul>' + formatBullets(sections['Action Taken']) + '</ul>' +
            
            '<h4>Resolution:</h4>' +
            '<p>' + sections['Resolution'] + '</p>' +
        '</div>' +
    '</div>';
    
    var dialog = new GlideModal('glide_modal_confirm', false, 600);
    dialog.setTitle('✨ AI Summary — ' + recordNum);
    dialog.renderWithContent(html);
}
```

---

## 🏗️ Architecture Diagrams

### Solution 1: Webex Bot Architecture

```
                                    ┌─────────────────────────────────────────────┐
                                    │              AWS Cloud                       │
                                    │  ┌───────────────────────────────────────┐  │
                                    │  │         AWS Lambda Function           │  │
┌──────────────┐                    │  │  ┌─────────────────────────────────┐  │  │
│              │                    │  │  │         FastAPI App             │  │  │
│    Webex     │   Webhook POST     │  │  │                                 │  │  │
│   Platform   │───────────────────────│  │  app.py ──> servicenow_client   │  │  │
│              │                    │  │  │     │                           │  │  │
│  ┌────────┐  │                    │  │  │     ├──> formatter.py           │  │  │
│  │  User  │  │                    │  │  │     │                           │  │  │
│  │ Webex  │  │  Adaptive Card     │  │  │     └──> summarizer.py ─────────│──│──│───┐
│  │  App   │  │<──────────────────────│  │                                 │  │  │   │
│  └────────┘  │                    │  │  └─────────────────────────────────┘  │  │   │
│              │                    │  └───────────────────────────────────────┘  │   │
└──────────────┘                    └─────────────────────────────────────────────┘   │
                                                        │                             │
                                                        │ REST API                    │ OAuth2 + REST
                                                        ▼                             ▼
                                    ┌─────────────────────────┐      ┌─────────────────────────┐
                                    │      ServiceNow         │      │     Cisco CIRCUIT       │
                                    │   dev380388.service-    │      │         LLM             │
                                    │       now.com           │      │                         │
                                    │                         │      │  id.cisco.com (OAuth2)  │
                                    │  • sn_customerservice_  │      │  chat-ai.cisco.com      │
                                    │    case                 │      │  (gpt-5-nano)           │
                                    │  • sys_journal_field    │      │                         │
                                    │  • sys_email            │      └─────────────────────────┘
                                    └─────────────────────────┘
```

### Solution 2: Native ServiceNow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            ServiceNow Platform                                       │
│                         dev380388.service-now.com                                    │
│                                                                                      │
│  ┌─────────────────────┐     ┌─────────────────────────────────────────────────┐   │
│  │    Browser (User)    │     │              Server-Side                        │   │
│  │                      │     │                                                 │   │
│  │  ┌────────────────┐  │     │  ┌─────────────────────────────────────────┐   │   │
│  │  │   Case Form    │  │     │  │        Script Include                   │   │   │
│  │  │                │  │     │  │        CaseSummaryAI                    │   │   │
│  │  │ [AI Summary]───│──│─────│──│──>  getSummary()                        │   │   │
│  │  │    Button      │  │     │  │         │                               │   │   │
│  │  └────────────────┘  │     │  │         ├── GlideRecord (case data)     │   │   │
│  │         │            │     │  │         ├── GlideRecord (journals)      │   │   │
│  │         │            │     │  │         ├── GlideRecord (emails)        │   │   │
│  │         ▼            │     │  │         ├── _buildTimeline()            │   │   │
│  │  ┌────────────────┐  │     │  │         ├── _buildPrompt()              │   │   │
│  │  │  UI Action JS  │  │     │  │         └── RESTMessageV2 ──────────────│───│───│──┐
│  │  │                │  │     │  │                                         │   │   │  │
│  │  │ GlideAjax ─────│──│─────│──│───>                                     │   │   │  │
│  │  │                │  │     │  └─────────────────────────────────────────┘   │   │  │
│  │  │ GlideModal <───│──│─────│─── JSON response                               │   │  │
│  │  │ (popup)        │  │     │                                                 │   │  │
│  │  └────────────────┘  │     │  ┌─────────────────────────────────────────┐   │   │  │
│  │                      │     │  │        System Properties                │   │   │  │
│  └─────────────────────┘     │  │  x_case_summary.circuit_client_id       │   │   │  │
│                               │  │  x_case_summary.circuit_client_secret   │   │   │  │
│                               │  │  x_case_summary.circuit_app_key         │   │   │  │
│                               │  │  x_case_summary.circuit_model           │   │   │  │
│                               │  └─────────────────────────────────────────┘   │   │  │
└───────────────────────────────────────────────────────────────────────────────────┘  │
                                                                                        │
                                                                                        │
                                         ┌──────────────────────────────────────────────┘
                                         │
                                         ▼
                              ┌─────────────────────────┐
                              │     Cisco CIRCUIT       │
                              │         LLM             │
                              │                         │
                              │  id.cisco.com (OAuth2)  │
                              │  chat-ai.cisco.com      │
                              │  (gpt-5-nano)           │
                              └─────────────────────────┘
```

---

## 🛠️ Tech Stack

### Solution 1: Webex Bot

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Runtime** | AWS Lambda | Serverless execution |
| **Framework** | FastAPI + Mangum | HTTP handling + Lambda adapter |
| **Language** | Python 3.11 | Backend logic |
| **Messaging** | Webex Teams API | Bot messages + Adaptive Cards |
| **Data** | ServiceNow REST API | Case/journal/email data |
| **AI** | Cisco CIRCUIT LLM | gpt-5-nano model |
| **Auth** | OAuth2 Client Credentials | CIRCUIT API access |
| **Deployment** | AWS API Gateway | Webhook endpoint |

### Solution 2: Native ServiceNow

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Platform** | ServiceNow PDI | Hosting + execution |
| **Server Logic** | Script Include (JS) | CaseSummaryAI class |
| **Client Logic** | UI Action (JS) | Button + modal popup |
| **Data** | GlideRecord | Query case/journal/email tables |
| **HTTP** | RESTMessageV2 | Outbound calls to CIRCUIT |
| **Config** | System Properties | Store credentials |
| **AI** | Cisco CIRCUIT LLM | gpt-5-nano model |
| **Auth** | OAuth2 + Basic Auth | CIRCUIT API access |

### Cisco CIRCUIT LLM Details

| Property | Value |
|----------|-------|
| **Token Endpoint** | `https://id.cisco.com/oauth2/default/v1/token` |
| **Chat Endpoint** | `https://chat-ai.cisco.com/openai/deployments/{model}/chat/completions` |
| **Model** | `gpt-5-nano` |
| **Auth Method** | OAuth2 Client Credentials → Bearer token in `api-key` header |
| **App Key** | Passed in request body as `user: {appkey: "..."}` |

---

## 🎬 Demo Flow Script (5-7 minutes)

### Opening (30 seconds)

> "Hi everyone! I'm Jansi from the CX team. Today I'll show you how we're using AI to solve a real problem that every support engineer faces — understanding case context quickly."

### Part 1: The Problem (1 minute)

1. **Open ServiceNow** → Navigate to Cases
2. **Open CS0001027** → Show the case form
3. **Scroll through Activity** → Point out 39 journal entries

> "This case has 39 journal entries spanning 3 days. If you're picking up this case, you'd need to read through all of this to understand: What's the issue? What was tried? What's the status? That takes 10-15 minutes."

### Part 2: Solution Demo (3-4 minutes)

#### Demo the ServiceNow Button (Primary Demo)

1. **Point to the "AI Summary" button** in the form header
2. **Click it** → Show loading popup

> "Watch this. One click..."

3. **Show the result popup** with Issue/Action Taken/Resolution

> "In 30 seconds, CIRCUIT LLM analyzed all 39 entries and gave us a structured summary:
> - **Issue**: Password reset links expiring due to timezone mismatch
> - **Action Taken**: 5 bullet points of what the team did
> - **Resolution**: Root cause fixed, deployed to production
>
> The engineer now has full context without reading anything."

4. **Highlight the header**: "Powered by CIRCUIT LLM — 39 entries analyzed"

#### Quick Architecture Explanation (1 minute)

> "How does this work?"

Draw or show the diagram:

```
Button Click → Script Include (server-side JavaScript)
    ↓
Fetches: Case data + Comments + Work notes + Emails
    ↓
Builds chronological timeline
    ↓
Crafts prompt with rules (no PII, deduplicate, etc.)
    ↓
Calls Cisco CIRCUIT LLM (gpt-5-nano)
    ↓
Parses response into sections
    ↓
Displays in styled popup
```

> "Everything runs inside ServiceNow — no external servers needed. Credentials are stored securely in System Properties."

### Part 3: Value Proposition (30 seconds)

| Metric | Before | After |
|--------|--------|-------|
| Time to understand | 10-15 min | 30 sec |
| Manual reading | Required | Not needed |
| Context switching | Multiple tabs | One click |

> "This is a 95% reduction in time to understand a case. Multiply that by hundreds of cases per day across the team."

### Closing (30 seconds)

> "We built two versions:
> 1. **Webex Bot** — for quick lookups from mobile or chat
> 2. **ServiceNow Button** — for when you're already working in ServiceNow
>
> Both use Cisco CIRCUIT LLM, which is approved for internal use. Questions?"

---

## 💬 Talking Points

### If Asked: "How accurate is the AI?"

> "We use a very low temperature (0.05) so it's deterministic. The prompt has strict rules:
> - Only use facts from the data
> - Never invent or assume
> - Deduplicate repeated information
> - No PII (names, emails)
>
> It's been tested on 20+ cases with good results. But it's a summary tool, not a replacement for reading when needed."

### If Asked: "What about security/PII?"

> "CIRCUIT LLM is Cisco's internal AI platform — data doesn't leave Cisco. The prompt explicitly tells the model to exclude personal names and email addresses. Credentials are stored in ServiceNow System Properties, not in code."

### If Asked: "Can this work for Incidents too?"

> "Yes! The Script Include already supports any table. Just change the UI Action to target the `incident` table and it works the same way. The journal entries structure is identical."

### If Asked: "How long did this take to build?"

> "The Webex Bot: ~2 days (Python, Lambda, webhooks)
> The ServiceNow Button: ~1 day (Script Include, UI Action)
> Most time was spent on prompt engineering to get good summaries."

### If Asked: "What's CIRCUIT?"

> "CIRCUIT is Cisco's internal AI platform — it's like OpenAI's API but hosted by Cisco. We authenticate with OAuth2 and call the chat completions endpoint. The model we use is gpt-5-nano, which is fast and cheap."

---

## ⚙️ Environment Setup Reference

### Solution 1: Webex Bot Environment Variables

```bash
# .env file
SERVICENOW_INSTANCE=dev380388.service-now.com
SERVICENOW_USERNAME=admin
SERVICENOW_PASSWORD=********

WEBEX_BOT_TOKEN=NzQ2YzM5ZD...
WEBEX_BOT_EMAIL=case-summary-bot@webex.bot

CIRCUIT_CLIENT_ID=0oatuvf1hxeWbWSbT5d7
CIRCUIT_CLIENT_SECRET=Dni7MPubYXGn...
CIRCUIT_APP_KEY=egai-prd-cx-123212180-summarize-1774871716656
CIRCUIT_MODEL=gpt-5-nano
```

### Solution 2: ServiceNow System Properties

Navigate to: `sys_properties.list`

| Name | Value |
|------|-------|
| `x_case_summary.circuit_client_id` | `0oatuvf1hxeWbWSbT5d7` |
| `x_case_summary.circuit_client_secret` | `Dni7MPubYXGn...` |
| `x_case_summary.circuit_app_key` | `egai-prd-cx-123212180-summarize-...` |
| `x_case_summary.circuit_model` | `gpt-5-nano` |
| `x_case_summary.circuit_token_url` | `https://id.cisco.com/oauth2/default/v1/token` |
| `x_case_summary.circuit_chat_base_url` | `https://chat-ai.cisco.com/openai/deployments` |

### ServiceNow Setup Checklist

- [ ] Create 6 System Properties
- [ ] Create Script Include: `CaseSummaryAI` (Client callable: ✅)
- [ ] Create UI Action: `AI Summary` (Table: `sn_customerservice_case`, Client: ✅, Form button: ✅)
- [ ] Test on case CS0001027 or CS0001028

---

## 📊 Summary

| Aspect | Solution 1: Webex Bot | Solution 2: ServiceNow Button |
|--------|----------------------|------------------------------|
| **Best For** | Mobile, quick lookups | In-platform workflow |
| **Infrastructure** | AWS Lambda (external) | ServiceNow (native) |
| **LOC** | ~1200 (Python) | ~670 (JavaScript) |
| **Latency** | ~5-8 seconds | ~3-5 seconds |
| **Maintenance** | AWS + Webex webhooks | ServiceNow only |

---

**Created by:** Jansi Gorle  
**Team:** CX (Customer Experience)  
**Date:** April 2026  
**GitHub:** [GorleJansi/Case-Summary-Bot](https://github.com/GorleJansi/Case-Summary-Bot)
