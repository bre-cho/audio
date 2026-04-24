# AUDIO CANARY DEPLOY PATCH

## Mục tiêu
Thêm 1 lane deploy an toàn cho audio pipeline mà không phá `full-stack-e2e.yml` hay deploy flow hiện có.

## Flow
1. Audio CI gate phải xanh.
2. Lấy stable revision hiện tại.
3. Deploy revision mới dưới dạng canary.
4. Smoke test audio trên canary URL.
5. Shift traffic tăng dần: 5 -> 25 -> 50 -> 100.
6. Mỗi nấc đều chạy lại audio smoke.
7. Fail ở bất kỳ nấc nào -> rollback ngay.

## Patch tối thiểu vào workflow deploy hiện có
```yaml
needs: [audio-ci-e2e]
```

```yaml
- name: Canary deploy guard
  run: bash scripts/deploy/canary_deploy.sh deploy
```

```yaml
- name: Canary smoke
  run: bash scripts/deploy/post_canary_audio_smoke.sh smoke
```

```yaml
- name: Progressive shift
  run: bash scripts/deploy/audio_shift_traffic.sh 5,25,50,100
```

```yaml
- name: Rollback on canary failure
  if: failure()
  run: bash scripts/deploy/rollback_canary.sh
```

## Mapping lệnh thật
### Cloud Run ví dụ
- `FETCH_STABLE_COMMAND`: đọc revision đang nhận 100% traffic
- `CANARY_DEPLOY_COMMAND`: `gcloud run deploy ... --no-traffic`
- `SHIFT_TRAFFIC_COMMAND`: `gcloud run services update-traffic ...`
- `ROLLBACK_COMMAND`: chuyển traffic về stable revision

### ECS/ALB ví dụ
- `FETCH_STABLE_COMMAND`: đọc target group stable
- `CANARY_DEPLOY_COMMAND`: create new task set
- `SHIFT_TRAFFIC_COMMAND`: đổi weighted routing
- `ROLLBACK_COMMAND`: scale down canary task set, restore weight stable
