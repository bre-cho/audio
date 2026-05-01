def test_minimax_provider_has_required_methods():
    from app.providers.minimax_provider import MinimaxProvider

    required = [
        "health_check",
        "synthesize_speech",
        "create_async_tts_task",
        "query_async_tts_task",
        "upload_voice_clone_audio",
        "upload_prompt_audio",
        "clone_voice",
        "design_voice",
        "list_voices",
        "delete_voice",
        "require_capability",
    ]
    for name in required:
        assert hasattr(MinimaxProvider, name), name


def test_minimax_models_importable():
    from app.providers.minimax_models import MinimaxCloneRequest, MinimaxTTSRequest

    assert MinimaxTTSRequest(text="hi", voice_id="v").model
    assert MinimaxCloneRequest(voice_id="v", clone_file_id="f").voice_id == "v"
