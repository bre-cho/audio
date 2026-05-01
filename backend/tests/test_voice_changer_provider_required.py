import pytest
from app.audio_engines.voice_changer.rvc_adapter import RVCVoiceConversionAdapter


def test_rvc_adapter_scaffold_blocks_until_wired():
    with pytest.raises(NotImplementedError):
        RVCVoiceConversionAdapter().convert(input_path="x.wav", target_voice_id="v", output_path="out.wav")
