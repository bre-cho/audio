# MODULE GAP MATRIX

| Module | Current repo risk | Patch target | Production gate |
|---|---|---|---|
| TTS | Provider exists but fallback/silent risk | Real provider only in prod | provider_ready + qa_pass |
| Voice Clone | Consent exists, provider clone incomplete | Instant/pro clone/RVC upload | consent + provider_clone_ready |
| Voice Changer | Pitch shift thô | Model-based conversion scaffold | similarity/naturalness QA |
| Voice Design | Missing voice recipe | Voice recipe + library | recipe_valid + capability_ready |
| SFX | Simple effects only | Prompt-to-SFX scaffold | artifact QA |
| BGM | Missing dedicated engine | BGM generate + loop/mix | loudness + duration QA |
| Podcast | Partial | Multi-speaker timeline/mixdown | per-speaker artifacts QA |
| Noise Reducer | Missing real DSP/model | RNNoise/Demucs hook | SNR improvement QA |
| Enhancer | Missing full chain | de-click/de-ess/EQ/compress | loudness/clipping QA |
| STT/Subtitles | Missing or partial | transcript + SRT/VTT | segment timing QA |
| Translation | Missing | voice translate scaffold | source/target QA |
