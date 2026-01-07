import json
from dotenv import load_dotenv
from rules import find_kite_windows
from test_windy import get_point_forecast

load_dotenv()

def format_window(window):
    start = window[0]
    end = window[-1]
    avg_wind = sum(e["wind_kt"] for e in window) / len(window)

    from datetime import datetime, timezone
    t0 = datetime.fromtimestamp(start["ts"]/1000, tz=timezone.utc)
    t1 = datetime.fromtimestamp(end["ts"]/1000, tz=timezone.utc)

    return (
        f"{t0.strftime('%A')} "
        f"{t0.strftime('%H:%M')}–{t1.strftime('%H:%M')} · "
        f"{avg_wind:.1f} kt · {start['dir_card']}"
    )

def main():
    cfg = json.load(open("config.json", encoding="utf-8"))

    for spot in cfg["spots"]:
        print(f"\n🪁 {spot['name']}")
        data = get_point_forecast(spot["lat"], spot["lon"])

        windows = find_kite_windows(
            data=data,
            spot_cfg=spot,
            min_wind_kt=cfg["min_wind_kt"],
            min_consecutive_points=cfg["min_consecutive_points"],
            weekend_days=cfg["weekend_days"]
        )

        if not windows:
            print("  ❌ Sin ventanas kiteables")
            continue

        for w in windows:
            print("  ✅", format_window(w))

if __name__ == "__main__":
    main()

