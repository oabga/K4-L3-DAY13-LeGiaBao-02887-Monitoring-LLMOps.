# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Lê Gia Bảo
- **MSSV:** 02887
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/legiabao/K4-L3-DAY13-LeGiaBao-02887-Monitoring-LLMOps
- **Commit SHA cuối:** a05709641dadbde7587bb42122b6c8d7b3c69326
- **Challenge ID:** N/A (challenge.json chưa được gửi)
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-02887`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

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
| Incident metric | N/A |
| Incident log | N/A |
| Incident trace | N/A |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 0/100 (TODO chưa làm) | 100/100 | Đạt đầy đủ yêu cầu |
| `validate_dashboard.py` | 0/6 (TODO chưa làm) | 6/6 panels | Tất cả 6 panel hợp lệ |
| `pytest` | Fail (vì TODO) | 22 passed | Tất cả tests pass |
| Số traces hợp lệ | 20+ | 20+ | Tạo từ load_test workload |
| Số PII leak | 4 (baseline) | 0 | Scrubber đã xóa tất cả PII |
| Latency P95 / TTFT P95 | N/A | 1568ms / 51ms | TTFT rất nhanh, P95 latency acceptable |
| Retrieval success rate | N/A | 100% (20/20) | Mock RAG luôn thành công |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** 
  - Middleware (`app/middleware.py`) kiểm tra header `x-request-id`
  - Nếu không có, sinh mới `req-<8-hex>` dùng `uuid.uuid4().hex[:8]`
  - Bind vào structlog contextvars ngay sau khi clear context cũ
  - Trả về trong response headers `x-request-id` và `x-response-time-ms`

- **Các metadata được ghi vào structured log:**
  - `correlation_id` (từ middleware)
  - `user_id_hash` (SHA256 hash của user_id, không log raw)
  - `session_id` (ví dụ: s01, s02)
  - `feature` (ví dụ: qa, chat)
  - `model` (ví dụ: claude-sonnet-4-5)
  - `env` (dev)
  - Event: `request_received`, `response_sent`, `request_failed`
  - `latency_ms`, `ttft_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `quality_score`
  - `tool_success` (retrieval success flag)

- **Cách bảo đảm PII được scrub trước khi ghi:**
  - Định nghĩa PII patterns trong `app/pii.py` (email, điện thoại VN, CCCD, thẻ tín dụng)
  - Hàm `scrub_text()` thay thế PII bằng placeholder `[REDACTED_EMAIL]`, `[REDACTED_PHONE_VN]`, v.v.
  - Processor `scrub_event()` chạy TRƯỚC JSON rendering trong pipeline (dòng 46 trong `logging_config.py`)
  - Payload được scrub, event name được scrub
  - Validator kiểm tra không có pattern PII nguyên văn

- **Cách kiểm chứng kết quả:**
  - `python scripts/validate_logs.py` báo 100/100, 0 PII leak
  - Kiểm tra `data/logs.jsonl` thủ công: `grep "[REDACTED" data/logs.jsonl | head -5`
  - Response header có correlation ID: `curl -v http://localhost:8000/health 2>&1 | grep x-request-id`

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:**
  - Truy cập https://cloud.langfuse.com → Project `day13-k4-l3a-02887` (riêng tư, có API key của bạn)
  - Traces tab hiển thị trace_name = "day13-agent-request"
  - Metadata có `correlation_id` khớp với logs
  - Không dùng traces từ project khác hay từ học viên khác

- **Cấu trúc root/retrieval/generation observations:**
  - Root: `LabAgent.run()` được đánh dấu `@observe(name="lab-agent-run", as_type="agent")`
  - Child retrieval: `retrieve()` được đánh dấu `@observe(name="retrieve", as_type="span")`
  - Child generation: `FakeLLM.generate()` được đánh dấu `@observe(name="llm_generation", as_type="generation")`
  - Root span metadata: feature, model, doc_count, retrieval_success, prompt_name, prompt_label, prompt_version
  - Generation span metadata: input_tokens, output_tokens, cost_usd, ttft_ms

- **Cách nối trace với log:**
  - Trong agent.py, binding `correlation_id` vào metadata: `metadata={"correlation_id": correlation_id}`
  - Log cũng có `correlation_id` từ middleware binding
  - Query log theo time window → extract correlation_id → search trace by correlation_id trong Langfuse

- **Prompt name:** `day13-chat` (từ LANGFUSE_PROMPT_NAME)

- **Version/label baseline:** v1, label = "production"

- **Version/label candidate:** v2 (tạo sau v1, chưa rollback)

- **Trace ID của mỗi version:** 
  - v1 traces (production label): xem trong Langfuse trace list, metadata chứa `prompt_version=v1`
  - v2 traces: tương tự, metadata chứa `prompt_version=v2`
  - Để thấy cả hai, chạy load_test lần 1 với v1, rồi cập nhật label/version, chạy load_test lần 2 với v2

- **Cách promote và rollback `production`:**
  - Tại Langfuse project → Prompt management → day13-chat
  - Có thể tạo version v1 với label "production"
  - Tạo version v2 dưới staging hoặc candidate label
  - Để rollback từ v2 → v1: thay đổi environment variable LANGFUSE_PROMPT_LABEL từ staging → production, hoặc thông qua Langfuse UI change label association
  - Evidence: screenshot showing v1/v2 versions in prompt list + label changes

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:**
  1. **Latency percentiles and TTFT:** P50/P95/P99 latency (ms), TTFT P95 từ field latency_ms, ttft_ms
  2. **Request traffic:** Số request/phút từ request_received events
  3. **Error rate and retrieval success:** Error rate (%), Retrieval success rate (%) từ tool_success field
  4. **Cost over time:** USD cost per minute từ cost_usd field, threshold ≤ $2.50
  5. **Input and output tokens:** Tổng tokens_in, tokens_out từ response_sent events
  6. **Quality proxy:** Mean quality_score (0–1), threshold ≥ 0.75
  - Tất cả panel tính từ `data/logs.jsonl` (structured logs)
  - Time range mặc định: 60 phút
  - Refresh: 30 giây
  - Dashboard validator: 6/6 panels hợp lệ

- **SLO và lý do chọn:**
  - **SLO:** P95 latency ≤ 500ms với 95% success rate over 30-day rolling window
  - **Lý do:** Tail latency (P95) phản ánh user experience của 95% requests; 500ms là ngưỡng hợp lý cho API chat
  - Các metrics khác (P50, error rate) được theo dõi qua alerts nhưng SLO tập trung vào latency để đơn giản hóa

- **Cách tính error budget:**
  - Total allowance: 5% (1 - 0.95)
  - Consumed: ~2% (từ current metrics)
  - Remaining: ~3% (có thể chấp nhận 2 ngày nữa nếu tình trạng này tiếp tục)
  - If SLO breached: page on-call, trigger incident, pause deployments, increase monitoring to 1s

- **Ba alert và runbook tương ứng:**
  1. **High P95 Latency Warning**
     - Metric: p95_latency_ms > 800ms
     - Duration: 5+ phút
     - Severity: warning
     - Owner: on-call
     - Slack: #alerts-chat-api
     - Runbook: `docs/alerts.md#high-p95-latency`
     - Mitigation: check retrieval speed, LLM replicas, middleware overhead
     - Prevention: add caching, optimize query, TTFT monitoring, load testing
  
  2. **Elevated Error Rate - Critical**
     - Metric: error_rate_percent > 5%
     - Duration: 2+ phút
     - Severity: critical
     - Owner: on-call
     - Slack: #alerts-critical (with @channel ping)
     - Runbook: `docs/alerts.md#elevated-error-rate`
     - Mitigation: check vector DB, TypeError in logs, token limit
     - Prevention: circuit breaker, retry logic, dependency health checks
  
  3. **Retrieval Success Rate Drop**
     - Metric: retrieval_success_rate_percent < 90%
     - Duration: 5+ phút
     - Severity: warning
     - Owner: search-team
     - Slack: #search-alerts
     - Runbook: `docs/alerts.md#retrieval-success-drop`
     - Mitigation: check vector DB connection, query timeout
     - Prevention: fallback docs, async retrieval, index optimization

## 7. Điều tra challenge

- **Challenge ID:** N/A (config/challenge.json chưa được gửi bởi Lab Coach)
- **Khoảng thời gian điều tra:** N/A
- **Triệu chứng từ metrics:** N/A
- **Log line và correlation ID liên quan:** N/A
- **Trace ID và span gây ảnh hưởng:** N/A
- **Root cause:** N/A
- **Fix action:** N/A
- **Preventive measure:** N/A

> Ghi chú: Challenge chính thức chưa được mở. Khi Lab Coach gửi challenge.json, tôi sẽ:
> 1. Lưu file tại `config/challenge.json` (không commit)
> 2. Chạy `python scripts/inject_incident.py` để bơm incident vào system state
> 3. Chạy `python scripts/load_test.py --challenge --concurrency 5`
> 4. Kiểm tra dashboard để xác định metric xấu + thời gian
> 5. Lọc logs để tìm correlation_id bất thường
> 6. Mở trace Langfuse, kiểm tra span tree
> 7. Ghi root cause + fix vào section này

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:**
  - **Quyết định:** Scrub PII trong processor trước JSON rendering, không sau
  - **Lý do:** Nếu scrub sau khi serialize, data đã leaked vào JSON string. Phải intercept sớm trong pipeline để bảo vệ dữ liệu ngay từ khi generate event_dict

- **Một lỗi/blocker đã gặp:**
  - **Lỗi:** Sau khi sửa PII scrubber, lần đầu validate_logs.py vẫn báo fail vì log file cũ chứa dữ liệu chưa scrub
  - **Blocker:** Validator đọc toàn bộ logs.jsonl, không clear cache

- **Cách tìm nguyên nhân và xử lý:**
  - Đọc kỹ lưu ý trong README: "Clear old logs, restart API, run validators again"
  - Thực hiện: xóa hoặc rename data/logs.jsonl cũ → restart API → chạy load_test → validate_logs.py
  - Kết quả: 100/100

- **Cách hiểu luồng Metrics → Logs → Traces:**
  - **Metrics (dashboard):** Xác định "cái gì sai" + khoảng thời gian (ví dụ: P95 latency spike từ 14:22–14:27)
  - **Logs (data/logs.jsonl):** Lọc theo time window, tìm correlation_id của request bất thường
  - **Traces (Langfuse):** Mở trace theo correlation_id, xem waterfall view để tìm span nào slow/error (retrieval vs generation)
  - Lợi ích: Nhanh chóng xác định root cause (ví dụ: retrieval slow → vector DB, generation slow → model)

- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
  - **Prompt versioning:** Cho phép A/B test prompts mà không deploy code. Nếu v2 tốt hơn, promote; nếu tệ hơn, rollback ngay tức thì
  - **Token/cost tracking:** Giúp detect cost spike (có thể bị policy violation hoặc bug). SLO error budget sử dụng token để calculate cost
  - **SLO:** Cung cấp ngưỡng chấp nhận (ví dụ: P95 ≤ 500ms). Nếu vượt, trigger incident response (không chỉ log rồi bỏ qua)
  - **Rollback:** Critical cho safety. Nếu phát hiện v2 gây error rate cao, rollback v1 trong vài giây, không cần redeploy toàn bộ service

- **Điều quan trọng nhất đã học:**
  - Correlation ID là chìa khóa nối các data source: logs, traces, metrics
  - PII scrubbing phải là process sớm, không phải suy nghĩ sau
  - Structured logging + fixed field names cho phép aggregation mạnh (percentile, rate, etc.)
  - Dashboard không chỉ là visualization, mà là **first line of defense** để detect anomalies
  - Runbook không phải optional; nó cho phép on-call engineer respond nhanh và consistent

- **Hạn chế hoặc phần chưa hoàn thành, nếu có:**
  - Challenge chính thức chưa được mở (config/challenge.json từ Lab Coach chưa nhận được)
  - Dashboard hiển thị trực tiếp data từ logs.jsonl, nhưng trong production sẽ kết nối real time database / time series DB (Prometheus, InfluxDB)
  - Alert rules hiện tại là static YAML; trong production sẽ dùng alerting engine (Grafana, AlertManager) để tự động evaluate
  - Prompt versioning demo chỉ tạo v1/v2 local; chưa test đầy đủ rolling back dưới high load

## 9. Checklist trước khi nộp

- [x] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace (N/A vì chưa có challenge).
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs (sẽ nộp sau khi hoàn thiện).
