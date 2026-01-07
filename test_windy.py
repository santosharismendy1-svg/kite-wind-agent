import os
import json
import math
import requests
from dotenv import load_dotenv

load_dotenv()

WINDY_API_KEY = os.getenv("WINDY_API_KEY")
if not WINDY_API_KEY:
    raise SystemExit("❌ Falta WINDY_API_KEY en .env")

KNOTS_PER_MS = 1.9438444924406

def uv_to_speed_dir(u_ms: float, v_ms: float):
    """
    Windy devuelve viento como vector:
      u: componente hacia el Este (positivo = viento "empujando" hacia el Este)
      v: componente hacia el Norte (positivo = viento "empujando" hacia el Norte)
    Convertimos a:
      - speed en kt
      - direction en grados meteorológicos (de donde viene el viento)
    """
    speed_ms = math.sqrt(u_ms*u_ms + v_ms*v_ms)
    speed_kt = speed_ms * KNOTS_PER_MS

    # Dirección "from" meteorológica
    # atan2 devuelve el ángulo del vector (u,v) hacia donde va.
    # Para pasar a "from" (de dónde viene), invertimos el vector: (-u, -v)
    dir_rad = math.atan2(-u_ms, -v_ms)
    dir_deg = (math.degrees(dir_rad) + 360) % 360
    return speed_kt, dir_deg

def get_point_forecast(lat: float, lon: float):
    url = "https://api.windy.com/api/point-forecast/v2"
    payload = {
        "lat": lat,
        "lon": lon,
        "model": "gfs",                 # ✅ GFS global (Argentina OK)
        "parameters": ["wind", "windGust"],  # ✅ wind -> u/v, windGust -> gust
        "levels": ["surface"],
        "key": WINDY_API_KEY
    }
    r = requests.post(url, json=payload, timeout=30)

    # Si falla, imprimimos el body para ver el motivo exacto
    if r.status_code != 200:
        print("❌ Status:", r.status_code)
        print("❌ Response:", r.text[:2000])
        r.raise_for_status()

    return r.json()

def main():
    cfg = json.load(open("config.json", encoding="utf-8"))
    spot = cfg["spots"][0]
    print(f"📍 Probando spot: {spot['name']} ({spot['lat']}, {spot['lon']})")

    data = get_point_forecast(spot["lat"], spot["lon"])

    # Keys importantes según doc:
    # ts, wind_u-surface, wind_v-surface, gust-surface, units, etc.
    print("✅ Keys de la respuesta:", list(data.keys()))

    ts = data.get("ts", [])
    u = data.get("wind_u-surface", [])
    v = data.get("wind_v-surface", [])
    gust = data.get("gust-surface", [])

    print(f"✅ Puntos: ts={len(ts)}, u={len(u)}, v={len(v)}, gust={len(gust)}")

    # Mostrar primeras 8 horas
    print("\nPrimeras 8 entradas (kt / dir):")
    for i in range(min(8, len(ts))):
        if u[i] is None or v[i] is None:
            continue
        speed_kt, dir_deg = uv_to_speed_dir(u[i], v[i])
        g_kt = (gust[i] * KNOTS_PER_MS) if i < len(gust) and gust[i] is not None else None
        print(f"- i={i} | wind={speed_kt:5.1f} kt | dir={dir_deg:6.1f}° | gust={g_kt:.1f} kt" if g_kt else
              f"- i={i} | wind={speed_kt:5.1f} kt | dir={dir_deg:6.1f}°")

if __name__ == "__main__":
    main()

