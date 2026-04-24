# Rollback Strategy

## Recommended
Use an explicit command, for example:
- Kubernetes: `helm rollback <release> <revision>`
- Compose: deploy previous image tag and restart services
- VM/PM2/systemd: switch symlink/release pointer to previous revision

## Guard rules
- Never rollback on a pre-deploy failure; just block
- Rollback only after deployment succeeded but post-deploy audio smoke failed
- Keep deploy and rollback idempotent
- Always collect logs/artifacts before returning failure

## Suggested rollback metadata
Persist:
- current revision
- previous stable revision
- release id
- deployment environment
- deployment timestamp
