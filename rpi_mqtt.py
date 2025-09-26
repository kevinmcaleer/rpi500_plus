#!/usr/bin/env python3
import json
import re
import shlex
import subprocess
from typing import Tuple, Optional

import paho.mqtt.client as mqtt

# --- CONFIG ---
MQTT_HOST = "192.168.1.152"
MQTT_PORT = 1883
BASE = "home/keyboard"  # topic root
# ----------------

# ----- Helpers around the official CLI -----
CLI = "rpi-keyboard-config"

def _run(args: list[str]) -> str:
    """Run rpi-keyboard-config with args and return stdout (strip trailing newline)."""
    res = subprocess.run([CLI, *args], check=True, capture_output=True, text=True)
    return res.stdout.strip()

def set_effect(effect: str, *, speed: Optional[int] = None,
               hue: Optional[int] = None, saturation: Optional[int] = None):
    args = ["effect", effect]
    if speed is not None:
        args += ["--speed", str(_clamp(speed))]
    if hue is not None:
        args += ["--hue", str(_clamp(hue))]
    if saturation is not None:
        args += ["--saturation", str(_clamp(saturation))]
    _run(args)

def set_preset_index(index: int):
    _run(["preset", "index", str(index)])

def list_effects() -> str:
    return _run(["list-effects"])

def set_brightness(val: int):
    # 0..255
    _run(["brightness", str(_clamp(val))])

def set_hue(val: int):
    # 0..255
    _run(["hue", str(_clamp(val))])

def leds_clear():
    _run(["leds", "clear"])

def leds_set_all(colour: str):
    # colour: name ("red"), HSV "h,s,v" (0..255), or RGB "rgb(r,g,b)"
    _run(["leds", "set", "--colour", colour])

def led_set_rc(row: int, col: int, colour: str):
    # colour formats as above; row/col are integers
    _run(["led", "set", f"{row},{col}", "--colour", colour])

def info_ascii() -> str:
    # Useful to see row/col mapping
    return _run(["info", "--ascii"])

def _clamp(x: int) -> int:
    return max(0, min(255, int(x)))

# ----- MQTT glue -----

def parse_colour(payload: str) -> str:
    """
    Accept:
      - common names: "red"
      - hex: "#RRGGBB"
      - CSV: "r,g,b"
      - JSON: {"r":255,"g":0,"b":0} or {"h":0,"s":255,"v":255}
      - HSV CSV: "h,s,v"  (0..255)
    Returns a CLI-friendly string: either 'rgb(r,g,b)' or 'h,s,v' or a named colour.
    """
    p = payload.strip()

    # JSON?
    if p.startswith("{"):
        obj = json.loads(p)
        # HSV takes precedence if present
        if all(k in obj for k in ("h", "s", "v")):
            return f'{_clamp(obj["h"])},{_clamp(obj["s"])},{_clamp(obj["v"])}'
        if all(k in obj for k in ("r", "g", "b")):
            return f'rgb({_clamp(obj["r"])},{_clamp(obj["g"])},{_clamp(obj["b"])})'
        raise ValueError("JSON must be RGB or HSV")

    # Hex?
    if p.startswith("#") and len(p) == 7 and re.fullmatch(r"#[0-9a-fA-F]{6}", p):
        r = int(p[1:3], 16)
        g = int(p[3:5], 16)
        b = int(p[5:7], 16)
        return f"rgb({r},{g},{b})"

    # CSV?
    if "," in p:
        parts = [x.strip() for x in p.split(",")]
        if len(parts) != 3:
            raise ValueError("Colour CSV must have 3 numbers")
        nums = tuple(int(x) for x in parts)
        # Heuristic: if any > 1 and <=255, assume HSV unless prefixed as rgb()
        if all(0 <= n <= 255 for n in nums):
            # prefer HSV form for CLI (docs examples show HSV),
            # but allow 'rgb()' if explicitly requested upstream.
            return f"{nums[0]},{nums[1]},{nums[2]}"
        raise ValueError("CSV numbers must be 0..255")

    # Fallback: treat as a named colour (e.g., "red")
    if re.fullmatch(r"[A-Za-z]+", p):
        return p

    raise ValueError("Unsupported colour format")

# Optional: map keys → (row,col). Populate this as you like.
# Tip: run `rpi-keyboard-config info --ascii` to see positions, then fill below.
KEYMAP: dict[str, tuple[int,int]] = {
    # "ESC": (1, 1),
    # "F1": (1, 3),
    # "A": (4, 2),
    # ... fill to taste
}

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode("utf-8").strip()

    try:
        # Topics:
        #  - {BASE}/led → set whole keyboard colour
        #  - {BASE}/led/row,col → set one LED by row,col (e.g., "2,6")
        #  - {BASE}/led/key/KEY → set one LED by key label using KEYMAP (e.g., "A", "ESC")
        #  - {BASE}/clear → turn off all LEDs
        #  - {BASE}/brightness → 0..255
        #  - {BASE}/hue → 0..255
        #  - {BASE}/effect → effect name (string); optional JSON {"effect":"Cycle Spiral","speed":140}
        #  - {BASE}/preset/index → 0..6
        parts = topic.split("/")

        if topic == f"{BASE}/clear":
            leds_clear()
            return

        if topic == f"{BASE}/brightness":
            set_brightness(int(payload))
            return

        if topic == f"{BASE}/hue":
            set_hue(int(payload))
            return

        if topic == f"{BASE}/preset/index":
            set_preset_index(int(payload))
            return

        if topic == f"{BASE}/effect":
            if payload.startswith("{"):
                obj = json.loads(payload)
                set_effect(
                    obj.get("effect", ""),
                    speed=obj.get("speed"),
                    hue=obj.get("hue"),
                    saturation=obj.get("saturation"),
                )
            else:
                set_effect(payload)
            return

        if topic == f"{BASE}/led":
            colour = parse_colour(payload)
            leds_set_all(colour)
            return

        # /led/<row,col>
        if len(parts) == 4 and parts[2] == "led" and re.fullmatch(r"\d+,\d+", parts[3]):
            row, col = (int(x) for x in parts[3].split(","))
            colour = parse_colour(payload)
            led_set_rc(row, col, colour)
            return

        # /led/key/<KEY>
        if len(parts) == 5 and parts[2] == "led" and parts[3] == "key":
            key = parts[4].upper()
            if key not in KEYMAP:
                print(f"Unknown key '{key}'. Populate KEYMAP or use row,col.")
                return
            row, col = KEYMAP[key]
            colour = parse_colour(payload)
            led_set_rc(row, col, colour)
            return

        print(f"Unhandled topic: {topic}")

    except Exception as e:
        print("Error:", e)

def main():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT, 60)

    # Subscriptions
    subs = [
        f"{BASE}/led",
        f"{BASE}/led/#",
        f"{BASE}/clear",
        f"{BASE}/brightness",
        f"{BASE}/hue",
        f"{BASE}/effect",
        f"{BASE}/preset/index",
    ]
    for t in subs:
        client.subscribe(t)

    print("Connected. Try publishing to topics under:", BASE)
    client.loop_forever()

if __name__ == "__main__":
    main()
