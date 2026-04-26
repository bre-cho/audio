# Audio Factory Patch Guide v40 → v76

Mục tiêu: gom toàn bộ patch từ **VERIFY REPORT APPEND SAFETY PATCH** đến **Multi-Stage Autonomous Approval Patch** thành một guide thống nhất để dev apply theo từng block nhưng không phá kiến trúc tổng thể.

## Core Law

```text
VERIFY không được pass giả.
Artifact không được promote nếu thiếu contract.
Baseline không được dùng nếu không có lifecycle.
Policy không được evolve nếu không có sandbox, tournament, governance.
Autonomous remediation không được chạy nếu vượt safe envelope.
```

## Kiến trúc tổng thể

```text
Verify Safety
→ Artifact Contract
→ Artifact Lineage / Replay / Drift
→ Promotion Governance
→ Continuous Regression
→ Baseline Registry / Lifecycle / Canary
→ Segment Rollback / Blast Radius / Simulation
→ Policy Decision / Audit / Learning
→ Sandbox / Tournament / Evolution
→ Kill-Switch / Last Safe Policy / Recovery Drill
→ Runbook / Self-Healing / Autonomous Remediation
→ Multi-Stage Approval
```

## Cách apply

1. Apply theo thứ tự trong `PATCH_ORDER.md`.
2. Mỗi block phải chạy checklist tương ứng trong `CHECKLIST.md`.
3. Contract phải khớp schema trong `schemas/`.
4. Không promote artifact/policy nếu verify gate fail.
5. Không bật autonomous remediation trước khi v69–v76 pass.

## Thư mục

```text
docs/audio-factory-patches/
  README.md
  PATCH_ORDER.md
  CHECKLIST.md
  CONTRACTS.md
  GOVERNANCE_FLOW.md
  DEV_APPLY_GUIDE.md
scripts/ci/examples/
  verify_audio_patch.example.sh
  verify_audio_e2e.example.sh
  verify_artifact_regression.example.sh
schemas/
  artifact_contract.schema.json
  baseline_contract.schema.json
  decision_contract.schema.json
  remediation_contract.schema.json
```
