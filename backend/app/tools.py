import os
import requests
from datetime import datetime, timedelta


def get_weather(city: str) -> str:
    """Backward-compatible string weather output using structured data under the hood."""
    w = get_weather_json(city)
    if not w:
        raise ValueError("Unable to fetch weather")
    temp = w["temp"]
    feels = w.get("feels", temp)
    desc = w.get("condition", "weather")
    return f"{w['city']}: {temp}°C (feels {feels}°C), {desc}"


def search_city_candidates(query: str):
    """Return a canonical city name if the query matches a city via
    OpenWeather's Geo API; otherwise return None.

    This validates arbitrary inputs and supports global cities.
    """
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        return None

    q = (query or "").strip()
    if len(q) < 3:
        return None

    url = "https://api.openweathermap.org/geo/1.0/direct"
    params = {
        "q": q,
        "limit": 1,
        "appid": api_key,
    }

    try:
        r = requests.get(url, params=params, timeout=8)
    except Exception:
        return None

    if r.status_code != 200:
        return None

    try:
        data = r.json()
    except Exception:
        return None

    if not data:
        return None

    # Return the canonical city name from the first match
    name = data[0].get("name")
    return name if name else None
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


def get_coordinates(city: str):
    """Resolve a city to (lat, lon) using OpenWeather Geo API."""
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        return None
    url = "https://api.openweathermap.org/geo/1.0/direct"
    params = {"q": city, "limit": 1, "appid": api_key}
    try:
        r = requests.get(url, params=params, timeout=8)
    except Exception:
        return None
    if r.status_code != 200:
        return None
    try:
        data = r.json()
    except Exception:
        return None
    if not data:
        return None
    lat = data[0].get("lat")
    lon = data[0].get("lon")
    if lat is None or lon is None:
        return None
    return float(lat), float(lon)


def get_forecast(city: str):
    """Fetch 5-day/3-hour forecast blocks for a city.

    Returns { city, forecast: [ { dt_txt, temp, humidity, wind, wind_kmh, condition } ] }
    """
    coords = get_coordinates(city)
    if not coords:
        return None
    lat, lon = coords
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        return None
    params = {"lat": lat, "lon": lon, "appid": api_key, "units": "metric"}
    try:
        r = requests.get(FORECAST_URL, params=params, timeout=10)
    except Exception:
        return None
    if r.status_code != 200:
        return None
    try:
        data = r.json()
    except Exception:
        return None
    lst = data.get("list") or []
    forecast = []
    for entry in lst:
        try:
            dt_txt = entry["dt_txt"]
            temp = float(entry["main"]["temp"])
            humidity = int(entry["main"]["humidity"])
            wind_ms = float(entry["wind"]["speed"])
            cond = str(entry["weather"][0]["main"]).lower()
        except Exception:
            continue
        forecast.append({
            "dt_txt": dt_txt,
            "temp": temp,
            "humidity": humidity,
            "wind": round(wind_ms, 1),
            "wind_kmh": round(wind_ms * 3.6, 1),
            "condition": cond,
        })
    if not forecast:
        return None
    return {"city": city.title(), "forecast": forecast}


def summarize_forecast(city: str):
    """Compute simple averages and min/max over entire forecast window."""
    raw = get_forecast(city)
    if not raw:
        return {"error": f"Forecast unavailable for {city}"}
    temps = [x["temp"] for x in raw["forecast"]]
    hums = [x["humidity"] for x in raw["forecast"]]
    avg_temp = sum(temps) / len(temps)
    avg_hum = sum(hums) / len(hums)
    high = max(temps)
    low = min(temps)
    return {
        "city": raw["city"],
        "summary": f"Avg Temp: {avg_temp:.1f}°C, High: {high:.1f}°C, Low: {low:.1f}°C; Avg Humidity: {avg_hum:.0f}%",
        "data_points": len(raw["forecast"]),
        "raw": raw,
    }


def weekend_summary(city: str):
    """Summarize forecast for upcoming Saturday and Sunday blocks."""
    raw = get_forecast(city)
    if not raw:
        return {"error": f"Forecast unavailable for {city}"}
    weekend = []
    for x in raw["forecast"]:
        try:
            dt = datetime.strptime(x["dt_txt"], "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue
        if dt.weekday() in (5, 6):
            weekend.append(x)
    if not weekend:
        return {"city": raw["city"], "summary": "No weekend data in forecast window", "data_points": 0, "raw": {"forecast": []}}
    temps = [x["temp"] for x in weekend]
    hums = [x["humidity"] for x in weekend]
    avg_temp = sum(temps) / len(temps)
    avg_hum = sum(hums) / len(hums)
    high = max(temps)
    low = min(temps)
    return {
        "city": raw["city"],
        "summary": f"Weekend Avg Temp: {avg_temp:.1f}°C (High {high:.1f}°C / Low {low:.1f}°C), Avg Humidity {avg_hum:.0f}%",
        "data_points": len(weekend),
        "raw": {"forecast": weekend},
    }


def tomorrow_summary(city: str):
    """Summarize tomorrow's forecast around midday (12:00-15:00 slot if available)."""
    raw = get_forecast(city)
    if not raw:
        return {"error": f"Forecast unavailable for {city}"}
    tomorrow = (datetime.utcnow() + timedelta(days=1)).date()
    # pick nearest block to 12:00-15:00
    target_hours = {12, 15}
    candidates = []
    for x in raw["forecast"]:
        try:
            dt = datetime.strptime(x["dt_txt"], "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue
        if dt.date() == tomorrow:
            candidates.append((x, dt))
    if not candidates:
        return {"city": raw["city"], "summary": "No tomorrow data available", "data_points": 0, "raw": {"forecast": []}}
    # choose block with hour closest to 13:00
    best = min(candidates, key=lambda t: min(abs(t[1].hour - h) for h in target_hours))
    x = best[0]
    return {
        "city": raw["city"],
        "summary": f"Tomorrow near midday: {x['temp']:.1f}°C, {x['humidity']}% humidity, wind {x['wind_kmh']:.1f} km/h, {x['condition']}",
        "data_points": 1,
        "raw": {"forecast": [x]},
    }


def hourly_lookup(city: str, target_hour: int):
    """Find nearest forecast block to the requested hour within next ~36 hours."""
    raw = get_forecast(city)
    if not raw:
        return {"error": f"Forecast unavailable for {city}"}
    target_hour = max(0, min(23, int(target_hour)))
    # consider next 36 hours from now
    now = datetime.utcnow()
    limit = now + timedelta(hours=36)
    candidates = []
    for x in raw["forecast"]:
        try:
            dt = datetime.strptime(x["dt_txt"], "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue
        if now <= dt <= limit:
            candidates.append((x, dt))
    if not candidates:
        return {"city": raw["city"], "summary": "No near-term forecast block found", "data_points": 0, "raw": {"forecast": []}}
    best = min(candidates, key=lambda t: abs(t[1].hour - target_hour))
    x = best[0]
    return {
        "city": raw["city"],
        "summary": f"Around {best[1].strftime('%Y-%m-%d %H:%M')}: {x['temp']:.1f}°C, {x['humidity']}% humidity, wind {x['wind_kmh']:.1f} km/h, {x['condition']}",
        "data_points": 1,
        "raw": {"forecast": [x]},
    }


def get_weather_json(city: str):
    """Return structured weather for a city using OpenWeather current weather API.

    Output example:
    {
      "city": "Nagpur",
      "temp": 29.0,
      "feels": 30.5,
      "humidity": 80,
      "visibility": 6.0,  # km
      "wind": 3.0,        # m/s
      "wind_kmh": 10.8,   # km/h
      "condition": "mist"
    }
    """
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        return None

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric",
    }
    try:
        res = requests.get(url, params=params, timeout=10)
    except Exception:
        return None
    if res.status_code != 200:
        return None
    try:
        data = res.json()
    except Exception:
        return None

    try:
        temp = float(data["main"]["temp"])
        feels = float(data["main"].get("feels_like", temp))
        humidity = int(data["main"]["humidity"])
        visibility_m = float(data.get("visibility", 0))
        wind_ms = float(data.get("wind", {}).get("speed", 0.0))
        condition = str(data.get("weather", [{"main": "unknown"}])[0].get("main", "unknown")).lower()
    except Exception:
        return None

    return {
        "city": city.title(),
        "temp": temp,
        "feels": feels,
        "humidity": humidity,
        "visibility": round(visibility_m / 1000.0, 1),
        "wind": round(wind_ms, 1),
        "wind_kmh": round(wind_ms * 3.6, 1),
        "condition": condition,
    }


def score_city(w: dict) -> int:
    """Travel-friendly scoring (Option A):
    +1: temp in [20, 32]
    +1: humidity <= 65
    +1: wind (m/s) <= 8 (~28.8 km/h)
    """
    score = 0
    if 20 <= w.get("temp", 100) <= 32:
        score += 1
    if w.get("humidity", 101) <= 65:
        score += 1
    if w.get("wind", 100) <= 8:
        score += 1
    return score


def compare_weather(city1: str, city2: str):
    """Compare two cities and return winner and details.

    Returns dict with keys: winner, scores, city1_weather, city2_weather.
    """
    w1 = get_weather_json(city1)
    w2 = get_weather_json(city2)
    if not w1 or not w2:
        return {
            "winner": None,
            "scores": {},
            "city1_weather": w1,
            "city2_weather": w2,
            "error": "Weather unavailable to compare",
        }

    s1 = score_city(w1)
    s2 = score_city(w2)
    if s1 > s2:
        winner = w1["city"]
    elif s2 > s1:
        winner = w2["city"]
    else:
        winner = "Both equal"

    return {
        "winner": winner,
        "scores": {w1["city"]: s1, w2["city"]: s2},
        "city1_weather": w1,
        "city2_weather": w2,
    }
