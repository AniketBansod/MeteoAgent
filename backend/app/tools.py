import os
import requests


def get_weather(city: str) -> str:
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        raise ValueError("WEATHER_API_KEY not configured")

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"
    }

    res = requests.get(url, params=params, timeout=10)

    if res.status_code != 200:
        raise ValueError(f"Weather API error: {res.status_code} - {res.text}")

    data = res.json()

    temp = data["main"]["temp"]
    desc = data["weather"][0]["description"]

    return f"{city}: {temp}°C, {desc}"
