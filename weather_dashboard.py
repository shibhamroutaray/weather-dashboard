"""
Real-Time Weather Analytics Dashboard
-------------------------------------
A clean and readable Streamlit dashboard that fetches live weather
and forecast information using the OpenWeatherMap API.

Features:
- Temperature unit toggle (°C / °F)
- City comparison mode
- Wind + rain analytics
- Interactive charts
- Map visualization
- Auto-refresh every 60 seconds
"""

import os
import time
import requests
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv


# ============================================================
# Configuration & Utilities
# ============================================================

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")


def to_unit(temp_c: float, unit: str) -> float:
    """Convert temperature from Celsius to the selected unit."""
    return temp_c * 9 / 5 + 32 if unit == "°F" else temp_c


def fetch_current_weather(city: str, unit: str):
    """
    Fetch current weather for a city.
    Returns a dictionary of extracted fields, or None if invalid city.
    """
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"

    try:
        response = requests.get(url)
        data = response.json()
    except Exception:
        return None

    if data.get("cod") != 200:
        return None

    # Extract the fields we care about
    return {
        "temp": to_unit(data["main"]["temp"], unit),
        "humidity": data["main"]["humidity"],
        "description": data["weather"][0]["description"],
        "icon": data["weather"][0]["icon"],
        "timestamp": datetime.fromtimestamp(data["dt"]),
        "lat": data["coord"]["lat"],
        "lon": data["coord"]["lon"],
    }


def fetch_forecast(city: str, unit: str) -> pd.DataFrame | None:
    """
    Fetch 5-day forecast (3-hour intervals) and return a cleaned DataFrame.
    Returns None if city invalid.
    """
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"

    try:
        resp = requests.get(url)
        raw = resp.json()
    except Exception:
        return None

    if raw.get("cod") != "200":
        return None

    records = []
    for entry in raw["list"]:
        ts = datetime.fromtimestamp(entry["dt"])
        temp = to_unit(entry["main"]["temp"], unit)
        humidity = entry["main"]["humidity"]
        description = entry["weather"][0]["description"]
        wind = entry["wind"]["speed"]
        rain_chance = entry.get("pop", 0) * 100

        records.append([ts, temp, humidity, description, wind, rain_chance])

    df = pd.DataFrame(
        records,
        columns=["timestamp", "temperature", "humidity", "description", "wind_speed", "rain_chance"],
    ).set_index("timestamp")

    return df


# ============================================================
# Streamlit App Config
# ============================================================

st.set_page_config(page_title="Weather Dashboard", layout="wide")
st.title("Real-Time Weather Analytics Dashboard")

# Auto-refresh every 60s (simple + stable)
refresh_interval = 60
last_hit = st.session_state.get("last_hit", time.time())

if time.time() - last_hit > refresh_interval:
    st.session_state["last_hit"] = time.time()
    st.experimental_rerun()


# ============================================================
# Sidebar Controls
# ============================================================

SAVED_CITIES = [
    "Bhubaneswar,OD,IN",
    "Bilaspur,CG,IN",
    "Delhi,DL,IN",
    "Kolkata,WB,IN",
    "Mumbai,MH,IN",
    "Chennai,TN,IN",
    "Bengaluru,KA,IN",
    "New York,US",
    "London,GB",
]

st.sidebar.header("City Selection")
st.sidebar.caption("Choose from saved cities or enter your own.")

default_city = st.sidebar.selectbox("Saved Cities", SAVED_CITIES)
custom_city = st.sidebar.text_input("Custom City")
city = custom_city.strip() or default_city

unit = st.sidebar.radio("Temperature Unit", ["°C", "°F"])

compare_mode = st.sidebar.checkbox("Enable City Comparison")

if compare_mode:
    st.sidebar.subheader("Comparison City")
    default_city_2 = st.sidebar.selectbox("Saved Cities (City 2)", SAVED_CITIES, index=1)
    custom_city_2 = st.sidebar.text_input("Custom City (City 2)")
    city2 = custom_city_2.strip() or default_city_2


st.write(f"Showing weather for **{city}**")


# ============================================================
# Fetch Data
# ============================================================

current = fetch_current_weather(city, unit)
if not current:
    st.error("City not found. Please verify spelling.")
    st.stop()

if compare_mode:
    current2 = fetch_current_weather(city2, unit)
    if not current2:
        st.error("Comparison city not found.")
        st.stop()


# ============================================================
# Display Current Weather
# ============================================================

def render_city_block(title: str, data: dict):
    """Reusable display block for a city's current weather."""
    st.write(f"### {title}")

    col1, col2 = st.columns(2)
    with col1:
        st.metric(f"Temperature ({unit})", round(data["temp"], 1))
    with col2:
        st.metric("Humidity (%)", data["humidity"])

    col3, col4 = st.columns([1, 3])
    with col3:
        icon_url = f"http://openweathermap.org/img/wn/{data['icon']}@2x.png"
        st.image(icon_url, width=110)
    with col4:
        st.write(f"**Condition:** {data['description'].title()}")
        st.write(f"**Last Update:** {data['timestamp']}")


# Single city mode
if not compare_mode:
    st.subheader("Current Weather")
    render_city_block(city, current)

# Compare mode: side-by-side
else:
    st.subheader("City Comparison")
    c1, c2 = st.columns(2)
    with c1:
        render_city_block(city, current)
    with c2:
        render_city_block(city2, current2)


st.markdown("---")


# ============================================================
# Forecast Section
# ============================================================

forecast = fetch_forecast(city, unit)
if forecast is None:
    st.error("Unable to retrieve forecast data.")
    st.stop()

# Temperature chart
st.subheader("Temperature Trend (Next 5 Days)")
fig_temp = px.line(
    forecast,
    x=forecast.index,
    y="temperature",
    labels={"temperature": f"Temperature ({unit})", "timestamp": "Time"},
)
st.plotly_chart(fig_temp, use_container_width=True)

# Humidity chart
st.subheader("Humidity Trend")
fig_hum = px.line(forecast, x=forecast.index, y="humidity")
st.plotly_chart(fig_hum, use_container_width=True)

# Wind chart
st.subheader("Wind Speed Trend")
fig_wind = px.line(forecast, x=forecast.index, y="wind_speed")
st.plotly_chart(fig_wind, use_container_width=True)

# Rain chart
st.subheader("Rain Probability")
fig_rain = px.line(forecast, x=forecast.index, y="rain_chance")
st.plotly_chart(fig_rain, use_container_width=True)


# ============================================================
# Map
# ============================================================

st.subheader("City Location")

if not compare_mode:
    map_df = pd.DataFrame({"lat": [current["lat"]], "lon": [current["lon"]]})
else:
    map_df = pd.DataFrame(
        {
            "lat": [current["lat"], current2["lat"]],
            "lon": [current["lon"], current2["lon"]],
        }
    )

st.map(map_df, zoom=6)


# ============================================================
# Forecast Table + Insights
# ============================================================

st.subheader("Forecast Table")
st.dataframe(forecast)

st.markdown("---")
st.subheader("Quick Insights")

st.write(f"**Average Temperature:** {forecast['temperature'].mean():.2f} {unit}")
st.write(f"**Max Temperature:** {forecast['temperature'].max():.2f} {unit}")
st.write(f"**Min Temperature:** {forecast['temperature'].min():.2f} {unit}")

st.write(f"**Average Wind Speed:** {forecast['wind_speed'].mean():.2f} m/s")
rainy_count = (forecast["rain_chance"] > 50).sum()
st.write(f"**Rain Expected At:** {rainy_count} time periods")
