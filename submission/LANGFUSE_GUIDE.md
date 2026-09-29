# 📖 Hướng dẫn Langfuse Dashboard — Traces, Waterfall, Metadata

> Giải thích chi tiết từng phần để bạn hiểu rõ ý nghĩa

---

## 1️⃣ **Traces ở đâu?**

### Bước 1: Mở Langfuse
```
https://cloud.langfuse.com → Login
```

### Bước 2: Chọn Project
```
Góc trên trái → Dropdown project → Chọn "day13-k4-l3a-02887"
```

### Bước 3: Vào Traces Tab
```
Menu trái:
├── Observability (click)
│   ├── Traces ← CLICK HERE
│   ├── Metrics
│   └── Alerts
```

### Bước 4: Xem Danh Sách Traces
```
Sẽ thấy bảng như này:

┌─────────────────────────────────────────────────────┐
│ Traces (10 items)                                   │
├──────────┬──────────────┬────────────┬──────────────┤
│ Trace ID │ Name         │ Time       │ Duration     │
├──────────┼──────────────┼────────────┼──────────────┤
│ abc123xy │ day13-agent  │ 14:22:45Z  │ 452ms  ✓     │
│ def456ab │ day13-agent  │ 14:22:47Z  │ 389ms  ✓     │
│ ghi789cd │ day13-agent  │ 14:22:48Z  │ 401ms  ✓     │
│ jkl012ef │ day13-agent  │ 14:22:50Z  │ 395ms  ✓     │
│ ...      │ ...          │ ...        │ ...          │
└──────────┴──────────────┴────────────┴──────────────┘

✓ = Success (xanh)
✗ = Error (đỏ)
```

**Ý nghĩa:**
- **Trace ID:** Định danh duy nhất của request (giống correlation_id)
- **Name:** Tên root observation (ở đây là "day13-agent-request")
- **Time:** Thời điểm request được ghi nhận
- **Duration:** Tổng thời gian request hoàn thành (452ms)

---

## 2️⃣ **Waterfall là gì?**

### Click vào 1 Trace để Mở Waterfall
```
Click vào trace ID → Mở chi tiết trace
```

### Waterfall View (Cây thời gian)
```
Sẽ thấy cấu trúc như này:

┌────────────────────────────────────────────────────────┐
│ Trace Waterfall - day13-agent-request                 │
├────────────────────────────────────────────────────────┤
│                                                        │
│ ▼ lab-agent-run (ROOT) ■━━━━━━━━━━━━━━━━━━━━━□ 452ms │
│   ├─ ▼ retrieve (SPAN) ■━━━━━━━━□ 98ms                │
│   │   └─ Retrieval completed                          │
│   │                                                   │
│   ├─ ▼ llm_generation (GEN) ■━━━━━━━━━━━━━━□ 156ms   │
│   │   ├─ model: claude-sonnet-4-5                     │
│   │   ├─ tokens_in: 156                               │
│   │   ├─ tokens_out: 89                               │
│   │   └─ cost_usd: 0.001234                           │
│   │                                                   │
│   └─ Request complete ✓                               │
│                                                        │
└────────────────────────────────────────────────────────┘

Timeline (horizontal):
0ms         100ms        200ms        300ms        400ms
├────────────────────────────────────────────────────────┤
```

### 📊 Ý Nghĩa Waterfall

**Cấu trúc 3 Level:**

```
1. ROOT (lab-agent-run) — Thời gian tổng: 452ms
   ├─ Là root observation — bao quanh toàn bộ request
   └─ Duration = 452ms (từ bắt đầu đến kết thúc)

2. CHILD 1 (retrieve) — Thời gian: 98ms
   ├─ Là span con của root
   ├─ Bắt đầu lúc 0ms, kết thúc lúc 98ms
   ├─ Ý nghĩa: Thời gian vector DB lấy tài liệu
   └─ Nằm TRONG root (từ 0ms → 98ms)

3. CHILD 2 (llm_generation) — Thời gian: 156ms
   ├─ Là span con của root
   ├─ Bắt đầu lúc 98ms, kết thúc lúc 254ms (156ms duration)
   ├─ Ý nghĩa: Thời gian gọi LLM + generate response
   └─ Nằm TRONG root (từ 98ms → 254ms)
```

**Tại sao 452ms > 98 + 156?**
- Vì còn overhead: middleware, parsing, logging (≈ 198ms)

---

## 3️⃣ **Metadata là gì?**

### Cách Xem Metadata
```
Trong chi tiết trace, tìm tab "Metadata" hoặc scroll xuống
```

### Metadata Fields — Chi Tiết Từng Field
```
┌─────────────────────────────────────────────────────┐
│ Trace Metadata                                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│ trace_id              │ abc123xy-def456-ghi789     │
│   ➜ Định danh duy nhất của request                 │
│   ➜ Dùng để nối log + trace                        │
│                                                     │
│ correlation_id        │ req-d3cf084b               │
│   ➜ ID sinh ra ở middleware                        │
│   ➜ Xuất hiện trong logs.jsonl                     │
│   ➜ Dùng để nối từ metric → log → trace            │
│                                                     │
│ model                 │ claude-sonnet-4-5          │
│   ➜ Mô hình LLM được sử dụng                       │
│                                                     │
│ environment           │ dev                        │
│   ➜ Môi trường (dev/staging/prod)                  │
│                                                     │
│ user_id_hash          │ 2055254ee30a               │
│   ➜ Hash của user ID (không lộ ID thật)           │
│                                                     │
│ session_id            │ s01                        │
│   ➜ Session identifier                             │
│                                                     │
│ tags                  │ ["lab", "qa", "sonnet"]   │
│   ➜ Tags phân loại trace                           │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 4️⃣ **Generation Span Details — Ý Nghĩa Ở Đây**

### Khi Click vào `llm_generation` Span

```
┌──────────────────────────────────────────────────────┐
│ Generation - llm_generation                          │
├──────────────────────────────────────────────────────┤
│                                                      │
│ INPUT:                                              │
│ ┌────────────────────────────────────────────────┐  │
│ │ Feature=qa                                     │  │
│ │ Docs=Refunds are available within 7 days     │  │
│ │ Question=What is your refund policy?         │  │
│ └────────────────────────────────────────────────┘  │
│                                                      │
│ USAGE & COST:                                       │
│ ┌────────────────────────────────────────────────┐  │
│ │ input_tokens:     156                         │  │
│ │ output_tokens:    89                          │  │
│ │ cost_usd:         0.001234                    │  │
│ │ model:            claude-sonnet-4-5           │  │
│ │ ttft_ms:          45                          │  │
│ └────────────────────────────────────────────────┘  │
│                                                      │
│ OUTPUT:                                             │
│ ┌────────────────────────────────────────────────┐  │
│ │ Starter answer. You should improve this...   │  │
│ └────────────────────────────────────────────────┘  │
│                                                      │
│ METADATA:                                           │
│ ┌────────────────────────────────────────────────┐  │
│ │ prompt_name:      day13-chat                  │  │
│ │ prompt_label:     production                  │  │
│ │ prompt_version:   v1                          │  │
│ │ prompt_source:    langfuse                    │  │
│ └────────────────────────────────────────────────┘  │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 📊 Ý Nghĩa Từng Field

| Field | Ý Nghĩa | Dùng Để Làm Gì |
|---|---|---|
| **input_tokens** | Số token đầu vào (prompt + context) | Tính cost, optimize prompt length |
| **output_tokens** | Số token đầu ra (response) | Tính cost, kiểm tra response length |
| **cost_usd** | Chi phí của request này | Track tổng cost, budget monitoring |
| **model** | Model được sử dụng | So sánh cost giữa models |
| **ttft_ms** | Time To First Token (45ms) | Đo latency user thấy đầu tiên |
| **prompt_name** | Tên prompt trên Langfuse | Version control prompts |
| **prompt_label** | Label hiện tại (production/candidate) | Track rollback |
| **prompt_version** | Version ID (v1, v2, v3...) | Audit trail |
| **prompt_source** | Từ đâu (langfuse vs local) | Debug nếu fetch prompt fail |

---

## 5️⃣ **Retrieval Span Details**

### Khi Click vào `retrieve` Span

```
┌──────────────────────────────────────────────────────┐
│ Span - retrieve                                      │
├──────────────────────────────────────────────────────┤
│                                                      │
│ Duration:         98ms                              │
│ Status:           ✓ Success                         │
│ Start Time:       2026-09-29T14:22:45.123Z          │
│ End Time:         2026-09-29T14:22:45.221Z          │
│                                                      │
│ METADATA:                                           │
│ ┌────────────────────────────────────────────────┐  │
│ │ doc_count:        1                           │  │
│ │ retrieval_success: true                       │  │
│ │ query_preview:    "What is your refund..."   │  │
│ └────────────────────────────────────────────────┘  │
│                                                      │
│ OUTPUT:                                             │
│ ┌────────────────────────────────────────────────┐  │
│ │ [                                             │  │
│ │   "Refunds are available within 7 days..."  │  │
│ │ ]                                             │  │
│ └────────────────────────────────────────────────┘  │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**Ý nghĩa:**
- **Duration 98ms**: Bình thường (baseline ~100ms)
- **Status ✓**: Lấy tài liệu thành công
- **doc_count: 1**: Tìm được 1 tài liệu matching
- **retrieval_success: true**: Không timeout, không lỗi

---

## 6️⃣ **Nối Logs ↔ Traces — Dùng Correlation ID**

### Flow Metric → Log → Trace

```
METRIC (Dashboard)
  ↓ "Latency spike at 14:22:45"
  ↓
LOG (data/logs.jsonl)
  ↓ Tìm trong logs lúc 14:22:45
  ↓ Lấy correlation_id = "req-d3cf084b"
  ↓
TRACE (Langfuse)
  ↓ Search metadata: correlation_id = "req-d3cf084b"
  ↓ Tìm được trace với ID abc123xy
  ↓ Mở waterfall → thấy retrieve span = 2500ms (chậm!)
  ↓
ROOT CAUSE: "Retrieval timeout — vector DB slow"
```

### Ví Dụ Thực Tế

**Log Entry (data/logs.jsonl):**
```json
{
  "correlation_id": "req-d3cf084b",
  "event": "response_sent",
  "latency_ms": 2500,
  "ts": "2026-09-29T14:22:45.123Z",
  "tool_success": true
}
```

**Trace Metadata (Langfuse):**
```
correlation_id: "req-d3cf084b"  ← SAME ID!
trace_id: "abc123xy"
```

**Waterfall:**
```
├─ lab-agent-run [0–2500ms] (root)
│  ├─ retrieve [0–2400ms] ← 🔴 SLOW! (expected ~100ms)
│  └─ llm_generation [2400–2480ms]
```

**Kết luận:** Retrieval chậm 2400ms → Đó là nguyên nhân metric spike!

---

## 7️⃣ **Prompt Versioning — Rollback Demo**

### Scenario: A/B Test Prompt

**Phiên bản 1 (v1) - Baseline:**
```
Label: baseline
Content: "You are helpful. Context: {docs}"
```

**Phiên bản 2 (v2) - Candidate (Improvement):**
```
Label: candidate  
Content: "You are helpful. Be concise. Context: {docs}"
```

### Demo Rollback

**Step 1: Run với v1 (baseline)**
```bash
LANGFUSE_PROMPT_LABEL=baseline python scripts/load_test.py
# Trace: correlation_id = req-aaa111, prompt_version = v1
```

**Step 2: Promote v2 → production**
```
Langfuse UI → Prompts → day13-chat → v2 → "Set as Production"
```

**Step 3: Run lại (tự động lấy production label)**
```bash
LANGFUSE_PROMPT_LABEL=production python scripts/load_test.py
# Trace: correlation_id = req-bbb222, prompt_version = v2
```

**Evidence Rollback:**
- Screenshot trước: v1 = production
- Screenshot sau: v2 = production
- Chứng minh: "req-aaa111 dùng v1, req-bbb222 dùng v2" ✅

---

## 📸 **Khi Chụp Evidence, Cần Hiển Thị:**

### Evidence 06 - Trace List
```
✓ Project name: day13-k4-l3a-02887
✓ Tối thiểu 10 trace entries
✓ Mỗi trace có ID, name, time, duration
```

### Evidence 07 - Trace Waterfall
```
✓ 3-level structure: root → retrieve → llm_generation
✓ Duration của mỗi span hiểu được
✓ Status success ✓
```

### Evidence 08 - Trace Metadata
```
✓ correlation_id hiển thị rõ
✓ model, tokens_in, tokens_out, cost_usd
✓ prompt_name, prompt_label, prompt_version
✓ user_id_hash (hashed, không lộ raw ID)
```

### Evidence 09 - Prompt Versions
```
✓ Prompt name: day13-chat
✓ Danh sách versions (v1, v2, v3...)
✓ Labels (baseline, candidate, production)
```

### Evidence 10 - Prompt Rollback
```
✓ Before: v1 = production label
✓ After: v2 = production label
✓ Hoặc 2 screenshots tách riêng
```

---

## 🎯 **TL;DR — Quick Summary**

| Component | Là gì | Vị trí |
|---|---|---|
| **Traces** | Danh sách request | Langfuse → Traces tab |
| **Waterfall** | Cây thời gian (root + children) | Click trace ID |
| **Metadata** | Dữ liệu chi tiết (correlation_id, tokens, cost) | Scroll down trong trace |
| **Retrieval Span** | Thời gian lấy tài liệu | Child span #1 |
| **Generation Span** | Thời gian LLM generate | Child span #2 + tokens + cost |
| **Correlation ID** | Nối log ↔ trace | Metadata tab |
| **Prompt Version** | Track prompt changes | Generation span metadata |

---

**Bây giờ bạn mở Langfuse xem traces nhé! Thấy gì thì báo tôi! 🚀**
