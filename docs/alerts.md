# Alert Runbooks — Chat API Monitoring

> Procedures để detect, investigate, mitigate và prevent mỗi alert

---

## 1. High P95 Latency Warning

**Alert condition:** P95 latency > 800ms cho 5+ phút

### 🔍 Detection
- Dashboard panel "Latency percentiles and TTFT" cho thấy P95 spike từ ~150ms → >800ms
- Slack alert đến `#alerts-chat-api`

### 📊 Investigation (Metrics → Logs → Traces)

**Step 1: Metrics**
1. Mở dashboard latency panel
2. Xác định time window (ví dụ: 14:22–14:27)
3. Kiểm tra P95 vs P50/P99 – nếu P50 normal nhưng P95 cao = tail latency issue

**Step 2: Logs** 
1. Filter `data/logs.jsonl` cho time window:
   ```bash
   grep "2026-09-29T14:2[2-7]" data/logs.jsonl | grep "latency_ms" | sort -t':' -k7
   ```
2. Tìm requests với `latency_ms > 1000`
3. Extract `correlation_id` từ slow request

**Step 3: Traces**
1. Vào Langfuse project
2. Search trace by `correlation_id`
3. Mở waterfall view
4. Kiểm tra 3 spans:
   - `retrieve` (expected: ~100ms) → slow?
   - `llm_generation` (expected: ~150ms) → slow?
   - Root (expected: ~200ms total)

### 🛠️ Mitigation (Temporary Fix)

**If retrieval is slow (>500ms):**
```bash
# Restart search backend
systemctl restart elasticsearch

# Or reduce retrieval timeout
# In app/mock_rag.py, reduce sleep from 2.5s to 1s
```

**If LLM is slow (>300ms):**
```bash
# Check model load – may need to increase replicas
kubectl scale deployment llm-server --replicas=3

# Or reduce batch size in inference config
```

**If middleware overhead:**
```bash
# Check if correlation_id binding is slow
# Profile with: python -m cProfile scripts/load_test.py
```

### 🛡️ Prevention (Long-term Fix)

1. **Add caching:** Cache retrieval results for 1 hour
2. **Optimize retrieval query:** Use BM25 over dense retrieval
3. **Monitor LLM latency separately:** Add TTFT alert to catch slowness early
4. **Load test regularly:** Weekly load test to catch regression
5. **Set retrieval timeout:** In app/mock_rag.py, add timeout=1s to prevent cascade

---

## 2. Elevated Error Rate - Critical

**Alert condition:** Error rate > 5% cho 2+ phút

### 🔍 Detection
- Dashboard "Error rate and retrieval success" spike
- Slack critical alert đến `#alerts-critical`
- PagerDuty incident created

### 📊 Investigation (Metrics → Logs → Traces)

**Step 1: Metrics**
1. Dashboard "Errors" panel show error count + breakdown
2. Kiểm tra `error_breakdown` từ `/metrics` endpoint:
   ```bash
   curl http://localhost:8000/metrics | jq .error_breakdown
   ```
3. Xác định error type (TypeError, RuntimeError, etc.)

**Step 2: Logs**
1. Filter errors từ time window:
   ```bash
   grep "2026-09-29T14:2[2-7]" data/logs.jsonl | grep "request_failed"
   ```
2. Extract error_type + correlation_id:
   ```bash
   jq -r 'select(.event=="request_failed") | 
           "\(.correlation_id) | \(.error_type) | \(.payload.detail)"' data/logs.jsonl
   ```

**Step 3: Traces**
1. Vào Langfuse, filter traces by status=error
2. Kiểm tra error message trong span metadata
3. Nếu retrieval error → vector DB down
4. Nếu LLM error → model crash

### 🛠️ Mitigation

**If tool_fail error (retrieval):**
```bash
# Check vector DB connectivity
curl -X GET http://elasticsearch:9200/_cluster/health

# Restart if needed
docker restart elasticsearch
```

**If TypeError (middleware):**
```bash
# Check logs for exact error
tail -100 /var/log/app.log | grep TypeError

# Restart API server
systemctl restart api
```

**If token limit exceeded:**
```bash
# Check if prompt is too long
grep "tokens_in" data/logs.jsonl | sort -rn | head -1

# Truncate prompt in app/prompt_management.py
```

### 🛡️ Prevention

1. **Add retrieval circuit breaker:** Fail fast if DB down
2. **Implement retry logic:** Exponential backoff for transient errors
3. **Monitor dependencies:** Add health checks for ES/DB
4. **Error budget tracking:** Re-check error_budget after incident
5. **Incident post-mortem:** Document root cause in git commit

---

## 3. Retrieval Success Rate Drop

**Alert condition:** Retrieval success < 90% cho 5+ phút

### 🔍 Detection
- Dashboard "Retrieval success rate" panel drops from 95% → 85%
- Slack alert đến `#search-alerts`

### 📊 Investigation

**Step 1: Metrics**
1. Dashboard show retrieval success rate by time
2. Kiểm tra `tool_success=false` count:
   ```bash
   grep "tool_success.*false" data/logs.jsonl | wc -l
   ```

**Step 2: Logs**
1. Filter retrieval failures:
   ```bash
   jq 'select(.tool_success==false and .tool_name=="retrieval")' data/logs.jsonl
   ```
2. Kiểm tra payload để xem reason (ví dụ: "Vector store timeout")

**Step 3: Traces**
1. Mở trace của failed request
2. Kiểm tra `retrieve` span status
3. Span error message: "RuntimeError: Vector store timeout"?

### 🛠️ Mitigation

**If retrieval timeout:**
```bash
# Increase retrieval timeout
# In app/mock_rag.py, change sleep/timeout

# Or offload to async worker
# Add queue-based retrieval with timeout=5s
```

**If vector DB connection issue:**
```bash
# Test connectivity
python -c "from elasticsearch import Elasticsearch; \
           es = Elasticsearch(['localhost:9200']); \
           print(es.ping())"

# Check indices exist
curl -X GET http://localhost:9200/_cat/indices
```

### 🛡️ Prevention

1. **Add fallback documents:** If retrieval fails, use generic docs
2. **Implement retrieval SLO separately:** Alert at 95% threshold
3. **Monitor ES health:** Add cluster health check
4. **Async retrieval:** Use background job if sync timeout
5. **Query optimization:** Index optimization to reduce query time

---

## Summary Table

| Alert | Metric | Threshold | Duration | Severity | Team |
|---|---|---|---|---|---|
| High P95 Latency | p95_latency_ms | >800 | 5m | warning | on-call |
| Elevated Errors | error_rate_% | >5 | 2m | critical | on-call |
| Retrieval Drop | success_rate_% | <90 | 5m | warning | search-team |

---

## Escalation Path

1. **Warning (5 min):** Slack alert → Check dashboard
2. **Critical (2 min):** Slack @channel + PagerDuty → Run mitigation immediately
3. **SLO Breach:** Post-mortem within 24 hours → Fix + Prevention

---

## Testing Alerts

```bash
# Simulate high latency
python scripts/load_test.py --scenario slow_retrieval

# Simulate retrieval failure
python scripts/load_test.py --scenario tool_fail

# Simulate cost spike
python scripts/load_test.py --scenario cost_spike

# Validate alerts triggered
grep "ERROR\|WARNING" /var/log/app.log
```
