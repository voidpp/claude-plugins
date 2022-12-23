import logging
from datetime import date, timedelta
from urllib.parse import quote

from claude.components.exceptions import SelectorNotFoundInTree
from claude.components.fetcher import Fetcher
from claude.components.tools import parse_number, tree_search, tree_search_list
from claude.components.weather.plugin import WeatherProvider
from claude.components.weather.types import CurrentWeather, DayForecast, HourForecast

logger = logging.getLogger(__name__)

base_url = "https://www.idokep.hu"


class IdokepWeatherProvider(WeatherProvider):
    async def get_current(self, city: str) -> CurrentWeather:
        tree = await Fetcher.fetch_xml(f"{base_url}/idojaras/{quote(city)}")

        current_container = tree_search(".current-weather-lockup", tree)

        return CurrentWeather(
            image=base_url + tree_search(".current-weather-icon > img", current_container).attrib["src"],
            temperature=parse_number(tree_search(".current-temperature", current_container).text),
        )

    async def get_days(self, city: str) -> list[DayForecast]:
        tree = await Fetcher.fetch_xml(f"{base_url}/elorejelzes/{quote(city)}")

        day_columns = tree_search_list(".dailyForecastCol", tree)

        res = []

        col_date = None

        for day_column in day_columns:
            day_cell = tree_search(".dfColHeader .dfDayNum", day_column)
            if day_cell is None:
                continue

            precipitation_val = 0

            if rainlevel_container := tree_search_list(".rainlevel-container .mm", day_column, fail_on_not_found=False):
                precipitation_text = rainlevel_container[0].text
                if precipitation_text != ".":
                    precipitation_val = parse_number(precipitation_text)

            day = int(day_cell.text)

            [max, min] = [
                parse_number(element.text) for element in tree_search_list(".min-max-container a", day_column)
            ]

            if col_date is None:
                col_date = date.today()
                while col_date.day != day:
                    col_date = col_date + timedelta(days=1)

            day_data = {
                "image": base_url + tree_search(".forecast-icon", day_column).attrib["src"],
                "day": day,
                "date": str(col_date),
                "temperature": {
                    "min": min,
                    "max": max,
                },
                "precipitation": {
                    "value": precipitation_val,
                    "probability": None,
                },
            }
            res.append(DayForecast(**day_data))

            col_date = col_date + timedelta(days=1)

        return res

    async def get_hours(self, city: str) -> list[HourForecast]:
        tree = await Fetcher.fetch_xml(f"{base_url}/elorejelzes/{quote(city)}")

        hour_columns = tree_search_list(".new-hourly-forecast-card", tree)

        res = []

        for hour_column in hour_columns:

            precipitation_val = 0
            precipitation_prob = 0

            try:
                rain_chance = tree_search(".hourly-rain-chance > .interact", hour_column)
                precipitation_prob = parse_number(rain_chance.text)
            except SelectorNotFoundInTree:
                pass

            # TODO: wind

            hour_data = {
                "hour": int(tree_search(".new-hourly-forecast-hour", hour_column).text.split(":")[0]),
                "image": base_url + tree_search(".forecast-icon", hour_column).attrib["src"],
                "temperature": parse_number(tree_search(".tempValue > a", hour_column).text),
                "precipitation": {
                    "value": precipitation_val,
                    "probability": precipitation_prob,
                },
            }

            res.append(HourForecast(**hour_data))

        return res
