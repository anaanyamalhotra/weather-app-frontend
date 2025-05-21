import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Weather App", layout="centered")

API_KEY = st.secrets["WEATHER_API_KEY"]

def get_weather_data(location):
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={API_KEY}"
    geo_res = requests.get(geo_url).json()
    if not geo_res:
        return None, "Location not found."
    lat = geo_res[0]["lat"]
    lon = geo_res[0]["lon"]

    weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={API_KEY}"
    forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={API_KEY}"
    try:
        weather = requests.get(weather_url).json()
        forecast = requests.get(forecast_url).json()
        return {"weather": weather, "forecast": forecast}, None
    except:
        return None, "Failed to retrieve weather data."

st.title("🌤️ Weather App")
location = st.text_input("Enter a city or zip code:")

if st.button("Get Weather") and location:
    with st.spinner("Fetching weather..."):
        data, error = get_weather_data(location)
        if error:
            st.error(error)
        else:
            weather = data["weather"]
            st.subheader(f"Current Weather in {weather['name']}, {weather['sys']['country']}")
            st.write(f"**{weather['weather'][0]['main']}** — {weather['weather'][0]['description'].capitalize()}")
            st.metric("Temperature (°C)", weather["main"]["temp"])
            st.metric("Humidity (%)", weather["main"]["humidity"])
            st.metric("Wind (m/s)", weather["wind"]["speed"])

            st.subheader("5-Day Forecast")
            forecast = data["forecast"]["list"]
            filtered = forecast[::8]
            df = pd.DataFrame([{
                "Date": f["dt_txt"],
                "Condition": f["weather"][0]["description"].capitalize(),
                "Temp (°C)": f["main"]["temp"]
            } for f in filtered])
            st.table(df)
            st.download_button("Download CSV", df.to_csv(index=False), file_name="forecast.csv", mime="text/csv")
