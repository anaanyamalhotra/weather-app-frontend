import streamlit as st
import requests
import pandas as pd
import base64
import json
import datetime
import plotly.express as px
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Weather App", layout="centered")
API_KEY = st.secrets["WEATHER_API_KEY"]

# --- Persist weather data between reruns ---
if "weather_data" not in st.session_state:
    st.session_state.weather_data = None
    st.session_state.error = None

# --- Coordinate resolution ---
def get_coords(location):
    if "," in location:
        zip_part, country = location.split(",", 1)
        zip_url = f"http://api.openweathermap.org/data/2.5/weather?zip={zip_part.strip()},{country.strip()}&appid={API_KEY}"
        res = requests.get(zip_url)
        if res.status_code == 200:
            data = res.json()
            return data["coord"], None
    elif location.isdigit():
        zip_url = f"http://api.openweathermap.org/data/2.5/weather?zip={location},us&appid={API_KEY}"
        res = requests.get(zip_url)
        if res.status_code == 200:
            data = res.json()
            return data["coord"], None

    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={API_KEY}"
    geo_res = requests.get(geo_url).json()
    if geo_res:
        return {"lat": geo_res[0]["lat"], "lon": geo_res[0]["lon"]}, None
    return None, "Location not found."

# --- Weather data fetching ---
def get_weather_data(location, unit):
    coords, err = get_coords(location)
    if err:
        return None, err
    lat = coords["lat"]
    lon = coords["lon"]
    units = "metric" if unit == "Celsius" else "imperial"
    weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units={units}&appid={API_KEY}"
    forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units={units}&appid={API_KEY}"
    try:
        weather = requests.get(weather_url).json()
        forecast = requests.get(forecast_url).json()
        return {"weather": weather, "forecast": forecast, "coords": coords}, None
    except:
        return None, "Failed to retrieve weather data."

# --- Interactive map ---
def render_weather_map(lat, lon):
    m = folium.Map(location=[lat, lon], zoom_start=6)
    folium.TileLayer(
        tiles='https://tile.openweathermap.org/map/temp_new/{z}/{x}/{y}.png?appid=' + API_KEY,
        attr='OpenWeatherMap',
        name='Temperature',
        overlay=True,
        control=True
    ).add_to(m)
    folium.Marker([lat, lon], tooltip="Location").add_to(m)
    st_folium(m, width=700, height=500)

# --- Export helpers ---
def generate_pdf_download_link(df):
    html = df.to_html(index=False)
    b64 = base64.b64encode(html.encode()).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="forecast.html">📄 Download as PDF (HTML)</a>'

def generate_json_download(data):
    json_data = json.dumps(data, indent=2)
    b64 = base64.b64encode(json_data.encode()).decode()
    return f'<a href="data:application/json;base64,{b64}" download="forecast.json">🔽 Download as JSON</a>'

def get_youtube_video_url(query):
    return f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}+weather"

# --- Greeting ---
hour = datetime.datetime.now().hour
if hour < 12:
    greeting = "Good morning"
elif hour < 18:
    greeting = "Good afternoon"
else:
    greeting = "Good evening"

st.title("🌤️ Weather App")
st.markdown(f"_{greeting}! Check the weather, forecast, and explore your location below._")

location = st.text_input("Enter a location (e.g., New York or 10001). For international ZIP codes, use: postal code, country code (e.g., 10115,de)")
unit = st.radio("Choose temperature unit:", ["Celsius", "Fahrenheit"])

if st.button("Get Weather") and location:
    with st.spinner("Fetching weather..."):
        data, error = get_weather_data(location, unit)
        st.session_state.weather_data = data
        st.session_state.error = error

# --- Display Section ---
if st.session_state.weather_data:
    data = st.session_state.weather_data
    error = st.session_state.error

    weather = data["weather"]
    forecast_data = data["forecast"]
    coords = data["coords"]

    st.subheader(f"Current Weather in {weather['name']}, {weather['sys']['country']}")
    st.write(f"**{weather['weather'][0]['main']}** — {weather['weather'][0]['description'].capitalize()}")
    st.metric(f"Temperature (°{'C' if unit == 'Celsius' else 'F'})", weather["main"]["temp"])
    st.metric("Humidity (%)", weather["main"]["humidity"])
    st.metric("Wind (m/s)", weather["wind"]["speed"])

    st.subheader("📅 5-Day Forecast")
    forecast = forecast_data["list"]
    filtered = forecast[::8]
    df = pd.DataFrame([{
        "Date": f["dt_txt"],
        "Condition": f["weather"][0]["description"].capitalize(),
        f"Temp (°{'C' if unit == 'Celsius' else 'F'})": f["main"]["temp"]
    } for f in filtered])
    st.table(df)

    st.download_button("⬇️ Download CSV", df.to_csv(index=False), file_name="forecast.csv", mime="text/csv")
    st.markdown(generate_pdf_download_link(df), unsafe_allow_html=True)
    st.markdown(generate_json_download(filtered), unsafe_allow_html=True)

    st.subheader("📊 Forecast Temperature Trend")
    fig = px.line(df, x="Date", y=df.columns[-1], markers=True)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("🗺️ Interactive Weather Map")
    render_weather_map(coords["lat"], coords["lon"])

    st.subheader("📺 Related YouTube Search")
    st.markdown(f"[Watch weather videos for this location]({get_youtube_video_url(location)})")

