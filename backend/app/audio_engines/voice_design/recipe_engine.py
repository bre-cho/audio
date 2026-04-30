from __future__ import annotations


def build_voice_recipe(*, profile: dict) -> dict:
    """Builds a deterministic voice recipe payload for provider prompts."""
    return {
        "recipe_version": "v1",
        "profile": profile,
        "provider_prompt": "Voice design pipeline is not wired yet",
        "preview_text": "",
        "qa_checklist": ["provider_capability_check_pending"],
        "status": "planned",
    }
