# ROLLBACK + SHIFT POLICY

## Khuyến nghị traffic steps
- low risk: `5,25,50,100`
- conservative: `1,5,10,25,50,100`
- high velocity only when metrics mature: `10,50,100`

## Fail-safe rules
Rollback ngay nếu có một trong các tín hiệu:
- canary health endpoint fail
- preview API fail
- narration API fail
- job polling fail
- output audio không ffprobe được

## SLO gợi ý
- preview success >= 99%
- narration success >= 98%
- p95 preview latency không tăng > 30%
- p95 narration completion không tăng > 30%

## Khi nào không auto shift lên 100%
- output audio tạo được nhưng ffprobe lỗi
- worker nhận job nhưng không ra output_url
- audio preview pass nhưng narration fail
