import os
import time
import requests
import pandas as pd
import streamlit as st

from datetime import datetime
from dotenv import load_dotenv

# load env first
load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

# ------------ helpers -------------------

def c_to_f(c, unit):
    # quick convert
    if unit == "°F":
        return (c * 9/5) + 32
    return c


def get_current(city, unit):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"

    try:
        r = requests.get(url).json()
    except:
        return None

    if r.get("cod") != 200:
        return None
    
    main = r["main"]
    w = r["weather"][0]

    return {
        "city": city,
        "temp": c_to_f(main["temp"], unit),
        "humidity": main["humidity"],
        "desc": w["description"],
        "icon": w["icon"],
        "time": datetime.fromtimestamp(r["dt"]),
        "lat": r["coord"]["lat"],
        "lon": r["coord"]["lon"]
    }


def get_forecast(city, unit):
    # no fancy error handling
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
    try:
        raw = requests.get(url).json()
    except:
        return None

    if raw.get("cod") != "200":
        return None

    rows = []
    for item in raw["list"]:
        ts = datetime.fromtimestamp(item["dt"])
        rows.append({
            "timestamp": ts,
            "temperature": c_to_f(item["main"]["temp"], unit),
            "humidity": item["main"]["humidity"],
            "desc": item["weather"][0]["description"],
            "wind": item["wind"]["speed"],
            "rain_prob": item.get("pop", 0) * 100,
            "city": city
        })
    
    df = pd.DataFrame(rows)
    df = df.set_index("timestamp")
    return df


# ------------ page setup ---------------

st.set_page_config(page_title="Weather Dashboard", layout="wide")
st.title("Weather Analytics Dashboard ")

# auto refresh
if "t0" not in st.session_state:
    st.session_state["t0"] = time.time()

if time.time() - st.session_state["t0"] > 60:
    st.session_state["t0"] = time.time()
    st.experimental_rerun()

# ----------- sidebar --------------------

saved = [
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

st.sidebar.write("City Settings (quick pick or type your own)")

city = st.sidebar.selectbox("City", saved)
cust = st.sidebar.text_input("Custom City")
if cust.strip():
    city = cust.strip()

unit = st.sidebar.radio("Temp Unit", ["°C", "°F"])

compare = st.sidebar.checkbox("Compare w/ another city")

if compare:
    city2 = st.sidebar.selectbox("Compare City", saved, index=1)
    c2 = st.sidebar.text_input("Custom Compare City")
    if c2.strip():
        city2 = c2.strip()

# ------- fetch ----------

data1 = get_current(city, unit)
if not data1:
    st.error("City not found.")
    st.stop()

fc1 = get_forecast(city, unit)
if fc1 is None:
    st.error("Forecast error.")
    st.stop()

if compare:
    data2 = get_current(city2, unit)
    fc2 = get_forecast(city2, unit)
    if not data2 or fc2 is None:
        st.error(f"Could not load comparison city: {city2}")
        st.stop()
    both = pd.concat([fc1, fc2])
else:
    both = fc1.copy()

# ---- ui functions -----

def show_city(title, d):
    st.write(f"### {title}")
    c1, c2 = st.columns(2)
    c1.metric(f"Temp ({unit})", f"{d['temp']:.2f}")
    c2.metric("Humidity", f"{d['humidity']:.2f}")

    c3, c4 = st.columns([1, 3])
    c3.image(f"http://openweathermap.org/img/wn/{d['icon']}@2x.png", width=100)
    c4.write("Condition: **" + d["desc"].title() + "**")
    c4.write("Updated: " + str(d["time"]))


# ------ render ---------

if compare:
    colA, colB = st.columns(2)
    with colA: show_city(city, data1)
    with colB: show_city(city2, data2)
else:
    show_city(city, data1)

st.write("---")

# -------- charts ---------

import plotly.express as px

def line(title, col, label):
    st.write("### " + title)
    fig = px.line(
        both,
        x=both.index,
        y=col,
        color="city" if compare else None,
        labels={col: label, "timestamp": "Time"}
    )
    st.plotly_chart(fig, use_container_width=True)

line("Temperature", "temperature", f"Temp ({unit})")
line("Humidity", "humidity", "Humidity")
line("Wind Speed", "wind", "Wind (m/s)")
line("Rain Probability", "rain_prob", "Rain %")

# ------ map --------

st.write("### Locations")
if compare:
    df_map = pd.DataFrame({"lat": [data1["lat"], data2["lat"]], "lon": [data1["lon"], data2["lon"]]})
else:
    df_map = pd.DataFrame({"lat": [data1["lat"]], "lon": [data1["lon"]]})

st.map(df_map)

# -------- table --------

st.write("### Forecast Table")
st.dataframe(
    both.style.format({
        "temperature": "{:.2f}",
        "humidity": "{:.2f}",
        "wind": "{:.2f}",
        "rain_prob": "{:.2f}"
    })
)

# -------- insights ---------

st.write("---")
st.write("## Quick Insights")

def insight(df, label):
    st.write(f"### {label}")
    st.write(f"- Avg Temp: {df['temperature'].mean():.2f}")
    st.write(f"- Max Temp: {df['temperature'].max():.2f}")
    st.write(f"- Min Temp: {df['temperature'].min():.2f}")
    st.write(f"- Avg Wind: {df['wind'].mean():.2f}")
    st.write(f"- Rain>50%: {(df['rain_prob'] > 50).sum()} times")

if compare:
    col1, col2 = st.columns(2)
    with col1: insight(fc1, city)
    with col2: insight(fc2, city2)
else:
    insight(fc1, city)
