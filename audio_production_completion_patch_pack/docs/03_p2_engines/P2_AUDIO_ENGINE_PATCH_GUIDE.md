# P2 AUDIO ENGINE PATCH GUIDE — FULL AI AUDIO PLATFORM

## Mục tiêu
Bổ sung engine thật cho Voice Design, Voice Changer, Sound Effect, Podcast, Enhancer, Noise Reducer.

## P2.1 — Engine folder chuẩn

Thêm thư mục:
```text
backend/app/audio_engines/
  __init__.py
  voice_design/
  voice_changer/
  sound_effects/
  podcast/
  enhancer/
  noise_reducer/
  quality/
```

## P2.2 — Voice Design Engine

### File thêm
`backend/app/audio_engines/voice_design/recipe_engine.py`

Input:
- gender/tone/age/accent/energy/emotion/speed
- brand personality
- forbidden traits

Output:
- `voice_recipe.json`
- provider prompt
- preview text
- QA checklist

Acceptance:
- Có recipe version.
- Có prompt audit.
- Có provider capability check.

## P2.3 — Voice Changer Engine

### File thêm
`backend/app/audio_engines/voice_changer/conversion_engine.py`

Hai mode:
1. `safe_pitch_mode`: pitch/formant-preserving DSP.
2. `model_conversion_mode`: provider/model voice conversion.

Metadata bắt buộc:
- source_voice_hash
- target_voice_id
- conversion_strength
- similarity_score
- artifact lineage

Không được gọi pitch shift thô là voice cloning/voice conversion production.

## P2.4 — Noise Reducer Engine

### File thêm
`backend/app/audio_engines/noise_reducer/noise_pipeline.py`

Pipeline đề xuất:
1. Input validation.
2. Convert to mono/stereo working WAV.
3. Voice activity detection.
4. Noise profile estimation.
5. Spectral gate hoặc RNNoise.
6. Optional Demucs separation.
7. Loudness normalize.
8. Export + QA.

Quality report:
- estimated_snr_before
- estimated_snr_after
- noise_reduction_db
- speech_preservation_score
- clipping_detected

## P2.5 — Voice Enhancer Engine

### File thêm
`backend/app/audio_engines/enhancer/enhancement_pipeline.py`

Chain:
- de-click
- de-ess
- EQ preset
- compressor
- limiter
- LUFS normalization
- breath control optional

Target presets:
- podcast_voice
- youtube_narration
- audiobook
- phone_recording_cleanup
- studio_voice

## P2.6 — Sound Effect Engine

### File thêm
`backend/app/audio_engines/sound_effects/sfx_engine.py`

Contract:
- prompt
- duration_sec
- style
- negative_prompt
- loopable
- output_format

Provider adapter:
- ElevenLabs SFX nếu available
- fallback disabled nếu không có provider thật

## P2.7 — Podcast Generator Engine

### File thêm
`backend/app/audio_engines/podcast/podcast_mixer.py`

Flow:
1. Script parse thành segments.
2. Speaker registry.
3. TTS từng speaker.
4. Insert intro/outro/stinger.
5. BGM ducking.
6. Segment concat.
7. LUFS normalize.
8. Chapter/timeline export.
9. Transcript alignment.

Artifacts:
- final_mix.wav/mp3
- stems per speaker
- transcript.srt
- timeline.json
- chapter_markers.json
- quality_report.json

## P2.8 — Audio Quality Engine

### File thêm
`backend/app/audio_engines/quality/audio_quality_report.py`

Metrics:
- duration_ms
- rms
- peak
- clipping_count
- lufs_integrated
- silence_ratio
- snr_estimate
- sample_rate
- channels
- bit_depth
- transcript_similarity if transcript available

Promotion gate:
- no clipping above threshold
- non-silent
- min duration
- LUFS in target range
- checksum exists

## P2.9 — API routes cần thêm

```text
backend/app/api/voice_design.py
backend/app/api/voice_changer.py
backend/app/api/noise_reducer.py
backend/app/api/voice_enhancer.py
backend/app/api/sound_effects.py
backend/app/api/podcast.py
backend/app/api/audio_quality.py
```

## P2.10 — Acceptance checklist

- [ ] Mỗi engine có API + service + worker + DB model + artifact contract.
- [ ] Mỗi output có quality report.
- [ ] Feature chưa có provider thật phải disabled rõ.
- [ ] Podcast export đủ final mix + transcript + timeline.
- [ ] Noise reducer/enhancer có before/after metrics.
