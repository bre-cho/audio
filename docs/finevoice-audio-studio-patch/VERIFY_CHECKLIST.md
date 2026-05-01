# VERIFY CHECKLIST

## P0
- [ ] `internal_genvoice` blocked in production.
- [ ] Silent WAV rejected.
- [ ] Placeholder artifact cannot be promoted.
- [ ] Capability endpoint returns truthful status.

## P1
- [ ] Voice profile can be created/listed.
- [ ] Voice recipe validates style/emotion/language.
- [ ] Missing provider capability returns 409/422, not fake success.

## P2-P3
- [ ] Clone request requires consent.
- [ ] RVC upload validates file type.
- [ ] Voice changer returns QA metrics.

## P4-P6
- [ ] SFX/BGM/podcast routes create jobs or blocked capability response.
- [ ] STT exports JSON/SRT/VTT.
- [ ] Localization route does not claim success without provider.

## CI
- [ ] verify script exits non-zero on missing files.
- [ ] pytest covers quality gate and capability registry.
