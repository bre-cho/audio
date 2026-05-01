import pytest
from app.audio_engines.voice_changer.rvc_adapter import RVCVoiceConversionAdapter


def test_rvc_adapter_raises_when_not_configured():
    with pytest.raises(RuntimeError, match="rvc_not_configured"):
        RVCVoiceConversionAdapter().convert(input_path="x.wav", target_voice_id="v", output_path="out.wav")
