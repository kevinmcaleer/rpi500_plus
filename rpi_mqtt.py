#!/usr/bin/env python3
import json
import re
from typing import Tuple, Optional

import paho.mqtt.client as mqtt
from RPiKeyboardConfig import RPiKeyboardConfig

# --- CONFIG ---
MQTT_HOST = "192.168.1.152"
MQTT_PORT = 1883
BASE = "home/keyboard"  # topic root
# ----------------

# ----- Keyboard instance -----
keyboard = RPiKeyboardConfig()

def set_effect(effect: str, *, speed: Optional[int] = None,
               hue: Optional[int] = None, saturation: Optional[int] = None):
    # Note: Effects may need to be implemented differently with the library
    # For now, we'll set direct LED control mode and handle basic effects
    keyboard.set_led_direct_effect()
    if effect.lower() == "clear" or effect.lower() == "off":
        keyboard.rgb_clear()
    # Other effects would need custom implementation

def set_preset_index(index: int):
    # Presets are not directly available in the library API
    # This would need custom implementation based on specific presets
    pass

def list_effects() -> str:
    # Effects list is not available via library, return basic options
    return "clear, solid"

def set_brightness(val: int):
    # Brightness control may need to be implemented by adjusting LED values
    # The library doesn't have a direct brightness method
    # This is a placeholder - you may need to store brightness and apply it to colors
    pass

def set_hue(val: int):
    # Hue control would need to be implemented by setting all LEDs to the hue
    # This is a placeholder for custom implementation
    pass

def leds_clear():
    keyboard.rgb_clear()

def leds_set_all(colour: str):
    # Convert colour string to RGB tuple and set all LEDs
    rgb = _parse_colour_to_rgb(colour)
    # Set direct LED control mode first
    keyboard.set_led_direct_effect()
    # Set all LEDs (Pi 500+ ISO has 85 LEDs)
    for i in range(85):  # Actual number of LEDs for Pi 500+ ISO
        keyboard.set_led_by_idx(idx=i, colour=rgb)
    keyboard.send_leds()

def led_set_rc(row: int, col: int, colour: str):
    # Convert colour string to RGB tuple and set LED by matrix position
    rgb = _parse_colour_to_rgb(colour)
    keyboard.set_led_direct_effect()
    keyboard.set_led_by_matrix(matrix=[row, col], colour=rgb)
    keyboard.send_leds()

def info_ascii() -> str:
    # ASCII layout info is not available via library
    return "Use keyboard.model and keyboard.variant for basic info"

def _clamp(x: int) -> int:
    return max(0, min(255, int(x)))

def _parse_colour_to_rgb(colour: str) -> Tuple[int, int, int]:
    """Convert various color formats to RGB tuple for the library."""

    # Handle JSON format first
    if colour.startswith("{"):
        try:
            obj = json.loads(colour)
            # HSV takes precedence if present
            if all(k in obj for k in ("h", "s", "v")):
                h, s, v = obj["h"] / 255.0, obj["s"] / 255.0, obj["v"] / 255.0
                # HSV to RGB conversion
                if s == 0:
                    r = g = b = v
                else:
                    h *= 6.0
                    i = int(h)
                    f = h - i
                    p = v * (1 - s)
                    q = v * (1 - s * f)
                    t = v * (1 - s * (1 - f))

                    if i == 0:
                        r, g, b = v, t, p
                    elif i == 1:
                        r, g, b = q, v, p
                    elif i == 2:
                        r, g, b = p, v, t
                    elif i == 3:
                        r, g, b = p, q, v
                    elif i == 4:
                        r, g, b = t, p, v
                    else:
                        r, g, b = v, p, q
                return (int(r * 255), int(g * 255), int(b * 255))

            if all(k in obj for k in ("r", "g", "b")):
                return (_clamp(obj["r"]), _clamp(obj["g"]), _clamp(obj["b"]))
        except (json.JSONDecodeError, KeyError):
            pass

    # Handle named colors
    color_map = {
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "white": (255, 255, 255),
        "black": (0, 0, 0),
        "yellow": (255, 255, 0),
        "cyan": (0, 255, 255),
        "magenta": (255, 0, 255),
        "orange": (255, 165, 0),
        "purple": (128, 0, 128),
        "pink": (255, 192, 203),
    }

    if colour.lower() in color_map:
        return color_map[colour.lower()]

    # Handle rgb(r,g,b) format
    if colour.startswith("rgb(") and colour.endswith(")"):
        rgb_str = colour[4:-1]
        parts = [int(x.strip()) for x in rgb_str.split(",")]
        return (parts[0], parts[1], parts[2])

    # Handle HSV h,s,v format - convert to RGB
    if "," in colour and not colour.startswith("rgb"):
        parts = [int(x.strip()) for x in colour.split(",")]
        if len(parts) == 3:
            # Simple HSV to RGB conversion (h, s, v all 0-255)
            h, s, v = parts[0] / 255.0, parts[1] / 255.0, parts[2] / 255.0

            if s == 0:
                r = g = b = v
            else:
                h *= 6.0
                i = int(h)
                f = h - i
                p = v * (1 - s)
                q = v * (1 - s * f)
                t = v * (1 - s * (1 - f))

                if i == 0:
                    r, g, b = v, t, p
                elif i == 1:
                    r, g, b = q, v, p
                elif i == 2:
                    r, g, b = p, v, t
                elif i == 3:
                    r, g, b = p, q, v
                elif i == 4:
                    r, g, b = t, p, v
                else:
                    r, g, b = v, p, q

            return (int(r * 255), int(g * 255), int(b * 255))

    # Handle hex format
    if colour.startswith("#") and len(colour) == 7:
        r = int(colour[1:3], 16)
        g = int(colour[3:5], 16)
        b = int(colour[5:7], 16)
        return (r, g, b)

    # Default to white if we can't parse
    return (255, 255, 255)

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
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
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
