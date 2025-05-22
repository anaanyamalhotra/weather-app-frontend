
import streamlit as st
import requests
import pandas as pd
import datetime
import plotly.express as px
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="🌦️ Airvue", layout="wide")
BACKEND_URL = "https://weather-api-backend-1.onrender.com"

for key in ["weather_data", "compare_data"]:
    if key not in st.session_state:
        st.session_state[key] = None

def fetch_weather_from_backend(location, unit):
    try:
        res = requests.get(f"{BACKEND_URL}/weather", params={"location": location, "unit": unit})
        if res.status_code == 200:
            return res.json(), None
        return None, f"Error {res.status_code}"
    except Exception as e:
        return None, str(e)

def save_to_backend(location, weather, aqi):
    try:
        aqi_value = aqi["aqi"] if isinstance(aqi, dict) and "aqi" in aqi else 0
        payload = {
            "location": location,
            "temperature": weather["main"]["temp"],
            "humidity": weather["main"]["humidity"],
            "wind": weather["wind"]["speed"],
            "aqi": aqi_value
        }
        res = requests.post(f"{BACKEND_URL}/records/", json=payload)
        if res.status_code == 200:
            st.success("✅ Saved weather data to database.")
    except Exception as e:
        st.warning(f"⚠️ Could not save to database: {e}")

def show_alerts(w):
    alerts = []
    if w['main']['temp'] > 38: alerts.append("🔥 Extreme heat")
    if w['wind']['speed'] > 15: alerts.append("💨 Strong wind")
    if w['weather'][0]['main'].lower() in ['storm', 'snow', 'thunderstorm']: alerts.append("⚠️ Severe weather")
    for a in alerts: st.warning(a)

def show_map(lat, lon):
    m = folium.Map(location=[lat, lon], zoom_start=6)
    folium.TileLayer(tiles='https://tile.openweathermap.org/map/temp_new/{z}/{x}/{y}.png?appid=placeholder', attr='OpenWeatherMap').add_to(m)
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
    col_map = {"Temperature": "Temp", "Humidity": "Humidity", "Wind": "Wind"}
    y_col = col_map.get(metric, metric)
    fig = px.line(df, x="Time", y=y_col, title=f"{metric} over next 24h", markers=True)
    st.plotly_chart(fig, use_container_width=True)

def show_5day_table(forecast, unit):
    data = [{
        "Date": f["dt_txt"].split()[0],
        "Condition": f["weather"][0]["description"].capitalize(),
        f"Temp (°{'C' if unit == 'metric' else 'F'})": f["main"]["temp"]
    } for f in forecast[::8]]
    st.dataframe(pd.DataFrame(data), use_container_width=True)

def show_aqi_card(aqi):
    if not isinstance(aqi, dict) or not aqi or "aqi" not in aqi:
        st.warning("⚠️ Air Quality data not available for this location.")
        return

    aqi_score = aqi.get('aqi', 0)
    components = aqi.get('components', {})

    aqi_label = {
        1: "🟢 Good", 2: "🟡 Fair", 3: "🟠 Moderate", 4: "🔴 Poor", 5: "🟣 Very Poor"
    }

    st.markdown(f"""
    <div style='background-color:#111; padding:1em; border-radius:10px; border: 1px solid #444; margin-bottom: 1em;'>
        <h4 style='margin:0 0 0.5em 0;'>🌫️ Air Quality Index: 
        <span style='color:#1e90ff'>{aqi_score} — {aqi_label.get(aqi_score, "Unknown")}</span></h4>
    </div>
    """, unsafe_allow_html=True)

    if not components:
        st.info("No detailed pollutant data available.")
        return

    def get_pollutant_level(name, value):
        if name in ["pm2_5", "pm10"]:
            return "🟢 Low" if value <= 12 else "🟡 Moderate" if value <= 35 else "🔴 High"
        elif name == "o3":
            return "🟢 Low" if value <= 100 else "🟡 Moderate" if value <= 160 else "🔴 High"
        elif name == "co":
            return "🟢 Low" if value <= 1000 else "🟡 Moderate" if value <= 2000 else "🔴 High"
        else:
            return "⚪️"

    labels = {
        "pm2_5": "PM2.5", "pm10": "PM10", "co": "CO", "no": "NO", "no2": "NO₂",
        "o3": "O₃", "so2": "SO₂", "nh3": "NH₃"
    }

    df = pd.DataFrame([{
        "Pollutant": labels.get(k, k.upper()),
        "Level": get_pollutant_level(k, v),
        "µg/m³": round(v, 2)
    } for k, v in components.items()])
    st.dataframe(df, hide_index=True, use_container_width=True)

# Main UI
st.title("🌦️ Airvue")
st.markdown("💡 Enter a location (e.g., New York or 10001). For international ZIP codes, use: postal code, country code (e.g., 10115,de or 110001,in)")

colL, colR = st.columns(2)
with colL:
    loc1 = st.text_input("Location 1")
    unit = st.radio("Temperature Unit", ["Celsius", "Fahrenheit"], horizontal=True)
    unit_api = "metric" if unit == "Celsius" else "imperial"
with colR:
    loc2 = st.text_input("Compare with (optional)")

if st.button("Get Weather"):
    st.session_state.weather_data, _ = fetch_weather_from_backend(loc1, unit_api)
    st.session_state.compare_data, _ = fetch_weather_from_backend(loc2, unit_api) if loc2 else (None, None)

# Main Output
if st.session_state.weather_data:
    w1 = st.session_state.weather_data
    w2 = st.session_state.compare_data
    
    metric = st.selectbox("📊 Choose metric to plot", ["Temperature", "Humidity", "Wind"])
    if w2:
        col1, col2 = st.columns(2)
        for col, data, loc in zip([col1, col2], [w1, w2], [loc1, loc2]):
            with col:
                weather, forecast, coords, aqi = data["weather"], data["forecast"]["list"], data["coords"], data["aqi"]
                st.subheader(f"📍 {weather['name']}, {weather['sys']['country']}")
                st.metric("🌡️ Temperature", f"{weather['main'].get('temp', 'N/A')} °{ 'C' if unit_api == 'metric' else 'F'}")
                st.metric("💧 Humidity", f"{weather['main'].get('humidity', 'N/A')}%")
                st.metric("💨 Wind", f"{weather['wind'].get('speed', 'N/A')} m/s")
                show_aqi_card(aqi)
                show_alerts(weather)
                show_hourly_chart(forecast, metric)
                show_5day_table(forecast, unit_api)
                show_map(coords["lat"], coords["lon"])
                show_youtube(loc)
                save_to_backend(loc, weather, aqi)
    else:
        weather = w1["weather"]
        forecast = w1["forecast"]["list"]
        coords = w1["coords"]
        aqi = w1["aqi"]

        st.subheader(f"📍 {weather['name']}, {weather['sys']['country']}")
        st.metric("🌡️ Temperature", f"{weather['main'].get('temp', 'N/A')} °{ 'C' if unit_api == 'metric' else 'F'}")
        st.metric("💧 Humidity", f"{weather['main'].get('humidity', 'N/A')}%")
        st.metric("💨 Wind", f"{weather['wind'].get('speed', 'N/A')} m/s")
        show_aqi_card(aqi)
        show_alerts(weather)

        metric = st.selectbox("Choose metric to plot", ["Temperature", "Humidity", "Wind"])
        show_hourly_chart(forecast, metric)
        show_5day_table(forecast, unit_api)
        show_map(coords["lat"], coords["lon"])
        show_youtube(loc1)
        save_to_backend(loc1, weather, aqi)

# Admin Tab for record viewing
st.markdown("---")
if st.checkbox("🗂️ Show Saved Weather Records (DB)"):
    try:
        r = requests.get(f"{BACKEND_URL}/records/")
        if r.status_code == 200:
            df = pd.DataFrame(r.json())
            st.dataframe(df)
            st.download_button("📥 Export as CSV", data=df.to_csv(index=False), file_name="weather_history.csv", mime="text/csv")
        else:
            st.warning("Could not load records.")
    except Exception as e:
        st.error(f"Error: {e}")

# About Section
st.markdown("---")
st.markdown("### 👤 About This App")
st.markdown("Developed by Ananya Malhotra")

st.markdown("### 🚀 About Product Manager Accelerator")
st.markdown("""
Product Manager Accelerator (PMA) is a global community and coaching platform founded by Dr. Nancy Li. PMA empowers aspiring and experienced product managers to break into and excel in product management careers.
""")
