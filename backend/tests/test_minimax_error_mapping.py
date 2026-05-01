import pytest

from app.providers.minimax_errors import (
    MinimaxAuthError,
    MinimaxDuplicateVoiceError,
    MinimaxInsufficientBalanceError,
    MinimaxInvalidInputError,
    MinimaxRateLimitError,
    raise_for_minimax_base_resp,
)


def test_success_base_resp_does_not_raise():
    raise_for_minimax_base_resp({"base_resp": {"status_code": 0}})


@pytest.mark.parametrize(
    "code,exc",
    [
        (1002, MinimaxRateLimitError),
        (1004, MinimaxAuthError),
        (1008, MinimaxInsufficientBalanceError),
        (2037, MinimaxInvalidInputError),
        (2039, MinimaxDuplicateVoiceError),
        (2049, MinimaxAuthError),
    ],
)
def test_known_error_codes(code, exc):
    with pytest.raises(exc):
        raise_for_minimax_base_resp({"base_resp": {"status_code": code, "status_msg": "err"}})
