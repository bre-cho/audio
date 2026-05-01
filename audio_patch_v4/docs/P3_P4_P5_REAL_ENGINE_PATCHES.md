# P3/P4/P5 — Real Engine Patches

## Voice Changer
Required:
- RVC/OpenVoice runtime config
- input artifact lookup
- output artifact persistence
- speaker similarity score
- naturalness score
- artifact score

## SFX/BGM
Required:
- real provider endpoint
- duration validation
- commercial-use/license metadata
- loopable flag
- seed/model metadata

## Podcast
Required full flow:

```txt
script → segment → speaker casting → TTS per segment → timeline → BGM ducking → LUFS normalize → final MP3/WAV → SRT/VTT → artifact
```
