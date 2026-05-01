# P1 — Provider Single Source Patch

Problem: multiple ElevenLabs/Minimax adapters exist and may behave differently.

Target architecture:

```txt
providers/provider_contract.py
providers/provider_registry_v4.py
providers/elevenlabs_provider_v4.py
providers/minimax_provider_v4.py
```

Hard rules:

```txt
1 provider = 1 adapter
all routes call registry.require(capability)
no fallback to internal_genvoice
no placeholder audio
no queued if capability is disabled
```
