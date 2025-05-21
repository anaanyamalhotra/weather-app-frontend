import streamlit as st
import requests
import pandas as pd
import datetime
import plotly.express as px
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="🌤️ Weather App", layout="wide")
API_KEY = st.secrets["WEATHER_API_KEY"]

# Session state setup
for key in ["weather_data", "error", "compare_data"]:
    if key not in st.session_state:
        st.session_state[key] = None

# Get coordinates from city or zip input
def get_coords(location):
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={API_KEY}"
    res = requests.get(geo_url).json()
    if res:
        return {"lat": res[0]["lat"], "lon": res[0]["lon"]}, None
    return None, "Location not found."

# Fetch AQI from OpenWeatherMap
def get_air_quality(lat, lon):
    aqi_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
    res = requests.get(aqi_url).json()
    if "list" in res and len(res["list"]) > 0:
        return res["list"][0]["main"]["aqi"]
    return None

# Fetch weather and forecast
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
    aqi = get_air_quality(lat, lon)
    return {"weather": weather, "forecast": forecast, "coords": coords, "aqi": aqi}, None

def show_extreme_weather_alert(weather):
    alerts = []
    temp = weather['main']['temp']
    wind = weather['wind']['speed']
    condition = weather['weather'][0]['main'].lower()

    if temp > 38:
        alerts.append("🔥 Extreme heat alert")
    if wind > 15:
        alerts.append("💨 Strong wind conditions")
    if condition in ['storm', 'snow', 'thunderstorm']:
        alerts.append("⚠️ Severe weather warning")

    for a in alerts:
        st.warning(a)

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

def get_youtube_video_url(query):
    return f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}+weather"

# Greeting
hour = datetime.datetime.now().hour
greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
st.title("🌤️ Interactive Weather Dashboard")
st.markdown(f"_{greeting}! Check the weather, air quality, and forecasts._")

# Inputs
st.markdown("💡 Enter a city or ZIP code:")
st.markdown("- For U.S. ZIPs: `10001` or `Los Angeles`")
st.markdown("- For international: use `postalcode,countrycode` like `110001,in` or `10115,de`")

col1, col2 = st.columns(2)
with col1:
    location1 = st.text_input("Location 1")
    unit = st.radio("Units", ["Celsius", "Fahrenheit"], horizontal=True)
with col2:
    location2 = st.text_input("Compare with (optional)")

if st.button("Get Weather"):
    data1, error1 = get_weather_data(location1, unit)
    st.session_state.weather_data = data1
    st.session_state.error = error1
    st.session_state.compare_data = get_weather_data(location2, unit)[0] if location2 else None

# Main location
if st.session_state.weather_data:
    data = st.session_state.weather_data
    weather = data["weather"]
    forecast = data["forecast"]["list"]
    coords = data["coords"]

    st.subheader(f"🌍 Current Weather in {weather['name']}, {weather['sys']['country']}")
    st.write(f"**{weather['weather'][0]['main']}** — {weather['weather'][0]['description'].capitalize()}")
    st.metric(f"Temperature (°{'C' if unit == 'Celsius' else 'F'})", weather["main"]["temp"])
    st.metric("Humidity (%)", weather["main"]["humidity"])
    st.metric("Wind (m/s)", weather["wind"]["speed"])
    show_extreme_weather_alert(weather)

    # AQI
    aqi_labels = {1: "🟢 Good", 2: "🟡 Fair", 3: "🟠 Moderate", 4: "🔴 Poor", 5: "🟣 Very Poor"}
    if data["aqi"]:
        st.info(f"Air Quality Index (AQI): {data['aqi']} — {aqi_labels.get(data['aqi'], 'Unknown')}")

    # Hourly plots
    st.subheader("📈 Hourly Forecast (Next 24h)")
    df = pd.DataFrame([{
        "Time": f["dt_txt"],
        "Temp": f["main"]["temp"],
        "Humidity": f["main"]["humidity"],
        "Wind": f["wind"]["speed"]
    } for f in forecast[:8]])

    metric = st.selectbox("Choose metric to plot", ["Temp", "Humidity", "Wind"])
    fig = px.line(df, x="Time", y=metric, markers=True, title=f"{metric} over next 24h")
    st.plotly_chart(fig, use_container_width=True)

    # 5-day forecast
    st.subheader("📅 5-Day Snapshot")
    snapshot = forecast[::8]
    daily = pd.DataFrame([{
        "Date": f["dt_txt"].split()[0],
        "Condition": f["weather"][0]["description"].capitalize(),
        f"Temp (°{'C' if unit == 'Celsius' else 'F'})": f["main"]["temp"]
    } for f in snapshot])
    st.dataframe(daily, use_container_width=True)

    # Map
    st.subheader("🗺️ Temperature Map")
    render_weather_map(coords["lat"], coords["lon"])

    # YouTube
    st.subheader("📺 Related Weather Videos")
    st.markdown(f"[Search YouTube for {location1} weather]({get_youtube_video_url(location1)})")

# Comparison location
if st.session_state.compare_data:
    comp = st.session_state.compare_data["weather"]
    st.divider()
    st.subheader(f"🔁 Comparison: {comp['name']}, {comp['sys']['country']}")
    st.write(f"**{comp['weather'][0]['main']}** — {comp['weather'][0]['description'].capitalize()}")
    st.metric(f"Temperature (°{'C' if unit == 'Celsius' else 'F'})", comp["main"]["temp"])
    st.metric("Humidity (%)", comp["main"]["humidity"])
    st.metric("Wind (m/s)", comp["wind"]["speed"])
    show_extreme_weather_alert(comp)



