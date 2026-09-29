# 📸 Evidence Checklist — Hướng dẫn chụp & lưu từng CP

> **Hướng dẫn chi tiết:** Chụp gì, điền gì, lưu ở đâu cho mỗi checkpoint

---

## 🎯 CP0: Setup & Baseline (14:00–14:30)

### Nhiệm vụ
1. Setup Python venv + install requirements
2. Tạo Langfuse project cá nhân
3. Config `.env`
4. Chạy API + baseline validators

### Evidence cần chụp

#### **01-pytest.png** (Baseline)
```bash
# Terminal: chạy
python -m pytest -q

# Chụp screenshot kết quả (pass/fail count)
# Lưu: submission/evidence/01-pytest.png
```

**Nội dung screenshot:**
- Dòng cuối: `22 passed` (hoặc kết quả hiện tại)
- Đủ để chứng minh tests chạy được

---

#### **02-log-validator.png** (Baseline - điểm sẽ thấp)
```bash
# Terminal: chạy
python scripts/validate_logs.py

# Chụp screenshot kết quả
# Lưu: submission/evidence/02-log-validator-baseline.png
```

**Nội dung screenshot:**
- Score (ví dụ: `Score: 35/100` - thấy là bình thường vì chưa fix)
- Dòng "PII found" hoặc "Missing correlation_id"

**Chú ý:** Đây là baseline - sẽ được chụp lại ở CP1 khi ≥80

---

#### **03-dashboard-validator.png** (Baseline)
```bash
# Terminal: chạy
python scripts/validate_dashboard.py

# Chụp screenshot kết quả
# Lưu: submission/evidence/03-dashboard-validator-baseline.png
```

**Nội dung screenshot:**
- Kết quả validation (ví dụ: `2/6 panel`)
- Error messages về missing panels

---

### Điều cần ghi vào REPORT.md (Section 3)

```markdown
## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 35/100 | 80/100 | PII được scrub từ CP1 |
| `validate_dashboard.py` | 2/6 | 6/6 | 4 panel thêm vào CP2 |
| `pytest` | 22 passed | 22 passed | Không thay đổi |
```

---

## 🎯 CP1: Logging & PII (14:30–15:20)

### Nhiệm vụ
1. Fix middleware.py - correlation ID
2. Fix main.py - bind metadata
3. Fix pii.py - PII patterns
4. Fix logging_config.py - PII processor

### Evidence cần chụp

#### **04-structured-log.png** (Structured Log JSON)
```bash
# Terminal: xem một dòng log
tail -1 data/logs.jsonl | python -m json.tool

# Hoặc: cat một dòng cụ thể
cat data/logs.jsonl | head -5 | tail -1

# Chụp screenshot
# Lưu: submission/evidence/04-structured-log.png
```

**Nội dung screenshot phải hiển thị:**
```json
{
  "ts": "2026-09-29T...",
  "event": "response_sent",
  "correlation_id": "req-a1b2c3d4",
  "latency_ms": 152,
  "user_id_hash": "hash_...",
  "session_id": "sess_...",
  "feature": "chat",
  "model": "claude-sonnet",
  "env": "dev"
}
```

---

#### **05-pii-redaction.png** (PII Scrubbed)
```bash
# Terminal: chạy load test
python scripts/load_test.py

# Kiểm tra logs - tìm email, điện thoại bị che
grep -i "email\|\[EMAIL\]\|0[0-9]\{9\}\|\[PHONE\]" data/logs.jsonl | head -3

# Chụp screenshot cho thấy:
# - Original: "user@example.com" → Scrubbed: "[EMAIL]"
# - Original: "0912345678" → Scrubbed: "[PHONE]"
# Lưu: submission/evidence/05-pii-redaction.png
```

**Nội dung screenshot phải hiển thị:**
- Tối thiểu 2 ví dụ scrub: email → [EMAIL], phone → [PHONE]
- Hoặc: CCCD 12 chữ số → [ID], credit card → [CARD]

---

#### **02-log-validator.png** (Final - phải ≥80)
```bash
# Bước 1: Xóa log cũ
rm data/logs.jsonl

# Bước 2: Restart API
# Ctrl+C dừng, rồi:
uvicorn app.main:app --reload --env-file .env

# Bước 3: Chạy load test mới
python scripts/load_test.py

# Bước 4: Validate
python scripts/validate_logs.py

# Chụp screenshot kết quả CUỐI
# Lưu: submission/evidence/02-log-validator.png
```

**Nội dung screenshot phải hiển thị:**
- Score ≥ 80/100 (ví dụ: `Score: 85/100`)
- Danh sách các check pass/fail

**Chú ý:** Thay thế `02-log-validator-baseline.png` bằng phiên bản mới này

---

### Điều cần ghi vào REPORT.md (Section 4)

```markdown
## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:**
  - Middleware kiểm tra header `x-request-id`
  - Nếu không có, sinh `req-<8-hex>`
  - Bind vào structlog context, trả lại response header

- **Các metadata được ghi vào structured log:**
  - correlation_id, user_id_hash, session_id, feature, model, env
  - latency_ms, ttft_ms, tokens_in, tokens_out, cost_usd, quality_score

- **Cách bảo đảm PII được scrub trước khi ghi:**
  - PII processor trong structlog chain (trước JSON renderer)
  - Pattern: email → [EMAIL], phone → [PHONE], CCCD → [ID], card → [CARD]

- **Cách kiểm chứng kết quả:**
  - `validate_logs.py` ≥ 80/100 (evidence 02-log-validator.png)
  - No PII in data/logs.jsonl (evidence 05-pii-redaction.png)
```

---

## 🎯 CP2: Traces, Prompts & Dashboard (15:20–16:40)

### Nhiệm vụ
1. Thêm `@observe` cho retrieve() và generate()
2. Tạo prompt v1/v2 trên Langfuse
3. Xây dựng 6-panel dashboard
4. Hoàn thiện SLO, alerts, runbooks

### Evidence cần chụp

#### **06-trace-list.png** (Danh sách Traces)
```bash
# Web: Mở Langfuse dashboard
# https://cloud.langfuse.com → project day13-k4-l3a-02887
# → Traces tab

# Chụp screenshot danh sách traces (tối thiểu 10)
# Lưu: submission/evidence/06-trace-list.png
```

**Nội dung screenshot phải hiển thị:**
- Project name: `day13-k4-l3a-02887`
- Tối thiểu 10 trace entries
- Mỗi trace có ID, timestamp, status

---

#### **07-trace-waterfall.png** (Trace với Child Spans)
```bash
# Web: Langfuse → Traces → Click vào một trace

# Chụp screenshot waterfall (phải thấy 3 level):
# ├── lab-agent-run (root)
# │   ├── retrieve (span)
# │   └── llm_generation (generation)
# Lưu: submission/evidence/07-trace-waterfall.png
```

**Nội dung screenshot phải hiển thị:**
- Root observation: `lab-agent-run`
- Child span 1: `retrieve`
- Child span 2: `llm_generation`
- Duration của mỗi span

---

#### **08-trace-metadata.png** (Metadata & Tokens)
```bash
# Web: Trace → Click "Metadata" tab hoặc mở chi tiết

# Chụp screenshot metadata, phải hiển thị:
# - correlation_id
# - model
# - tokens (input_tokens, output_tokens)
# - cost_usd
# - prompt name/version/label
# Lưu: submission/evidence/08-trace-metadata.png
```

**Nội dung screenshot:**
```
metadata:
  correlation_id: "req-12345678"
  model: "claude-sonnet-4-5"
  input_tokens: 156
  output_tokens: 89
  cost_usd: 0.001234
  prompt_name: "day13-chat"
  prompt_label: "production"
  prompt_version: "v1"
```

---

#### **09-prompt-versions.png** (Prompt v1/v2)
```bash
# Web: Langfuse → Prompts → "day13-chat"

# Chụp screenshot danh sách versions
# Phải thấy:
# - v1 (label: production hoặc baseline)
# - v2 (label: candidate)
# Lưu: submission/evidence/09-prompt-versions.png
```

**Nội dung screenshot:**
- Prompt name: `day13-chat`
- Versions danh sách (v1, v2, ...)
- Labels (production, candidate, baseline)

---

#### **10-prompt-rollback.png** (Before/After Promote)
```bash
# Trước promote: Screenshot label v1 có "production"
# Lưu: submission/evidence/10a-prompt-before.png

# Promote v2 to production (trong Langfuse UI)

# Sau promote: Screenshot label v2 có "production"
# Lưu: submission/evidence/10b-prompt-after.png

# Hoặc dùng 1 ảnh kèm chú thích
```

**Nội dung screenshot:**
- Before: v1 = production
- After: v2 = production
- Hoặc 2 ảnh tách riêng

**Ghi chú trong REPORT.md:**
```markdown
- **Trace ID v1 (baseline):** req-v1-xxx-trace-id
- **Trace ID v2 (after rollback):** req-v2-xxx-trace-id
```

---

#### **03-dashboard-validator.png** (Final - phải 6/6)
```bash
# Terminal
python scripts/validate_dashboard.py

# Chụp screenshot
# Lưu: submission/evidence/03-dashboard-validator.png
```

**Nội dung screenshot:**
```
HỢP LỆ: 6/6 panel
```

---

#### **11-dashboard-overview.png** (Dashboard Running)
```bash
# Web: Mở dashboard (ứng dụng tự deploy hoặc Grafana)
# Hoặc screenshot từ terminal + logs

# Chụp screenshot phải hiển thị 6 panels:
# 1. Latency (P50, P95, P99)
# 2. TTFT (Time To First Token)
# 3. Traffic (requests/min)
# 4. Error Rate (%)
# 5. Retrieval Success Rate (%)
# 6. Quality Score (avg)

# Lưu: submission/evidence/11-dashboard-overview.png
```

**Nội dung screenshot:**
- 6 panels với data, time range, threshold lines
- Đơn vị (ms, %, req/min)
- SLO line (ví dụ: P95 latency = 500ms)

**Nếu 1 ảnh nhỏ:** Tách thành:
- `11a-dashboard-latency-traffic.png`
- `11b-dashboard-errors-quality.png`

---

### Điều cần ghi vào REPORT.md (Sections 5-6)

```markdown
## 5. Tracing và prompt versioning

- **Cấu trúc root/retrieval/generation observations:**
  - Root: `lab-agent-run` (as_type="agent")
  - Child 1: `retrieve` (as_type="span")
  - Child 2: `llm_generation` (as_type="generation")
  - Correlation_id propagated to all

- **Prompt v1/v2:**
  - v1: "You are a helpful AI..." (label: baseline)
  - v2: "You are a helpful AI. Be concise." (label: candidate)
  - Promoted v2 to production

- **Trace ID v1:** <trace-id-from-evidence>
- **Trace ID v2:** <trace-id-after-rollback>

## 6. Dashboard, SLO và alerts

- **Dashboard 6 panels:** latency, TTFT, traffic, errors, retrieval success, quality
- **SLO:** 95% of requests < 500ms P95 latency
- **Error budget:** 5% (remaining after current period)
- **3 alerts:**
  1. High P95 Latency (>800ms, 5min, warning)
  2. Elevated Error Rate (>5%, 2min, critical)
  3. Retrieval Success Drop (<90%, 5min, warning)
```

---

## 🎯 CP3: Challenge Investigation (16:40–17:30)

### Nhiệm vụ
1. Nhận `config/challenge.json` từ Lab Coach
2. Inject incident + chạy load test
3. Điều tra: Metric → Log → Trace
4. Kết luận root cause

### Evidence cần chụp

#### **12-incident-metric.png** (Dashboard Anomaly)
```bash
# Web: Dashboard → Metric panel bất thường
# Chụp khoảng thời gian có anomaly:
# - Latency spike
# - Error rate tăng
# - Retrieval success drop

# Lưu: submission/evidence/12-incident-metric.png
```

**Nội dung screenshot:**
- Metric name (e.g., "P95 Latency")
- Anomaly spike (từ 200ms lên 1000ms)
- Time range (e.g., 14:22–14:27 UTC)

---

#### **13-incident-log.png** (Log với Correlation ID)
```bash
# Terminal: lọc log trong time range anomaly
grep "2026-09-29T14:2[2-7]" data/logs.jsonl | \
  grep -E "latency_ms.*[5-9][0-9]{2}|error" | head -3

# Hoặc: cat data/logs.jsonl | python -m json.tool | grep -A20 "14:22"

# Chụp screenshot log line + correlation_id
# Lưu: submission/evidence/13-incident-log.png
```

**Nội dung screenshot:**
```json
{
  "ts": "2026-09-29T14:23:45.123Z",
  "event": "response_sent",
  "correlation_id": "req-incident001",
  "latency_ms": 2500,
  "status_code": 500,
  "tool_name": "retrieval",
  "tool_success": false
}
```

**Ghi nhớ:** `correlation_id: "req-incident001"` → dùng để tìm trace

---

#### **14-incident-trace.png** (Trace Waterfall)
```bash
# Web: Langfuse → Traces
# Search by metadata: correlation_id = "req-incident001"
# Click vào trace đó

# Chụp screenshot waterfall
# Phải thấy span gây ảnh hưởng:
# - retrieve span: 2400ms (chậm!)
# - hoặc llm_generation: error

# Lưu: submission/evidence/14-incident-trace.png
```

**Nội dung screenshot:**
- Trace ID: xxx
- Correlation_id: req-incident001 (phải khớp với log)
- Span tree với span gây ảnh hưởng (ghi nhận duration/error)

---

### Điều cần ghi vào REPORT.md (Section 7)

```markdown
## 7. Điều tra challenge

- **Challenge ID:** [từ config/challenge.json]
- **Khoảng thời gian:** 2026-09-29 14:22–14:27 UTC
- **Triệu chứng từ metrics:** P95 latency 2500ms (bình thường ~150ms)
- **Log line:** correlation_id "req-incident001", latency 2500ms, tool_success=false
- **Trace ID:** [trace-id-from-langfuse]
- **Span gây ảnh hưởng:** retrieve() duration 2400ms
- **Root cause:** RAG/retrieval timeout (STATE["rag_slow"] = true)
- **Fix action:** Tăng timeout hoặc tối ưu retrieval latency
- **Preventive measure:** Alert khi retrieval > 2000ms
```

---

## 🎯 CP4: Finalize & Submit (17:30–18:00)

### Nhiệm vụ
1. Hoàn thiện `submission/REPORT.md`
2. Kiểm tra tất cả 14 evidence
3. Xóa `.env` secret
4. Commit + push

### Evidence cuối cùng

#### **01-pytest.png** (Final)
```bash
# Terminal: chạy lần cuối
python -m pytest -q

# Chụp screenshot kết quả
# Lưu: submission/evidence/01-pytest.png
```

**Chú ý:** Thay thế phiên bản baseline

---

### Checklist điều cần ghi vào REPORT.md

#### **Section 2: Evidence Index**
```markdown
| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |
```

#### **Section 3: Kết quả kỹ thuật**
```markdown
| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 35/100 | 85/100 | PII scrub hoàn thiện |
| `validate_dashboard.py` | 2/6 | 6/6 | Đủ 6 panels |
| `pytest` | 22 passed | 22 passed | - |
| Số traces hợp lệ | 0 | 15+ | Tự tạo trong project cá nhân |
| Số PII leak | nhiều | 0 | Không PII trong logs |
| Latency P95 / TTFT P95 | - | 150ms / 30ms | Normal baseline |
| Retrieval success rate | - | 98% | Baseline |
```

#### **Sections 4-8: Detailed Explanations**
- Điền đầy đủ cách thực hiện từng phần
- Giải thích quyết định kỹ thuật
- Ghi lại lỗi/blocker và cách xử lý

#### **Section 9: Checklist trước nộp**
- [ ] Kết quả đúng commit SHA được nộp
- [ ] 14 ảnh/output mở được bằng đường dẫn tương đối
- [ ] Incident evidence nối M→L→T
- [ ] Traces từ project cá nhân, không lộ key/secret
- [ ] Repo chạy được theo README
- [ ] Không có `.env`, secret, PII thô
- [ ] URL + commit SHA submitted

---

## 📁 **Cấu trúc thư mục submission/ cuối cùng:**

```
submission/
├── REPORT.md                    (9 sections điền đầy đủ)
├── EVIDENCE_CHECKLIST.md        (file này - hướng dẫn)
└── evidence/
    ├── 01-pytest.png
    ├── 02-log-validator.png
    ├── 03-dashboard-validator.png
    ├── 04-structured-log.png
    ├── 05-pii-redaction.png
    ├── 06-trace-list.png
    ├── 07-trace-waterfall.png
    ├── 08-trace-metadata.png
    ├── 09-prompt-versions.png
    ├── 10-prompt-rollback.png
    │   (hoặc 10a + 10b nếu tách)
    ├── 11-dashboard-overview.png
    │   (hoặc 11a + 11b nếu tách)
    ├── 12-incident-metric.png
    ├── 13-incident-log.png
    └── 14-incident-trace.png
```

---

## ⏰ **Timeline tổng hợp:**

| CP | Thời gian | Evidence chụp | Điền REPORT |
|---|---|---|---|
| **CP0** | 14:00–14:30 | 01, 02, 03 (baseline) | Section 3 (baseline) |
| **CP1** | 14:30–15:20 | 04, 05, 02 (≥80) | Section 4 |
| **CP2** | 15:20–16:40 | 06–11, 03 (6/6) | Sections 5–6 |
| **CP3** | 16:40–17:30 | 12, 13, 14 | Section 7 |
| **CP4** | 17:30–18:00 | 01 (final) | Sections 1–2, 8–9 |
| **Submit** | <23:59:59 | ✅ Tất cả 14 files | ✅ Hoàn thiện |

---

**Good luck! 🚀**
