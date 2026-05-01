# 04 — API Contract: No Fake Queue

## Sai

```python
return {"status": "queued"}
```

khi route chưa tạo job thật hoặc chưa gọi worker thật.

## Đúng

```txt
409 capability_not_ready — provider/capability chưa ready
501 engine_not_implemented — capability ready nhưng service chưa implement
202 queued — đã tạo job thật trong DB/queue
200 completed — sync engine đã chạy và trả artifact thật
```

## Response mẫu

```json
{
  "error": "capability_not_ready",
  "capability": "bgm",
  "provider": "disabled",
  "status": "disabled",
  "reason": "BGM_PROVIDER_disabled"
}
```
