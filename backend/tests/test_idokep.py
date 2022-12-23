import pytest

from backend.idokep import IdokepWeatherProvider
from backend.tests.tools import mock_fetch_url


@pytest.mark.asyncio
async def test_current():
    with mock_fetch_url("idokep_current.html"):
        provider = IdokepWeatherProvider()
        result = await provider.get_current("whatever")
    assert type(result.temperature) == int


@pytest.mark.asyncio
async def test_days():
    with mock_fetch_url("idokep_days.html"):
        provider = IdokepWeatherProvider()
        result = await provider.get_days("whatever")

    assert len(result) > 10
    assert result[0].temperature.min is not None
    assert result[0].temperature.max is not None
    assert result[0].day is not None
    assert 0


@pytest.mark.asyncio
async def test_hours():
    with mock_fetch_url("idokep_days.html"):
        provider = IdokepWeatherProvider()
        result = await provider.get_hours("whatever")

    assert len(result) > 10
    assert result[0].temperature is not None
    assert result[0].precipitation.probability is not None
    assert result[5].precipitation.probability is not None
