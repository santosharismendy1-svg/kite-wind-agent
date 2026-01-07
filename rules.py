import math
from datetime import datetime
from zoneinfo import ZoneInfo

KNOTS_PER_MS = 1.9438444924406
AR_TZ = ZoneInfo("America/Argentina/Buenos_Aires")


def deg_to_compass(deg: float) -> str:
    """
    Convierte grados a rosa de los vientos (8 puntos).
    """
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    ix = int((deg + 22.5) // 45) % 8
    return dirs[ix]


def uv_to_speed_dir(u_ms: float, v_ms: float):
    """
    Windy (Point Forecast) entrega wind como componentes:
      - u: hacia el Este (m/s)
      - v: hacia el Norte (m/s)

    Devuelve:
      - speed_kt: velocidad en nudos
      - dir_deg: dirección meteorológica (de dónde viene) en grados [0..360)
      - dir_card: cardinal (N, NE, E, ...)
    """
    speed_ms = math.sqrt(u_ms * u_ms + v_ms * v_ms)
    speed_kt = speed_ms * KNOTS_PER_MS

    # Dirección "from" meteorológica (de dónde viene):
    # invertimos el vector (u,v) -> (-u,-v)
    dir_rad = math.atan2(-u_ms, -v_ms)
    dir_deg = (math.degrees(dir_rad) + 360) % 360
    dir_card = deg_to_compass(dir_deg)

    return speed_kt, dir_deg, dir_card


def is_weekend(ts_ms: int, weekend_days: list[str]) -> bool:
    """
    ts_ms viene en milisegundos (Windy). Evaluamos el día en horario Argentina.
    weekend_days: ["saturday","sunday"] (lowercase)
    """
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=AR_TZ)
    day = dt.strftime("%A").lower()
    return day in weekend_days


def find_kite_windows(
    data: dict,
    spot_cfg: dict,
    min_wind_kt: float,
    min_consecutive_points: int,
    weekend_days: list[str],
):
    """
    Devuelve una lista de ventanas (cada ventana es una lista de entries consecutivos),
    donde cada entry es kiteable según:
      - wind_kt >= min_wind_kt
      - dir_card dentro de spot_cfg["directions"]
      - y la ventana tiene al menos min_consecutive_points puntos consecutivos.
    """

    ts = data.get("ts", [])
    u = data.get("wind_u-surface", [])
    v = data.get("wind_v-surface", [])

    if not ts or not u or not v:
        return []

    allowed_dirs = set(spot_cfg.get("directions", []))

    windows = []
    current = []

    for i in range(min(len(ts), len(u), len(v))):
        # Solo evaluamos sábado/domingo (en hora Argentina)
        if not is_weekend(ts[i], weekend_days):
            if current:
                windows.append(current)
                current = []
            continue

        if u[i] is None or v[i] is None:
            # Si falta dato, cortamos la continuidad
            if current:
                windows.append(current)
                current = []
            continue

        wind_kt, dir_deg, dir_card = uv_to_speed_dir(u[i], v[i])

        kiteable = (wind_kt >= min_wind_kt) and (dir_card in allowed_dirs)

        entry = {
            "ts": ts[i],
            "wind_kt": wind_kt,
            "dir_deg": dir_deg,
            "dir_card": dir_card,
        }

        if kiteable:
            current.append(entry)
        else:
            if current:
                windows.append(current)
                current = []

    if current:
        windows.append(current)

    # Filtrar por "cantidad de puntos consecutivos"
    valid = [w for w in windows if len(w) >= min_consecutive_points]
    return valid
