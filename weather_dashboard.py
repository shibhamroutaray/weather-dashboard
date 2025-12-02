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
from typing import Optional

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv


# ============================================================
# Utility Functions
# ============================================================

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")


def to_unit(temp_c: float, unit: str) -> float:
    """Convert Celsius temperature to Fahrenheit if needed."""
    return temp_c * 9 / 5 + 32 if unit == "°F" else temp_c


def fetch_current_weather(city: str, unit: str) -> Optional[dict]:
    """Fetch & return cleaned current weather data for a city."""
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"

    try:
        data = requests.get(url).json()
    except Exception:
        return None

    if data.get("cod") != 200:
        return None

    return {
        "city": city,
        "temp": to_unit(data["main"]["temp"], unit),
        "humidity": data["main"]["humidity"],
        "description": data["weather"][0]["description"],
        "icon": data["weather"][0]["icon"],
        "timestamp": datetime.fromtimestamp(data["dt"]),
        "lat": data["coord"]["lat"],
        "lon": data["coord"]["lon"],
    }


def fetch_forecast(city: str, unit: str) -> Optional[pd.DataFrame]:
    """Fetch cleaned 5-day forecast (3-hour intervals)."""
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"

    try:
        raw = requests.get(url).json()
    except Exception:
        return None

    if raw.get("cod") != "200":
        return None

    rows = []
    for entry in raw["list"]:
        ts = datetime.fromtimestamp(entry["dt"])
        rows.append({
            "timestamp": ts,
            "temperature": to_unit(entry["main"]["temp"], unit),
            "humidity": entry["main"]["humidity"],
            "description": entry["weather"][0]["description"],
            "wind_speed": entry["wind"]["speed"],
            "precip_prob": entry.get("pop", 0) * 100,
            "city": city,
        })

    df = pd.DataFrame(rows).set_index("timestamp")
    return df


# ============================================================
# Streamlit Config
# ============================================================

st.set_page_config(page_title="Weather Analytics Dashboard", layout="wide")
st.title("Weather Analytics Dashboard")

# Auto-refresh every 60 seconds
interval = 60
last_time = st.session_state.get("last_time", time.time())

if time.time() - last_time > interval:
    st.session_state["last_time"] = time.time()
    st.experimental_rerun()


# ============================================================
# Sidebar Controls
# ============================================================

SAVED = [
    "Bhubaneswar,OD,IN",
    "Bilaspur,CT,IN",
    "Delhi,DL,IN",
    "Kolkata,WB,IN",
    "Mumbai,MH,IN",
    "Chennai,TN,IN",
    "Bengaluru,KA,IN",
    "New York,US",
    "London,GB",
]

st.sidebar.header("City Selection")
st.sidebar.caption("Use a saved city or type your own.")

city1 = st.sidebar.selectbox("Primary City", SAVED)
custom1 = st.sidebar.text_input("Custom Primary City")
if custom1.strip():
    city1 = custom1.strip()

unit = st.sidebar.radio("Temperature Unit", ["°C", "°F"])

compare_mode = st.sidebar.checkbox("Compare with another city")

if compare_mode:
    city2 = st.sidebar.selectbox("Comparison City", SAVED, index=1)
    custom2 = st.sidebar.text_input("Custom Comparison City")
    if custom2.strip():
        city2 = custom2.strip()


# ============================================================
# Fetch Data
# ============================================================

current1 = fetch_current_weather(city1, unit)
if not current1:
    st.error(f"City '{city1}' not found.")
    st.stop()

forecast1 = fetch_forecast(city1, unit)
if forecast1 is None:
    st.error("Could not fetch forecast.")
    st.stop()

if compare_mode:
    current2 = fetch_current_weather(city2, unit)
    forecast2 = fetch_forecast(city2, unit)

    if not current2 or forecast2 is None:
        st.error(f"Comparison city '{city2}' not found.")
        st.stop()

    combined = pd.concat([forecast1, forecast2])
else:
    combined = forecast1.copy()


# ============================================================
# Current Weather Display
# ============================================================

def render_city(title: str, data: dict):
    """Small helper to display weather block."""
    st.write(f"### {title}")

    c1, c2 = st.columns(2)
    with c1:
        st.metric(f"Temperature ({unit})", f"{data['temp']:.2f}")
    with c2:
        st.metric("Humidity (%)", f"{data['humidity']:.2f}")

    c3, c4 = st.columns([1, 3])
    with c3:
        st.image(f"http://openweathermap.org/img/wn/{data['icon']}@2x.png", width=110)
    with c4:
        st.write(f"Condition: **{data['description'].title()}**")
        st.write(f"Updated: {data['timestamp']}")


if not compare_mode:
    st.subheader("Current Weather")
    render_city(city1, current1)
else:
    st.subheader("Current Weather — Comparison")
    colA, colB = st.columns(2)
    with colA:
        render_city(city1, current1)
    with colB:
        render_city(city2, current2)

st.markdown("---")


# ============================================================
# Charts (Comparison-aware)
# ============================================================

def line_chart(title, y_field, y_label):
    st.subheader(title)
    fig = px.line(
        combined,
        x=combined.index,
        y=y_field,
        color="city" if compare_mode else None,
        labels={y_field: y_label, "timestamp": "Time"},
    )
    st.plotly_chart(fig, use_container_width=True)


line_chart("Temperature Trend (Next 5 Days)", "temperature", f"Temperature ({unit})")
line_chart("Humidity Trend", "humidity", "Humidity (%)")
line_chart("Wind Speed Trend", "wind_speed", "Wind Speed (m/s)")
line_chart("Precipitation Probability", "precip_prob", "Rain Chance (%)")


# ============================================================
# Map Display
# ============================================================

st.subheader("City Locations")
if not compare_mode:
    map_df = pd.DataFrame({"lat": [current1["lat"]], "lon": [current1["lon"]]})
else:
    map_df = pd.DataFrame({
        "lat": [current1["lat"], current2["lat"]],
        "lon": [current1["lon"], current2["lon"]],
    })

st.map(map_df, zoom=6)


# Forecast Table (2-Decimal Formatting)


st.subheader("Forecast Data Table")

styled = combined.copy().style.format({
    "temperature": "{:.2f}",
    "humidity": "{:.2f}",
    "wind_speed": "{:.2f}",
    "precip_prob": "{:.2f}",
})

st.dataframe(styled)



# Insights


st.markdown("---")
st.subheader("5-Day Forecast Insights")

def insights(df: pd.DataFrame, label: str):
    st.write(f"### {label}")
    st.write(f"- **Avg Temperature**: {df['temperature'].mean():.2f} {unit}")
    st.write(f"- **Max Temperature**: {df['temperature'].max():.2f} {unit}")
    st.write(f"- **Min Temperature**: {df['temperature'].min():.2f} {unit}")
    st.write(f"- **Avg Wind Speed**: {df['wind_speed'].mean():.2f} m/s")
    st.write(f"- **Rainy Periods (>50%)**: {(df['precip_prob'] > 50).sum()} times")


if not compare_mode:
    insights(forecast1, f"{city1} — 5-Day Summary")
else:
    col1, col2 = st.columns(2)
    with col1:
        insights(forecast1, city1)
    with col2:
        insights(forecast2, city2)
