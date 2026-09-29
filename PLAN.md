# 📋 Day 13 Monitoring & LLMOps — Comprehensive Plan

**Date:** 2026-09-29  
**Student Email:** legiabao9873@gmail.com  
**MSSV:** 02887  
**Repository:** K4-L3-DAY13-LeGiaBao-02887-Monitoring-LLMOps  
**Lab Duration:** 240 minutes (14:00–18:00)

---

## 🎯 Lab Goal

Transform a black-box AI API into an observable system that can answer three critical questions:
1. **What's wrong with the system?** (Metrics)
2. **Which request was affected?** (Logs with Correlation ID)
3. **Which step caused the problem?** (Traces with Span tree)

**Key Investigation Flow:** Metrics → Logs → Traces → Root Cause

---

## 📊 Checkpoint Roadmap

| Checkpoint | Time | Focus | Success Criteria |
|---|---|---|---|
| **CP0** | 14:00–14:30 | Setup & baseline | `/health` ok, logs created, tests pass |
| **CP1** | 14:30–15:20 | Logging & PII | `validate_logs.py` ≥ 80/100 |
| **CP2** | 15:20–16:40 | Traces, prompts & dashboard | 10+ traces, 6/6 dashboard panels |
| **CP3** | 16:40–17:30 | Challenge investigation | Root cause from metric + log + trace |
| **CP4** | 17:30–18:00 | Report & evidence | Full report submitted with all evidence |

---

## ✅ CP0: Setup & Baseline (0–30 minutes)

### What needs to be done

1. **Environment Setup**
   - [ ] Activate Python virtual environment
   - [ ] Install dependencies from `requirements.txt`
   - [ ] Copy `.env.example` to `.env` (don't commit `.env`)

2. **Langfuse Cloud Project**
   - [ ] Go to https://cloud.langfuse.com
   - [ ] Create personal project named `day13-k4-l3a-02887`
   - [ ] Extract API keys from **Project Settings → API Keys**
   - [ ] **DO NOT** share keys; never screenshot the secret key page
   - [ ] Fill `.env` with your own keys:
     ```dotenv
     LANGFUSE_PUBLIC_KEY=pk-lf-...
     LANGFUSE_SECRET_KEY=sk-lf-...
     LANGFUSE_BASE_URL=https://cloud.langfuse.com
     LANGFUSE_PROMPT_NAME=day13-chat
     LANGFUSE_PROMPT_LABEL=production
     ```

3. **Run Baseline Tests**
   - [ ] Terminal 1: `uvicorn app.main:app --reload --env-file .env`
   - [ ] Terminal 2: Run baseline validators:
     ```bash
     python scripts/load_test.py
     python scripts/validate_logs.py
     python scripts/validate_dashboard.py
     python -m pytest -q
     ```

4. **Verify & Document**
   - [ ] `/health` endpoint returns `{"ok": true}`
   - [ ] `data/logs.jsonl` is created (check file exists)
   - [ ] Traces appear in your personal Langfuse project
   - [ ] **Save baseline results** to `submission/REPORT.md` Section 3
     - Note the score for `validate_logs.py` and `validate_dashboard.py`
     - This is normal baseline — many validators will fail until CP1/CP2 work is done

### Success Check
```bash
✓ API running at http://localhost:8000
✓ GET http://localhost:8000/health returns {"ok": true}
✓ data/logs.jsonl file exists with entries
✓ Traces visible in Langfuse dashboard (your project)
✓ pytest passes without errors
```

---

## ✅ CP1: Logging & PII (30–80 minutes)

### What needs to be done

#### 1. **Correlation ID Management** (`app/middleware.py`)

The middleware should:
1. **Clear old context** at the start of each request (avoid leakage)
2. **Extract or generate** correlation ID:
   - Check for `x-request-id` header from client
   - If missing, generate: `req-` + 8 random hex chars (e.g., `req-a1b2c3d4`)
3. **Bind to context** so all log statements in that request share it
4. **Return in response** headers so client can track the request

```python
# app/middleware.py TODO items:
- clear_contextvars()  # Avoid leakage between requests
- Extract x-request-id or generate req-<8-hex>
- bind_contextvars(correlation_id=correlation_id)
- response.headers["x-request-id"] = correlation_id
- response.headers["x-response-time-ms"] = duration_ms
```

**Test manually:**
```bash
curl -H "x-request-id: req-manual123" http://localhost:8000/chat \
  -d '{"query":"test"}' -H "Content-Type: application/json"
# Response headers should include x-request-id and x-response-time-ms
# logs.jsonl should have correlation_id field
```

#### 2. **Structured Logging with Metadata** (`app/main.py`)

Before logging `request_received`, bind request context:
```python
# TODO in main.py /chat endpoint:
bind_contextvars(
    user_id_hash="hash_of_actual_user_id",  # Don't log raw user_id
    session_id="session_123",
    feature="chat",
    model="gpt-4-turbo",
    env="lab"
)
logger.info("request_received", query=request.query)
```

**Fields that must appear in logs:**
- `correlation_id` (from middleware)
- `user_id_hash` (hashed, not raw)
- `session_id`
- `feature`
- `model`
- `env`
- `request_received`, `response_sent` event names
- `latency_ms` (duration of request)
- `status_code`
- `quality_score` (mock LLM output quality)

#### 3. **PII Redaction** (`app/pii.py` and `app/logging_config.py`)

PII must be scrubbed BEFORE log is written to file:

**In `app/pii.py`, implement patterns for:**
- [ ] Email: `[^@]+@[^@]+\.[^@]+` → `[EMAIL]`
- [ ] Vietnamese phone: `(0[0-9]{9}|\+?84[0-9]{9})` → `[PHONE]`
- [ ] CCCD (ID card): `\d{12}` → `[ID]`
- [ ] Credit card: `\d{4}-?\d{4}-?\d{4}-?\d{4}` → `[CARD]`

**In `app/logging_config.py`:**
- Register PII processor in the structlog chain BEFORE JSON rendering
- Processor should scan all log fields and replace sensitive patterns

**Processing order matters:**
```
Raw data → PII Scrubber → JSON Renderer → File Writer
```

If you scrub AFTER JSON rendering, it's too late.

#### 4. **Validation**

Run validator and save baseline:
```bash
# Before making changes (for reference):
python scripts/validate_logs.py > submission/evidence/01-log-baseline.txt

# Delete old logs to get clean test:
rm data/logs.jsonl

# Restart API and run fresh load test:
python scripts/load_test.py

# Check results (need ≥ 80/100):
python scripts/validate_logs.py
```

**Check manually:**
```bash
# Look for no plain PII in logs:
grep -i "email\|@\|cccd\|thanh.toan" data/logs.jsonl
# Should return nothing or only scrubbed versions like [EMAIL]

# Verify correlation_id in all relevant entries:
grep "correlation_id" data/logs.jsonl | wc -l
```

### Success Check
```bash
✓ validate_logs.py shows ≥ 80/100 score
✓ Correlation ID appears in response headers (x-request-id)
✓ All log entries have correlation_id field
✓ Structured metadata appears: user_id_hash, session_id, feature, model, env
✓ No plain email/phone/CCCD in data/logs.jsonl
✓ PII test file passes: python -m pytest tests/test_pii.py -v
```

---

## ✅ CP2: Tracing, Prompts & Dashboard (80–160 minutes)

### Part A: Instrumentation & Traces (`app/agent.py` with Langfuse)

**Current state:**
- Root observation wraps `LabAgent.run()`
- Missing: child observations for `retrieve()` and LLM calls

**What to add:**

#### 1. **Retrieval Span**
```python
# In LabAgent.retrieve() method:
from langfuse.decorators import observe

@observe(name="retrieval", as_type="span")  
def retrieve(self, query: str) -> list[str]:
    # ... retrieval logic ...
    return results
```

#### 2. **LLM Generation Span**
```python
# In FakeLLM.generate() method:
@observe(
    name="llm_call",
    as_type="generation",  # Not "span"!
)
def generate(self, prompt: str) -> str:
    # Must track:
    # - model name
    # - prompt (masked if contains PII)
    # - output
    # - input_tokens, output_tokens (count or estimate)
    # - cost
    
    output = f"Generated response based on {prompt}"
    
    # Use Langfuse API to attach metadata:
    from langfuse.decorators import current_trace_id
    trace = get_current_trace()
    trace.generation(
        name="llm_generation",
        model="fake-llm-v1",
        input=prompt,
        output=output,
        usage={"input_tokens": 10, "output_tokens": 20},
        metadata={"cost": 0.0003}
    )
    return output
```

#### 2. **Correlation ID in Trace Metadata**
- [ ] Retrieve correlation ID from contextvars
- [ ] Add to trace metadata so trace ↔ log linkage works:
```python
# In root observation or trace initialization:
metadata = {"correlation_id": correlation_id}
trace = observe(metadata=metadata)
```

**Test:**
```bash
# Run a request:
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"What is AI?"}'

# Check Langfuse dashboard:
# - Navigate to your project
# - Find recent trace
# - Expand waterfall → should see root + retrieval + generation spans
# - Check metadata tab → should see correlation_id
```

### Part B: Prompt Versioning (`app/prompt_management.py` and Langfuse)

**Goal:** Prove you can track two versions of a prompt and do a rollback.

#### 1. **Create Prompt in Langfuse**
- [ ] Go to **Langfuse dashboard → Prompts**
- [ ] Click **+ New Prompt**
- [ ] Name: `day13-chat` (match `.env` LANGFUSE_PROMPT_NAME)
- [ ] Label: `production`
- [ ] Content v1:
  ```
  You are a helpful AI assistant.
  Context: {context}
  User question: {query}
  ```

#### 2. **Create Version 2**
- [ ] In Langfuse, click **Versions** for that prompt
- [ ] Click **+ New Version**
- [ ] Label: `candidate`
- [ ] Change content (e.g., add instruction: "Be concise"):
  ```
  You are a helpful AI assistant. Be concise.
  Context: {context}
  User question: {query}
  ```

#### 3. **Fetch & Use in Code** (`app/prompt_management.py`)
```python
# app/prompt_management.py should:
# - Load prompt from Langfuse using public key
# - Pass format: name="day13-chat", label="production" (or "candidate")
# - Inject into LLM prompt
# - Track which version in trace metadata

from langfuse.decorators import get_current_trace
from langfuse import Langfuse

def get_prompt_version(name: str, label: str) -> str:
    client = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    )
    prompt = client.get_prompt(name=name, label=label)
    return prompt.prompt
```

#### 4. **Rollback**
- [ ] In Langfuse, switch `production` label from v1 → v2:
  - Go to **Prompts → day13-chat**
  - Find version 2 (candidate)
  - Click **Set as Production**
- [ ] In code, fetch with `label="production"` → will now get v2
- [ ] Screenshot evidence showing version labels before/after

**Test:**
```bash
# Run two requests, one with each label:
# (via env var or code change)
LANGFUSE_PROMPT_LABEL=production python scripts/load_test.py
# Screenshot Langfuse showing trace with v1

# Then promote v2:
# (done in Langfuse UI)

# Run again with same label:
python scripts/load_test.py
# Screenshot trace with v2
```

### Part C: Metrics & Dashboard (`data/logs.jsonl` → `config/dashboard.yaml`)

**Data source:** structured logs in `data/logs.jsonl` (NOT Langfuse)

Each log line has:
- `timestamp`
- `correlation_id`
- `event` ("request_received" or "response_sent")
- `latency_ms`
- `status_code`
- `quality_score`
- `retrieval_success` (true/false)
- `user_id_hash`, `session_id`, `feature`, `model`, `env`

**Dashboard must have 6 panels:**

#### Panel 1: **Latency (P50, P95, P99)**
- Metric: Latency percentiles over time
- Source: `latency_ms` from `response_sent` logs
- Y-axis: milliseconds
- Expected: P50 ~50ms, P95 ~200ms, P99 ~500ms

#### Panel 2: **TTFT (Time To First Token)**
- Metric: First token latency percentiles
- Source: `ttft_ms` from logs (may need to add this field)
- Y-axis: milliseconds
- Expected: P95 ~30ms

#### Panel 3: **Request Rate (Traffic)**
- Metric: Requests per minute
- Source: Count of `request_received` events
- Y-axis: requests/min
- Expected: Should rise during load test

#### Panel 4: **Error Rate**
- Metric: % of requests with status_code ≠ 200
- Source: Count of `response_sent` with `status_code != 200`
- Y-axis: percentage
- Formula: `errors / total_requests * 100`

#### Panel 5: **Retrieval Success Rate**
- Metric: % of requests where `retrieval_success == true`
- Source: Count of `response_sent` logs
- Y-axis: percentage
- Important: Distinguish from error rate (retrieval fail ≠ 500 error)

#### Panel 6: **Quality Score Distribution**
- Metric: Average or percentile of `quality_score`
- Source: `quality_score` from `response_sent`
- Y-axis: score (0–100)
- Show trend over time

**Implementation:**
- [ ] Update `config/dashboard.yaml` with 6 panel definitions
- [ ] Each panel: name, metric, aggregation, threshold
- [ ] Follow format in [DASHBOARD_SETUP.md](docs/DASHBOARD_SETUP.md)

**Validation:**
```bash
python scripts/validate_dashboard.py
# Must output: HỢP LỆ: 6/6 panel
```

### Part D: SLO & Alerts (`config/slo.yaml` and `config/alert_rules.yaml`)

#### 1. **SLO Definition** (`config/slo.yaml`)
Example:
```yaml
slo:
  name: "Chat API Latency SLO"
  objective: 0.95  # 95% of requests meet target
  window: 30d  # 30-day rolling window
  target_metric: "p95_latency_ms"
  target_value: 500  # 500ms
  
error_budget:
  total_error: 0.05  # 5% allowed error
  consumed: 0.02  # ~2% consumed so far (calculated from recent data)
  remaining: 0.03  # ~3% remaining budget
```

**Why:** Lets on-call know how much "broken" time is left before SLO breach.

#### 2. **Alert Rules** (`config/alert_rules.yaml`)
Must have **3 symptom-based alerts** (not threshold-based):

**Alert 1: High Latency**
```yaml
- name: "High P95 Latency"
  condition: "p95_latency_ms > 800"  # Abnormal rise from baseline 500
  duration: "5m"  # Sustained for 5 minutes
  severity: "warning"
  owner: "on-call"
  slack_channel: "#alerts-chat-api"
  runbook: "See docs/alerts.md → High P95 Latency section"
```

**Alert 2: High Error Rate**
```yaml
- name: "Elevated Error Rate"
  condition: "error_rate_percent > 5"
  duration: "2m"
  severity: "critical"
  owner: "on-call"
  slack_channel: "#alerts-critical"
  runbook: "See docs/alerts.md → Elevated Errors section"
```

**Alert 3: Retrieval Failures**
```yaml
- name: "Retrieval Success Drop"
  condition: "retrieval_success_rate < 90"
  duration: "5m"
  severity: "warning"
  owner: "search-team"
  slack_channel: "#search-alerts"
  runbook: "See docs/alerts.md → Retrieval Issues section"
```

#### 3. **Runbook Documentation** (`docs/alerts.md`)
For each alert, document:
- **Detection:** How to notice the alert
- **Investigation:** Steps to debug (Metrics → Logs → Traces)
- **Mitigation:** Quick temporary fix
- **Prevention:** Long-term fix

Example:
```markdown
## High P95 Latency

**Detection:** Alert fires when P95 > 800ms for 5 minutes

**Investigation:**
1. Check dashboard latency panel → identify time window
2. Filter logs by time window → find slow requests
3. Grab correlation_id from slow request
4. Find trace in Langfuse → see which span is slow
5. Check if retrieval, LLM, or middleware is bottleneck

**Mitigation (quick):** Restart API server to clear caches
**Prevention (long-term):** Increase retrieval timeout, optimize prompt
```

### Success Check for CP2
```bash
✓ python scripts/validate_dashboard.py → HỢP LỆ: 6/6 panel
✓ 10+ traces in Langfuse (your personal project)
✓ Each trace has retrieval + generation child spans
✓ Each trace metadata includes correlation_id
✓ Two prompt versions (v1/v2) created in Langfuse
✓ One rollback demonstrated and evidenced
✓ config/slo.yaml and config/alert_rules.yaml completed
✓ docs/alerts.md has 3 runbooks with Metrics → Logs → Traces steps
```

---

## ✅ CP3: Challenge Investigation (160–210 minutes)

**Note:** Only run this when Lab Coach announces challenge is open and provides `config/challenge.json`.

### What needs to be done

1. **Receive Challenge File**
   - [ ] Lab Coach sends `config/challenge.json` (private to K4-L3A)
   - [ ] Save to `config/challenge.json` (already in `.gitignore`)
   - [ ] **DO NOT** push, share, or force-commit this file

2. **Inject Incident**
   ```bash
   python scripts/inject_incident.py
   python scripts/load_test.py --challenge --concurrency 5
   ```
   This creates an artificial incident in the system.

3. **Investigation Workflow** (Metrics → Logs → Traces)

   **Step 1: Identify symptoms in Metrics**
   - [ ] Open dashboard
   - [ ] Look for anomaly: high latency, error spike, retrieval failure
   - [ ] Note time range (e.g., 14:22–14:27)

   **Step 2: Find affected request in Logs**
   - [ ] Filter `data/logs.jsonl` for time window
   - [ ] Look for abnormal `latency_ms` or `status_code`
   - [ ] Extract one `correlation_id` from a problematic request

   **Step 3: Find corresponding Trace**
   - [ ] Go to Langfuse
   - [ ] Search traces by `correlation_id` (in metadata)
   - [ ] Open trace waterfall
   - [ ] Compare span durations and status

   **Step 4: Determine Root Cause**
   - [ ] Identify which span is slow or failed
   - [ ] Cross-reference with code logic:
     - Slow retrieval? → Search index issue
     - Slow LLM? → Token limit, model overload
     - Error in middleware? → Serialization, context leak
   - [ ] **Root cause must be supported by evidence from all 3 layers**

4. **Document in Report**
   - [ ] Save to `submission/REPORT.md` Section 7 (Challenge Investigation)
   - [ ] Include:
     - Challenge ID (from file)
     - Time window
     - Symptom (metric, log, trace)
     - Root cause
     - Fix action (what code change)
     - Preventive measure (monitoring/alert)

### Success Check
```bash
✓ Challenge evidence gathered: metric + log + trace
✓ Evidence shows same correlation_id in log and trace metadata
✓ Root cause is technical and supported by data
✓ Written to submission/REPORT.md Section 7
✓ All evidence screenshots saved to submission/evidence/
```

---

## ✅ CP4: Report & Final Submission (210–240 minutes)

### What needs to be done

1. **Complete `submission/REPORT.md`**
   - [ ] Fill all 9 sections:
     1. Student info (name, MSSV, repo URL, commit SHA)
     2. Evidence index (paths to all screenshots)
     3. Technical results (baseline vs. final scores)
     4. Logging & PII explanation
     5. Tracing & prompt versioning explanation
     6. Dashboard, SLO & alerts explanation
     7. Challenge investigation (root cause + fix)
     8. Personal reflection (decisions, blockers, learnings)
     9. Checklist

2. **Collect Evidence** (screenshots/outputs)
   - [ ] **01-pytest.png:** Final test run output
   - [ ] **02-log-validator.png:** `validate_logs.py` score ≥ 80
   - [ ] **03-dashboard-validator.png:** `validate_dashboard.py` 6/6
   - [ ] **04-structured-log.png:** Sample line from `data/logs.jsonl` (no PII)
   - [ ] **05-pii-redaction.png:** Example showing email → [EMAIL]
   - [ ] **06-trace-list.png:** Langfuse trace list (your project)
   - [ ] **07-trace-waterfall.png:** One trace with retrieval + generation spans
   - [ ] **08-trace-metadata.png:** Metadata tab showing correlation_id
   - [ ] **09-prompt-versions.png:** Two prompt versions in Langfuse UI
   - [ ] **10-prompt-rollback.png:** Before/after rollback labels
   - [ ] **11-dashboard-overview.png:** Your 6-panel dashboard with data
   - [ ] **12-incident-metric.png:** Dashboard showing anomaly (CP3 only)
   - [ ] **13-incident-log.png:** Log excerpt with correlation_id
   - [ ] **14-incident-trace.png:** Trace waterfall with slow/failed span
   
   Save to `submission/evidence/` with these exact names.

3. **Verify No Secrets Leaked**
   ```bash
   # Check for API keys, secrets:
   grep -r "sk-lf-\|pk-lf-\|LANGFUSE_SECRET" .
   # Should return nothing (only in .env which is .gitignore'd)
   
   # Check for PII in evidence:
   grep -l "@\|0[0-9]\{9\}\|thanh.toan" submission/evidence/*
   # Should find nothing
   ```

4. **Final Tests**
   ```bash
   python -m pytest -q
   python scripts/validate_logs.py
   python scripts/validate_dashboard.py
   git status --short  # Should show only submission/ changes
   git log -1 --oneline
   ```

5. **Submit to LMS/Codelabs**
   - [ ] Repository URL: `https://github.com/legiabao9873/K4-L3-DAY13-LeGiaBao-02887-Monitoring-LLMOps`
   - [ ] Commit SHA: (from `git log -1 --oneline`)
   - [ ] Deadline: 23:59:59 Asia/Ho_Chi_Minh today

### Success Check
```bash
✓ submission/REPORT.md is complete (9 sections filled)
✓ submission/evidence/ has 14 screenshots (01–14)
✓ All links in REPORT.md use relative paths and work locally
✓ No .env, secrets, or PII in repo
✓ Tests and validators pass on commit SHA being submitted
✓ URL and commit SHA submitted to LMS before deadline
```

---

## 🔍 Quick Reference: Investigation Flow

When stuck on CP3, follow this systematic flow:

```
1. METRICS: "What went wrong and when?"
   → Dashboard panel shows anomaly + time window

2. LOGS: "Which request was affected?"
   → Filter data/logs.jsonl by time
   → Extract correlation_id from abnormal entry
   → Verify metadata matches expected request

3. TRACES: "Which step failed?"
   → Langfuse: Search by correlation_id
   → Compare span durations to baseline
   → Check error status and error message

4. ROOT CAUSE: "Why?"
   → Span slow? → resource bottleneck, queue, network
   → Span error? → logic bug, data format, timeout
   → Multiple spans affected? → cascade failure
```

**Evidence checklist:**
- [ ] Metric: clear anomaly (spike, drop, threshold breach)
- [ ] Log: correlation_id + metadata + latency value
- [ ] Trace: span with matching correlation_id + error/duration mismatch
- [ ] Root cause: technical explanation of why that span behaved badly

---

## 📚 Key Files to Modify

| File | Purpose | TODOs | Status |
|---|---|---|---|
| `app/middleware.py` | Correlation ID handling | 4 TODOs (clear, generate, bind, return) | CP1 |
| `app/main.py` | Request context binding | 1 TODO (bind metadata) | CP1 |
| `app/pii.py` | PII pattern definitions | Patterns for email/phone/CCCD/card | CP1 |
| `app/logging_config.py` | PII processor registration | Register scrubber in chain | CP1 |
| `app/agent.py` | Span instrumentation | Add child observations for retrieve/generate | CP2 |
| `app/prompt_management.py` | Prompt versioning | Fetch from Langfuse, use labels | CP2 |
| `config/dashboard.yaml` | Metrics dashboard | 6 panel definitions | CP2 |
| `config/slo.yaml` | SLO configuration | Objectives, targets, error budget | CP2 |
| `config/alert_rules.yaml` | Alert definitions | 3 symptom-based alerts | CP2 |
| `docs/alerts.md` | Runbooks | Detection, investigation, mitigation | CP2 |
| `submission/REPORT.md` | Individual report | 9 sections + evidence index | CP4 |

---

## 🎓 Learning Outcomes

By end of lab, you will understand:

1. **Structured Logging**
   - Why correlation IDs matter (request tracing across services)
   - How to bind context to avoid data leakage
   - When and how to scrub PII (processor order matters)

2. **Observability Signals**
   - Metrics tell you "how bad?" (latency, error %, success rate)
   - Logs tell you "which request?" (correlation ID + metadata)
   - Traces tell you "where?" (which span, which step)

3. **LLM Operations**
   - Cost + tokens traceable per request
   - Prompt versions trackable and rollbackable
   - Quality metrics vs. reliability metrics

4. **Incident Response**
   - Metrics identify symptom
   - Logs pinpoint request
   - Traces isolate root cause
   - **Only conclude when all 3 layers agree**

---

## ⏰ Time Allocation Guide

- **CP0 (30 min):** Setup, Langfuse, baseline → 15 min buffer
- **CP1 (50 min):** Middleware, logging, PII → 10 min buffer
- **CP2 (80 min):** Spans, prompts, dashboard, SLO, alerts → 20 min buffer
- **CP3 (50 min):** Challenge investigation, root cause → 10 min buffer
- **CP4 (30 min):** Report, evidence, final checks → 5 min buffer

**Total:** 240 min allocated, 60 min buffer for blockers

---

## 🆘 If Stuck

| Problem | Quick Fix |
|---|---|
| Logs still old after code fix | Delete `data/logs.jsonl`, restart API, re-run load test |
| Langfuse shows no traces | Check `.env` keys, restart API, verify trace code added |
| Validator fails but code looks right | Reread error msg carefully; check field names in config files |
| Challenge file not provided | Continue practice with `--scenario` flag in load test |
| Time running short | Skip optional evidence, focus on core CP1–CP2 requirements |

See `docs/GUIDE.md` for detailed troubleshooting.

---

**Generated:** 2026-09-29  
**For:** K4-L3A Day 13 Monitoring & LLMOps Lab  
**Status:** Ready to start CP0
