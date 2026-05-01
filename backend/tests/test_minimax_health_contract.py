from types import SimpleNamespace

from app.services.minimax_capability_service import get_minimax_capabilities


def test_no_key_blocks_all_minimax_capabilities():
    settings = SimpleNamespace(minimax_api_key=None)
    states = get_minimax_capabilities(settings)
    assert states
    assert all(s.status == "blocked" for s in states)
    assert all(s.reason == "missing_api_key" for s in states)
