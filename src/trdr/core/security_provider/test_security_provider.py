import pytest
import asyncio


def test_get_security_list_returns_list_of_security_objects(security_provider_with_fake_data):
    security_list = asyncio.run(security_provider_with_fake_data.get_security_list())
    assert len(security_list) == len(security_provider_with_fake_data._bar_provider._data_cache.keys())


def test_get_security_returns_none_if_symbol_not_found(security_provider_with_fake_data):
    abcdefg_security = asyncio.run(security_provider_with_fake_data.get_security("ABCDEFG"))
    assert abcdefg_security is None
    amzn_security = asyncio.run(security_provider_with_fake_data.get_security("AMZN"))
    assert amzn_security is None


def test_get_security_returns_security_object_with_correct_length(security_provider_with_fake_data):
    security = asyncio.run(security_provider_with_fake_data.get_security("AAPL"))
    assert len(security.bars) == len(security_provider_with_fake_data._bar_provider._data_cache["AAPL"])


def test_get_security_raises_exception_if_other_exception_is_raised(security_provider_with_fake_data, monkeypatch):
    def raise_value_error(*args, **kwargs):
        raise ValueError("Simulated exception")

    monkeypatch.setattr(security_provider_with_fake_data._bar_provider, "get_bars", raise_value_error)

    with pytest.raises(ValueError):
        result = asyncio.run(security_provider_with_fake_data.get_security("AAPL"))
        assert result is None
