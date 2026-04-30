# FRONTEND PATCH GUIDE — VIETNAMESE UI + FEATURE READINESS

## Mục tiêu
Frontend phải hiển thị đúng trạng thái thật của backend: ready/partial/disabled/planned. Không quảng cáo feature chưa production-ready.

## 1. Sidebar/navigation cần có
- Tổng quan Audio Factory
- Text to Speech
- Voice Clone
- Voice Changer
- Voice Design
- Noise Reducer
- Voice Enhancer
- Sound Effects
- Podcast Generator
- Library/Artifacts
- Jobs/Workers
- Provider Health
- Quality Reports

## 2. Feature readiness badge
Mỗi feature hiển thị badge:
- `READY`: API + worker + provider thật + QA gate đủ.
- `PARTIAL`: có API/worker nhưng thiếu provider hoặc QA.
- `DISABLED`: provider/engine chưa production.
- `PLANNED`: chưa wired.

Nguồn dữ liệu: `/providers`, `/health`, `/audio/capabilities`.

## 3. Việt hóa mặc định
Tất cả text hiển thị mặc định tiếng Việt:
- Generate → Tạo giọng
- Clone Voice → Nhân bản giọng nói
- Voice Changer → Đổi giọng
- Noise Reduction → Lọc nhiễu
- Voice Enhancement → Nâng cấp giọng
- Sound Effects → Hiệu ứng âm thanh
- Podcast Generator → Tạo podcast
- Provider Health → Trạng thái nhà cung cấp
- Quality Report → Báo cáo chất lượng

## 4. Không cho submit feature disabled
Nếu backend trả `feature_status=disabled`, frontend disable button và hiện lý do.

## 5. Upload UX
Các module upload audio cần:
- validate file type: wav/mp3/m4a/flac
- validate max size
- show duration after upload
- show consent checkbox riêng cho voice clone
- show privacy warning cho clone voice

## 6. Artifact UI
Mỗi output cần hiển thị:
- waveform hoặc audio player
- provider
- generation mode
- quality report
- checksum
- download link
- job id
- promotion status
