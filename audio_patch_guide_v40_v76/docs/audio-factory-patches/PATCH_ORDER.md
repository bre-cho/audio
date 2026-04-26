# Patch Order v40 → v76

## Block A — Verify Safety Layer

- **v40 — Verify Report Append Safety Patch**
  - `>` → `>>` để không ghi đè report.
  - `SEARCH_PATHS` guard để grep không chết khi thiếu folder.
  - `PROJECT_ID` guard để E2E không chạy tiếp bằng project_id rỗng/null.

- **v41 — Verify Exit Code Integrity Patch**
  - `set -euo pipefail`
  - `IFS=$'\n\t'`
  - `trap ERR`
  - wrapper `run()`
  - cấm `|| true` không có lý do.
  - guard pipeline/subshell/curl/jq.

- **v42 — Verify Assertion Layer Patch**
  - assert JSON key.
  - assert HTTP 2xx.
  - assert file/dir/report tồn tại.
  - assert project/preview state.
  - mini test runner.

## Block B — Artifact Contract & Traceability

- **v43 — Verify Artifact Contract Patch**
  - artifact phải có `artifact_id`, `artifact_type`, `path/url`, `mime_type`, `size_bytes`, `checksum`, `created_at`, `source_job_id`.
  - size > 0.
  - file size khớp contract.
  - checksum khớp.

- **v44 — Verify Artifact Lineage Patch**
  - artifact phải truy ngược được project/job/scene/preview/render.
  - cần `input_hash`, `provider`, `template_version`, `parent_artifact_id optional`.

- **v45 — Verify Artifact Replayability Patch**
  - artifact phải dry-run replay được từ source job/input/config/template/runtime.

- **v46 — Verify Artifact Determinism Patch**
  - same input/config/template/runtime/seed → same checksum hoặc declared nondeterministic.

- **v47 — Verify Artifact Drift Budget Patch**
  - duration/loudness/transcript/checksum drift phải trong budget.

- **v48 — Verify Artifact Promotion Gate Patch**
  - chỉ promote nếu pass đủ: contract, lineage, replayability, determinism, drift budget.

- **v49 — Verify Promotion Authority & Bypass Guard Patch**
  - chỉ đúng actor/role/source được promote.
  - chặn promoted khi bất kỳ gate nào false/missing.
  - promotion hash immutable.

## Block C — Continuous Regression & Baseline

- **v50 — Verify Continuous Regression Guard Patch**
  - nightly replay.
  - detect drift/provider/runtime/model change.
  - auto incident + freeze promotion.

- **v51 — Regression Baseline Registry Patch**
  - baseline registry: golden/canary/regression.
  - owner, approved_by, replay_schedule, drift_budget_policy, status.

- **v52 — Baseline Lifecycle Policy Patch**
  - candidate → active → deprecated → frozen → archived.
  - không skip/revert nếu không có audit.

- **v53 — Baseline Replacement & Rollback Patch**
  - baseline mới thay cũ phải có previous/rollback baseline.
  - candidate fail thì freeze và rollback.

- **v54 — Baseline Canary Promotion Patch**
  - candidate → canary_active → active.
  - traffic percentage, canary window, control baseline, rollback baseline.

- **v55 — Baseline Canary Auto-Rollback Patch**
  - canary fail → freeze candidate → restore control → incident → block promotion.

- **v56 — Canary Confidence Scoring Patch**
  - score ≥90 promote, 70–89 extend, <70 rollback.

- **v57 — Canary Sample Size & Statistical Guard Patch**
  - confidence score chỉ hợp lệ khi đủ sample/duration/replay/success count.

- **v58 — Canary Segment Coverage Patch**
  - sample phải phủ provider/template/runtime/duration/language/voice/project_type.

- **v59 — Segment-Specific Rollback Patch**
  - lỗi segment nào rollback/freeze/fallback segment đó nếu không critical.

- **v60 — Segment Blast Radius Guard Patch**
  - trước rollback/fallback phải tính affected projects/jobs/artifacts/users/publish queue.

## Block D — Simulation, Policy, Decision & Learning

- **v61 — Preemptive Risk Simulation Patch**
  - simulate action trước khi apply.
  - predicted impact/error/latency/success/confidence.

- **v62 — Policy Simulation & What-If Engine Patch**
  - so sánh nhiều scenario: rollback/fallback/freeze/delay/promote.
  - chọn decision_score tốt nhất.

- **v63 — Decision Record & Policy Audit Patch**
  - mọi decision phải có scenarios, selected action, rejected actions, score breakdown, reason, actor, outcome tracking.

- **v64 — Decision Feedback Learning Patch**
  - compare predicted vs actual.
  - update policy weights theo accuracy.
  - accuracy <50 thì freeze policy + incident.

- **v65 — Policy Learning Sandbox Patch**
  - policy candidate phải replay historical/mixed/synthetic dataset.
  - compare old vs new.
  - safety_score gate.

- **v66 — Multi-Policy Tournament Patch**
  - nhiều policy thi trên cùng scenario set.
  - chọn winner nếu score và guardrail pass.

- **v67 — Policy Diversity & Anti-Convergence Patch**
  - chống policy duplicate/local optimum.
  - enforce exploration/exploitation ratio.

- **v68 — Evolution Strategy Mutation Engine Patch**
  - tự sinh policy đời sau bằng minor/major/crossover mutation.

- **v69 — Evolution Governance & Kill-Switch Patch**
  - mutation limit, policy delta limit, runaway detector, kill-switch, rollback last safe.

## Block E — Recovery, Runbook, Autonomous Remediation

- **v70 — Last Safe Policy Registry Patch**
  - rollback về policy đã chứng minh an toàn, không rollback mù.

- **v71 — Safe Policy Recovery Drill Patch**
  - diễn tập kill-switch/rollback định kỳ.

- **v72 — Recovery SLO & Error Budget Patch**
  - recovery time, rollback success rate, failed drills/month.

- **v73 — Recovery Runbook Auto-Generation Patch**
  - drill/rollback fail → sinh runbook có root cause hint, fix, owner, verification command.

- **v74 — Runbook Execution Verification Patch**
  - runbook phải execute + verify + recheck SLO + regression.

- **v75 — Autonomous Remediation Engine Patch**
  - tự sửa end-to-end trong safe envelope.
  - risk low, blast radius low, confidence ≥90, runbook verified.

- **v76 — Multi-Stage Autonomous Approval Patch**
  - Tier 0 auto approve.
  - Tier 1 delayed auto approve.
  - Tier 2 human approval.
  - Tier 3 blocked.
