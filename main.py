import streamlit as st
import requests
import pandas as pd
import datetime
import plotly.express as px
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="🌦️ Weather App", layout="wide")
API_KEY = st.secrets["WEATHER_API_KEY"]

# Session setup
for key in ["weather_data", "compare_data"]:
    if key not in st.session_state:
        st.session_state[key] = None

# API helpers
def get_coords(location):
    res = requests.get(f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={API_KEY}").json()
    return ({"lat": res[0]["lat"], "lon": res[0]["lon"]}, None) if res else (None, "Location not found.")

def get_air_quality(lat, lon):
    res = requests.get(f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}").json()
    return res.get("list", [{}])[0].get("main", {}).get("aqi")

def get_weather_data(location, unit):
    coords, err = get_coords(location)
    if err: return None, err
    lat, lon = coords["lat"], coords["lon"]
    u = "metric" if unit == "Celsius" else "imperial"
    weather = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units={u}&appid={API_KEY}").json()
    forecast = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units={u}&appid={API_KEY}").json()
    aqi = get_air_quality(lat, lon)
    return {"weather": weather, "forecast": forecast, "coords": coords, "aqi": aqi}, None

# UI helpers
def show_alerts(w):
    alerts = []
    if w['main']['temp'] > 38: alerts.append("🔥 Extreme heat")
    if w['wind']['speed'] > 15: alerts.append("💨 Strong wind")
    if w['weather'][0]['main'].lower() in ['storm', 'snow', 'thunderstorm']: alerts.append("⚠️ Severe weather")
    for a in alerts: st.warning(a)

def show_map(lat, lon):
    m = folium.Map(location=[lat, lon], zoom_start=6)
    folium.TileLayer(tiles='https://tile.openweathermap.org/map/temp_new/{z}/{x}/{y}.png?appid=' + API_KEY, attr='OpenWeatherMap').add_to(m)
    folium.Marker([lat, lon], tooltip="Location").add_to(m)
    st_folium(m, width=700, height=500)

def show_youtube(location):
    youtube_url = f"https://www.youtube.com/results?search_query={location.replace(' ', '+')}+weather"
    st.markdown(
        f"""
        <div style='padding: 0.5em 1em; background-color: #1e1e1e; border: 1px solid #444; border-radius: 8px;'>
            <h4 style='margin: 0 0 0.5em 0;'>📺 Related Weather Videos</h4>
            <a href="{youtube_url}" target="_blank" style="text-decoration: none; color: #1e90ff; font-weight: 600;">
                ▶️ Watch weather videos for {location.title()}
            </a>
         </div>
         """,
         unsafe_allow_html=True
    )

def show_hourly_chart(forecast, metric):
    df = pd.DataFrame([{
        "Time": f["dt_txt"], 
        "Temp": f["main"]["temp"], 
        "Humidity": f["main"]["humidity"], 
        "Wind": f["wind"]["speed"]
    } for f in forecast[:8]])
    fig = px.line(df, x="Time", y=metric, title=f"{metric} over next 24h", markers=True)
    st.plotly_chart(fig, use_container_width=True)

def show_5day_table(forecast, unit):
    data = [{
        "Date": f["dt_txt"].split()[0],
        "Condition": f["weather"][0]["description"].capitalize(),
        f"Temp (°{'C' if unit == 'Celsius' else 'F'})": f["main"]["temp"]
    } for f in forecast[::8]]
    st.dataframe(pd.DataFrame(data), use_container_width=True)

# Greeting
hr = datetime.datetime.now().hour
greet = "Good morning" if hr < 12 else "Good afternoon" if hr < 18 else "Good evening"
st.title("🌦️ Weather Dashboard")
st.markdown(f"_{greet}! Compare forecasts, maps, AQI, and more._")

st.markdown("💡 Input city or ZIP. International ZIPs: `10115,de` (Berlin), `110001,in` (Delhi)")

colL, colR = st.columns(2)
with colL:
    loc1 = st.text_input("Location 1")
    unit = st.radio("Temperature Unit", ["Celsius", "Fahrenheit"], horizontal=True)
with colR:
    loc2 = st.text_input("Compare with (optional)")

if st.button("Get Weather"):
    st.session_state.weather_data, _ = get_weather_data(loc1, unit)
    if loc2:
        st.session_state.compare_data, _ = get_weather_data(loc2, unit)
    else:
        st.session_state.compare_data = None

# Side-by-side comparison
if st.session_state.weather_data:
    w1 = st.session_state.weather_data
    w2 = st.session_state.compare_data

    if w2:
        col1, col2 = st.columns(2)

        # Location 1
        with col1:
            weather, forecast, coords, aqi = w1["weather"], w1["forecast"]["list"], w1["coords"], w1["aqi"]
            st.subheader(f"📍 {weather['name']}, {weather['sys']['country']}")
            st.metric("Temperature", weather["main"]["temp"])
            st.metric("Humidity", weather["main"]["humidity"])
            st.metric("Wind", weather["wind"]["speed"])
            if aqi: st.info(f"AQI: {aqi}")
            show_alerts(weather)
            show_hourly_chart(forecast, "Temp")
            show_5day_table(forecast, unit)
            show_map(coords["lat"], coords["lon"])
            show_youtube(loc1)

        # Location 2
        with col2:
            weather, forecast, coords, aqi = w2["weather"], w2["forecast"]["list"], w2["coords"], w2["aqi"]
            st.subheader(f"📍 {weather['name']}, {weather['sys']['country']}")
            st.metric("Temperature", weather["main"]["temp"])
            st.metric("Humidity", weather["main"]["humidity"])
            st.metric("Wind", weather["wind"]["speed"])
            if aqi: st.info(f"AQI: {aqi}")
            show_alerts(weather)
            show_hourly_chart(forecast, "Temp")
            show_5day_table(forecast, unit)
            show_map(coords["lat"], coords["lon"])
            show_youtube(loc2)

    else:
        weather = w1["weather"]
        forecast = w1["forecast"]["list"]
        coords = w1["coords"]
        aqi = w1["aqi"]

        st.subheader(f"📍 {weather['name']}, {weather['sys']['country']}")
        st.metric("Temperature", weather["main"]["temp"])
        st.metric("Humidity", weather["main"]["humidity"])
        st.metric("Wind", weather["wind"]["speed"])
        if aqi: st.info(f"AQI: {aqi}")
        show_alerts(weather)

        metric = st.selectbox("Choose metric to plot", ["Temp", "Humidity", "Wind"])
        show_hourly_chart(forecast, metric)
        show_5day_table(forecast, unit)
        show_map(coords["lat"], coords["lon"])
        show_youtube(loc1)




