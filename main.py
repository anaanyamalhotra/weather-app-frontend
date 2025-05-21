import streamlit as st
import requests
import pandas as pd
import datetime
import plotly.express as px
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="🌤️ Weather App", layout="wide")
API_KEY = st.secrets["WEATHER_API_KEY"]

# --- Session state setup ---
if "weather_data" not in st.session_state:
    st.session_state.weather_data = None
    st.session_state.error = None
if "compare_data" not in st.session_state:
    st.session_state.compare_data = None

# --- Fetch coordinates ---
def get_coords(location):
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={API_KEY}"
    geo_res = requests.get(geo_url).json()
    if geo_res:
        return {"lat": geo_res[0]["lat"], "lon": geo_res[0]["lon"]}, None
    return None, "Location not found."

# --- Fetch weather data ---
def get_weather_data(location, unit):
    coords, err = get_coords(location)
    if err:
        return None, err
    lat, lon = coords["lat"], coords["lon"]
    units = "metric" if unit == "Celsius" else "imperial"
    weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units={units}&appid={API_KEY}"
    forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units={units}&appid={API_KEY}"
    weather = requests.get(weather_url).json()
    forecast = requests.get(forecast_url).json()
    return {"weather": weather, "forecast": forecast, "coords": coords}, None

# --- Display interactive map ---
def render_weather_map(lat, lon):
    m = folium.Map(location=[lat, lon], zoom_start=6)
    folium.TileLayer(
        tiles='https://tile.openweathermap.org/map/temp_new/{z}/{x}/{y}.png?appid=' + API_KEY,
        attr='OpenWeatherMap',
        name='Temperature',
        overlay=True,
        control=True
    ).add_to(m)
    folium.Marker([lat, lon], tooltip="Selected Location").add_to(m)
    st_folium(m, width=700, height=500)

# --- Generate alert box ---
def show_extreme_weather_alert(weather):
    alerts = []
    temp = weather['main']['temp']
    wind = weather['wind']['speed']
    condition = weather['weather'][0]['main']

    if temp > 38:
        alerts.append("🔥 Extreme heat alert")
    if wind > 15:
        alerts.append("💨 Strong wind conditions")
    if condition.lower() in ['storm', 'snow', 'thunderstorm']:
        alerts.append("⚠️ Severe weather warning")

    for a in alerts:
        st.warning(a)

# --- Greeting ---
hour = datetime.datetime.now().hour
greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
st.title("🌤️ Weather Dashboard")
st.markdown(f"_{greeting}! Check weather trends and compare locations interactively._")

# --- Inputs ---
col1, col2 = st.columns(2)
with col1:
    location1 = st.text_input("Location 1 (e.g., New York or Delhi)")
    unit = st.radio("Temperature Unit", ["Celsius", "Fahrenheit"], horizontal=True)
with col2:
    location2 = st.text_input("Optional: Compare with Location 2 (e.g., Tokyo or Berlin)")

submit = st.button("Get Weather")

# --- Fetch on click ---
if submit:
    data1, error1 = get_weather_data(location1, unit)
    st.session_state.weather_data = data1
    st.session_state.error = error1
    if location2:
        data2, _ = get_weather_data(location2, unit)
        st.session_state.compare_data = data2
    else:
        st.session_state.compare_data = None

# --- Display section ---
if st.session_state.weather_data:
    data1 = st.session_state.weather_data
    weather = data1['weather']
    forecast = data1['forecast']['list']
    coords = data1['coords']

    st.subheader(f"Current Weather in {weather['name']}, {weather['sys']['country']}")
    st.write(f"**{weather['weather'][0]['main']}** — {weather['weather'][0]['description'].capitalize()}")
    st.metric(f"Temperature (°{'C' if unit == 'Celsius' else 'F'})", weather["main"]["temp"])
    st.metric("Humidity (%)", weather["main"]["humidity"])
    st.metric("Wind (m/s)", weather["wind"]["speed"])

    show_extreme_weather_alert(weather)

    # --- Hourly forecast ---
    st.subheader("📊 Hour-by-Hour Forecast (Next 24h)")
    df = pd.DataFrame([{
        "Time": f["dt_txt"],
        "Temp": f["main"]["temp"],
        "Humidity": f["main"]["humidity"],
        "Wind": f["wind"]["speed"]
    } for f in forecast[:8]])
    fig = px.line(df, x="Time", y="Temp", markers=True, title="Temperature")
    st.plotly_chart(fig, use_container_width=True)

    # --- 5-Day Forecast Table ---
    st.subheader("📅 5-Day Snapshot")
    snapshot = forecast[::8]
    daily = pd.DataFrame([{
        "Date": f["dt_txt"].split()[0],
        "Condition": f["weather"][0]["description"].capitalize(),
        f"Temp (°{'C' if unit == 'Celsius' else 'F'})": f["main"]["temp"]
    } for f in snapshot])
    st.dataframe(daily, use_container_width=True)

    st.subheader("🗺️ Temperature Map")
    render_weather_map(coords["lat"], coords["lon"])

    # --- YouTube link ---
    st.subheader("📺 Weather Videos")
    st.markdown(f"[Watch weather videos for {location1}](https://www.youtube.com/results?search_query={location1.replace(' ', '+')}+weather)")

# --- Comparison View ---
if st.session_state.compare_data:
    st.divider()
    data2 = st.session_state.compare_data
    w2 = data2['weather']
    st.subheader(f"🔁 Comparison: {w2['name']}, {w2['sys']['country']}")
    st.write(f"**{w2['weather'][0]['main']}** — {w2['weather'][0]['description'].capitalize()}")
    st.metric(f"Temperature (°{'C' if unit == 'Celsius' else 'F'})", w2["main"]["temp"])
    st.metric("Humidity (%)", w2["main"]["humidity"])
    st.metric("Wind (m/s)", w2["wind"]["speed"])
    show_extreme_weather_alert(w2)


