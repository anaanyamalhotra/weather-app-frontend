import streamlit as st
import requests
import pandas as pd
import datetime
import plotly.express as px
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="🌤️ Weather App", layout="wide")
API_KEY = st.secrets["WEATHER_API_KEY"]

# Initialize session state
for key in ["weather_data", "error", "compare_data"]:
    if key not in st.session_state:
        st.session_state[key] = None

def get_coords(location):
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={API_KEY}"
    res = requests.get(geo_url).json()
    if res:
        return {"lat": res[0]["lat"], "lon": res[0]["lon"]}, None
    return None, "Location not found."

def get_air_quality(lat, lon):
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
    res = requests.get(url).json()
    if "list" in res:
        return res["list"][0]["main"]["aqi"]
    return None

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
    if temp > 38: alerts.append("🔥 Extreme heat")
    if wind > 15: alerts.append("💨 Strong winds")
    if condition in ['storm', 'snow', 'thunderstorm']: alerts.append("⚠️ Severe weather")
    for alert in alerts: st.warning(alert)

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

# Greeting and UI
hour = datetime.datetime.now().hour
greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
st.title("🌦️ Weather Dashboard")
st.markdown(f"_{greeting}! Explore current conditions, AQI, and trends below._")

st.markdown("💡 Use `city` or `postalcode,countrycode` (e.g., `10001` or `10115,de`)")

col1, col2 = st.columns(2)
with col1:
    location1 = st.text_input("Location 1")
    unit = st.radio("Units", ["Celsius", "Fahrenheit"], horizontal=True)
with col2:
    location2 = st.text_input("Compare with (optional)")

if st.button("Get Weather"):
    data1, err1 = get_weather_data(location1, unit)
    st.session_state.weather_data = data1
    st.session_state.error = err1
    st.session_state.compare_data = get_weather_data(location2, unit)[0] if location2 else None

if st.session_state.weather_data:
    data1 = st.session_state.weather_data
    weather1 = data1["weather"]
    forecast1 = data1["forecast"]["list"]
    coords1 = data1["coords"]
    aqi1 = data1["aqi"]

    if st.session_state.compare_data:
        data2 = st.session_state.compare_data
        weather2 = data2["weather"]
        coords2 = data2["coords"]
        aqi2 = data2["aqi"]

        col1, col2 = st.columns(2)

        with col1:
            st.subheader(f"{weather1['name']}, {weather1['sys']['country']}")
            st.write(f"**{weather1['weather'][0]['main']}** — {weather1['weather'][0]['description'].capitalize()}")
            st.metric("Temp", weather1["main"]["temp"])
            st.metric("Humidity", weather1["main"]["humidity"])
            st.metric("Wind", weather1["wind"]["speed"])
            if aqi1: st.info(f"AQI: {aqi1}")
            show_extreme_weather_alert(weather1)

        with col2:
            st.subheader(f"{weather2['name']}, {weather2['sys']['country']}")
            st.write(f"**{weather2['weather'][0]['main']}** — {weather2['weather'][0]['description'].capitalize()}")
            st.metric("Temp", weather2["main"]["temp"])
            st.metric("Humidity", weather2["main"]["humidity"])
            st.metric("Wind", weather2["wind"]["speed"])
            if aqi2: st.info(f"AQI: {aqi2}")
            show_extreme_weather_alert(weather2)

    else:
        st.subheader(f"🌍 Current Weather in {weather1['name']}, {weather1['sys']['country']}")
        st.write(f"**{weather1['weather'][0]['main']}** — {weather1['weather'][0]['description'].capitalize()}")
        st.metric("Temp", weather1["main"]["temp"])
        st.metric("Humidity", weather1["main"]["humidity"])
        st.metric("Wind", weather1["wind"]["speed"])
        if aqi1: st.info(f"AQI: {aqi1}")
        show_extreme_weather_alert(weather1)

        st.subheader("📈 Hourly Trends")
        df = pd.DataFrame([{
            "Time": f["dt_txt"],
            "Temp": f["main"]["temp"],
            "Humidity": f["main"]["humidity"],
            "Wind": f["wind"]["speed"]
        } for f in forecast1[:8]])

        metric = st.selectbox("Show hourly:", ["Temp", "Humidity", "Wind"])
        fig = px.line(df, x="Time", y=metric, markers=True)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("🗺️ Temperature Map")
        render_weather_map(coords1["lat"], coords1["lon"])

        st.subheader("📺 Weather Videos")
        st.markdown(f"[Watch on YouTube]({get_youtube_video_url(location1)})")




