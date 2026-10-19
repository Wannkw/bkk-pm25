"""
Pull hourly PM2.5 from the Open-Meteo air quality API (CAMS model data, no key needed)
and save one CSV per city into data/.

Usage: python fetch_data.py
"""
import time
from pathlib import Path

import pandas as pd
import requests

API = "https://air-quality-api.open-meteo.com/v1/air-quality"

CITIES = {
    "bangkok": (13.7563, 100.5018),
    "chiang_mai": (18.7883, 98.9853),
}

START = "2023-01-01"
END = "2026-09-30"

OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)


def fetch(lat, lon):
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "pm2_5",
        "start_date": START,
        "end_date": END,
        "timezone": "Asia/Bangkok",
    }
    r = requests.get(API, params=params, timeout=60)
    r.raise_for_status()
    h = r.json()["hourly"]
    return pd.DataFrame({"time": pd.to_datetime(h["time"]), "pm25": h["pm2_5"]})


for name, (lat, lon) in CITIES.items():
    df = fetch(lat, lon)
    df.to_csv(OUT / f"{name}_hourly.csv", index=False)
    print(f"{name}: {len(df):,} rows, {df.pm25.isna().sum()} missing")
    time.sleep(1)  # be nice to the free API
