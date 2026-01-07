import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

from test_windy import get_point_forecast
from rules import find_kite_windows
from emailer import send_email

AR_TZ = ZoneInfo("America/Argentina/Buenos_Aires")


def fmt_window(window):
    start = window[0]
    end = window[-1]
    avg = sum(e["wind_kt"] for e in window) / len(window)

    t0 = datetime.fromtimestamp(start["ts"] / 1000, tz=AR_TZ)
    t1 = datetime.fromtimestamp(end["ts"] / 1000, tz=AR_TZ)

    # Sumamos el paso de tiempo aproximado para que el "end" no quede igual al último punto
    # (GFS suele ser cada 3h). Si querés, luego lo hacemos exacto leyendo el delta real.
    return f"{t0.strftime('%A %H:%M')}–{t1.strftime('%H:%M')} · {avg:.1f} kt · {start['dir_card']} · ({len(window)} puntos)"


def build_report(cfg):
    any_windows = False
    lines = []
    lines.append("🪁 Kite Alert (Twintip) — Ventanas kiteables del fin de semana\n")

    for spot in cfg["spots"]:
        data = get_point_forecast(spot["lat"], spot["lon"])
        windows = find_kite_windows(
            data=data,
            spot_cfg=spot,
            min_wind_kt=cfg["min_wind_kt"],
            min_consecutive_points=cfg["min_consecutive_points"],
            weekend_days=cfg["weekend_days"],
        )

        if windows:
            any_windows = True
            lines.append(f"{spot['name']}")
            for w in windows:
                lines.append(f"  ✅ {fmt_window(w)}")
            lines.append("")  # blank line
        else:
            # No listamos spots sin ventanas (para que el mail sea corto)
            pass

    return any_windows, "\n".join(lines).strip() + "\n"


def main():
    load_dotenv()

    cfg = json.load(open("config.json", encoding="utf-8"))
    has_windows, report = build_report(cfg)

    if not has_windows:
        print("🤫 No hay ventanas kiteables — no se envía email.")
        return

    subject = "🪁 Kite Alert — Hay viento el fin de semana"
    send_email(subject, report)
    print("✅ Email enviado.")


if __name__ == "__main__":
    main()
