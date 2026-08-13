from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import requests

app = FastAPI(title="Global Weather API Proxy")

# Enable CORS so your frontend can communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Serve the HTML Dashboard Interface
@app.get("/", response_class=FileResponse)
def read_root():
    return FileResponse("index.html")

# 2. Custom Weather API Endpoint with safe error fallback
@app.get("/api/weather")
def get_weather(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    need_sun: bool = Query(False, description="Include sunrise/sunset times")
):
    daily_param = "&daily=sunrise,sunset" if need_sun else ""
    open_meteo_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
        f"precipitation,weather_code,wind_speed_10m,wind_direction_10m"
        f"{daily_param}&timezone=auto"
    )

    try:
        headers = {"User-Agent": "AetheriaWeatherApp/1.0"}
        response = requests.get(open_meteo_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return {
                "source": "fallback",
                "temp": 0, "feelsLike": 0, "humidity": 0, "precip": 0,
                "windSpeed": 0, "windDir": 0, "weatherCode": 3,
                "time": None, "sunrise": "—", "sunset": "—"
            }
            
        data = response.json()
        cur = data.get("current", {})
        daily = data.get("daily", {})

        # Process and return structured weather JSON response
        return {
            "source": "custom_fastapi_backend",
            "temp": cur.get("temperature_2m", 0),
            "feelsLike": cur.get("apparent_temperature", 0),
            "humidity": cur.get("relative_humidity_2m", 0),
            "precip": cur.get("precipitation", 0),
            "windSpeed": cur.get("wind_speed_10m", 0),
            "windDir": cur.get("wind_direction_10m", 0),
            "weatherCode": cur.get("weather_code", 0),
            "time": cur.get("time"),
            "sunrise": daily.get("sunrise", ["—"])[0][-5:] if need_sun and daily.get("sunrise") else "—",
            "sunset": daily.get("sunset", ["—"])[0][-5:] if need_sun and daily.get("sunset") else "—"
        }
    except Exception as e:
        return {
            "source": "error_fallback",
            "temp": 0, "feelsLike": 0, "humidity": 0, "precip": 0,
            "windSpeed": 0, "windDir": 0, "weatherCode": 3,
            "time": None, "sunrise": "—", "sunset": "—"
        }
