from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import requests

# 1. Initialize FastAPI app FIRST
app = FastAPI(title="Global Weather API Proxy")

# 2. Mount static files AFTER app is created so logo.png can be served properly
app.mount("/static", StaticFiles(directory="."), name="static")

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

# 2. Custom Weather API Endpoint
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
        response = requests.get(open_meteo_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        cur = data.get("current", {})
        daily = data.get("daily", {})

        # Process and return structured weather JSON response
        return {
            "source": "custom_fastapi_backend",
            "temp": cur.get("temperature_2m"),
            "feelsLike": cur.get("apparent_temperature"),
            "humidity": cur.get("relative_humidity_2m"),
            "precip": cur.get("precipitation"),
            "windSpeed": cur.get("wind_speed_10m"),
            "windDir": cur.get("wind_direction_10m"),
            "weatherCode": cur.get("weather_code"),
            "time": cur.get("time"),
            "sunrise": daily.get("sunrise", ["—"])[0][-5:] if need_sun and daily.get("sunrise") else "—",
            "sunset": daily.get("sunset", ["—"])[0][-5:] if need_sun and daily.get("sunset") else "—"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch weather data: {str(e)}")
