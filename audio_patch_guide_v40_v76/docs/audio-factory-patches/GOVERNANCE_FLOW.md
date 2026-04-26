# Governance Flow

## Artifact Promotion Flow

```text
artifact created
→ contract check
→ lineage check
→ replayability check
→ determinism check
→ drift budget check
→ promotion gate
→ authority check
→ bypass guard
→ immutable promotion hash
→ promoted
```

## Baseline Flow

```text
candidate
→ canary_active
→ active
→ deprecated
→ archived
```

Failure path:

```text
candidate/canary fail
→ freeze candidate
→ rollback control baseline
→ create incident
→ block promotion
```

## Policy Evolution Flow

```text
decision feedback
→ policy candidate
→ sandbox replay
→ tournament
→ diversity filter
→ mutation
→ governance guard
→ canary
→ promote
```

Kill-switch path:

```text
runaway risk / safety score fail
→ freeze evolution
→ reject candidates
→ rollback last safe policy
→ open incident
→ manual approval required to resume
```

## Recovery & Self-Healing Flow

```text
SLO breach / regression / incident
→ generate runbook
→ verify runbook
→ simulate fix
→ policy what-if
→ blast radius guard
→ approval tier
→ execute
→ verify
→ recheck SLO
→ close incident or rollback
```

## Approval Tier

| Tier | Điều kiện | Action |
|---|---|---|
| Tier 0 | risk low, confidence ≥90, blast radius low | auto approve |
| Tier 1 | risk medium, confidence ≥85 | cooldown + monitor |
| Tier 2 | risk high hoặc blast radius high | human approval |
| Tier 3 | critical risk hoặc kill_switch=true | blocked |
