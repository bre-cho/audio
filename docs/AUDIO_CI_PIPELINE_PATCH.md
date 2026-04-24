# AUDIO CI PIPELINE PATCH

## Mục tiêu
Thêm một pipeline riêng để bảo vệ audio layer mà không làm nặng toàn bộ matrix render/video.

## Cấu trúc
1. `verify_audio_patch.sh`
   - compile/import/audio-smoke tĩnh
   - phát hiện dấu vết hardcode/hotfix cũ
2. `verify_audio_e2e.sh`
   - spin stack
   - login nếu cần
   - tạo project + voice + upload sample
   - gọi preview + narration thật
   - poll job và ffprobe file cuối
3. `audio_fail_safe.sh`
   - gom log `api`, `worker`, `frontend`, `edge-relay`
   - snapshot `docker compose ps`
   - tạo summary artifact
4. Slack alert
   - chỉ gửi khi workflow chạy
   - payload chứa tail của 2 report + link tới run

## Fail-safe rules
- Bất cứ bước nào fail -> workflow vẫn thu artifact rồi mới teardown.
- Slack alert vẫn gửi ở nhánh `if: always()`.
- Artifact giúp debug ngay mà không cần rerun mù.

## Secrets
- `SLACK_WEBHOOK_URL`
- `AUDIO_E2E_EMAIL`
- `AUDIO_E2E_PASSWORD`

## Ghi chú
- Workflow này dùng `actions/setup-python@v6`; action này đã nâng runtime lên Node 24 và yêu cầu runner đủ mới. citeturn935406search3
- Upload artifact đang dùng `actions/upload-artifact@v4`, còn GitHub hiện đã có package phát hành 5.0.0; giữ `@v4` ở đây là lựa chọn bảo thủ để giảm rủi ro tương thích trong repo đang chạy ổn. citeturn935406search7
- Slack alert dùng `slackapi/slack-github-action` vì đây là action từ nhà phát triển Slack, hỗ trợ incoming webhook và payload file. citeturn935406search4
- Không nên dùng `8398a7/action-slack` cho phần mới vì action đó đã bị archive từ tháng 9/2025. citeturn935406search5
