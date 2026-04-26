# Dev Apply Guide

## Nguyên tắc apply

Không apply kiểu rời rạc. Mỗi patch phải đi qua:

```text
Code change
→ Contract update
→ Verify script update
→ CI check
→ Runtime smoke test
→ Report artifact
```

## Thứ tự làm việc khuyến nghị

### Sprint 1 — Verify hardening

Apply v40–v42.

Kết quả mong muốn:

- verify script không pass giả.
- report đầy đủ.
- E2E dừng đúng khi project create fail.
- JSON/API/file assertion hoạt động.

### Sprint 2 — Artifact safety

Apply v43–v49.

Kết quả mong muốn:

- artifact có contract.
- artifact trace/replay được.
- drift/determinism có budget.
- không ai bypass promotion gate.

### Sprint 3 — Regression & baseline

Apply v50–v60.

Kết quả mong muốn:

- có baseline registry.
- nightly replay.
- canary promotion.
- segment rollback.
- blast radius guard.

### Sprint 4 — Decision intelligence

Apply v61–v69.

Kết quả mong muốn:

- action được simulate trước.
- policy what-if chọn phương án tốt nhất.
- decision audit đầy đủ.
- policy học từ outcome.
- sandbox/tournament/mutation có kill-switch.

### Sprint 5 — Recovery & autonomous remediation

Apply v70–v76.

Kết quả mong muốn:

- last safe policy registry.
- recovery drill.
- SLO/error budget.
- runbook tự sinh và verify.
- remediation tự động nhưng có approval tier.

## Definition of Done

Patch chỉ được coi là DONE khi:

- `bash -n` pass.
- verify runtime pass.
- E2E pass.
- contract schema validate pass.
- report artifact sinh ra và không rỗng.
- failure case có `[FAIL]` rõ ràng.
- không có đường bypass gate.
