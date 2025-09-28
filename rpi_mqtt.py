#!/usr/bin/env python3
import json
import os
import re
import subprocess
import time
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
    print(f"[DEBUG] Clearing all LEDs using CLI")
    try:
        result = subprocess.run(['rpi-keyboard-config', 'leds', 'clear'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"[DEBUG] LED clear complete via CLI")
        else:
            print(f"[DEBUG] CLI clear failed: {result.stderr}")
    except Exception as e:
        print(f"[DEBUG] LED clear failed: {e}")
        raise

def leds_set_all_OLD(colour: str):
    # Convert colour string to RGB tuple and set all LEDs
    rgb = _parse_colour_to_rgb(colour)
    print(f"[DEBUG] Setting all LEDs to RGB: {rgb}")

    try:
        # Try with fresh keyboard instance
        print(f"[DEBUG] Creating fresh keyboard instance")
        import os
        print(f"[DEBUG] Current working directory: {os.getcwd()}")
        print(f"[DEBUG] Current user ID: {os.getuid()}")
        print(f"[DEBUG] Environment PATH: {os.environ.get('PATH', 'NOT SET')}")

        fresh_keyboard = RPiKeyboardConfig()
        print(f"[DEBUG] Keyboard instance created successfully")
        print(f"[DEBUG] Keyboard model: {fresh_keyboard.model}")
        print(f"[DEBUG] Keyboard variant: {fresh_keyboard.variant}")

        # Set direct LED control mode first
        print(f"[DEBUG] Setting LED direct effect mode")
        fresh_keyboard.set_led_direct_effect()

        # Let's try the EXACT same approach that worked in direct tests
        print(f"[DEBUG] Using exact same approach as working direct test")
        print(f"[DEBUG] Clearing first...")
        fresh_keyboard.rgb_clear()

        import time
        time.sleep(0.5)

        print(f"[DEBUG] Setting LED direct effect")
        fresh_keyboard.set_led_direct_effect()

        print(f"[DEBUG] Trying the EXACT sequence that worked in direct test")

        # Replicate the exact working test sequence
        print(f"[DEBUG] Step 1: Clear LEDs")
        fresh_keyboard.rgb_clear()

        import time
        time.sleep(0.5)

        print(f"[DEBUG] Step 2: Set direct effect")
        fresh_keyboard.set_led_direct_effect()

        print(f"[DEBUG] Step 3: Set LED 0 to red and send immediately")
        fresh_keyboard.set_led_by_idx(idx=0, colour=(255, 0, 0))
        fresh_keyboard.send_leds()

        time.sleep(2)

        print(f"[DEBUG] Step 4: Try setting first 5 LEDs")
        for i in range(5):
            print(f"[DEBUG] Setting LED {i} to red")
            fresh_keyboard.set_led_by_idx(idx=i, colour=(255, 0, 0))

        fresh_keyboard.send_leds()
        print(f"[DEBUG] First 5 LEDs should be red now!")

        time.sleep(3)

        print(f"[DEBUG] Step 5: Try all LEDs")
        for i in range(85):
            fresh_keyboard.set_led_by_idx(idx=i, colour=(255, 0, 0))

        fresh_keyboard.send_leds()
        print(f"[DEBUG] All LEDs should be red now!")

    except Exception as e:
        print(f"[DEBUG] LED operation failed with fresh instance: {e}")
        print(f"[DEBUG] Trying simple approach with rgb_clear + direct set")
        try:
            # Try a different approach - clear first, then set
            import time
            time.sleep(0.2)

            simple_keyboard = RPiKeyboardConfig()
            simple_keyboard.rgb_clear()
            time.sleep(0.1)
            simple_keyboard.set_led_direct_effect()

            # Set just first few LEDs to test
            for i in range(min(10, 85)):
                simple_keyboard.set_led_by_idx(idx=i, colour=rgb)

            simple_keyboard.send_leds()
            print(f"[DEBUG] LED update completed with simple approach")

        except Exception as e2:
            print(f"[DEBUG] All LED operations failed: {e2}")
            raise

def leds_set_all(colour: str):
    print(f"[DEBUG] Setting all LEDs to color: {colour} using CLI")
    try:

        # Parse color and convert to format for CLI
        if colour.lower() in ["red", "green", "blue", "white", "black", "yellow", "cyan", "magenta", "orange", "purple", "pink"]:
            color_arg = colour.lower()
        elif colour.startswith("#") and len(colour) == 7:
            # Use hex format directly
            color_arg = colour
        elif colour.startswith("rgb("):
            # Extract RGB values and convert to hex
            rgb_str = colour[4:-1]
            parts = [int(x.strip()) for x in rgb_str.split(",")]
            color_arg = f"#{parts[0]:02x}{parts[1]:02x}{parts[2]:02x}"
        else:
            # Default to red if we can't parse
            color_arg = "red"

        # Set to Direct effect mode first for consistent behavior
        effect_result = subprocess.run(['rpi-keyboard-config', 'effect', 'Direct'],
                                     capture_output=True, text=True, timeout=5)
        print(f"[DEBUG] Set Direct effect: {effect_result.returncode}")

        print(f"[DEBUG] Using CLI command: rpi-keyboard-config leds set -c {color_arg}")

        # Skip clear step for faster response - just set the color directly
        result = subprocess.run(['rpi-keyboard-config', 'leds', 'set', '-c', color_arg],
                              capture_output=True, text=True, timeout=5)

        if result.returncode == 0:
            print(f"[DEBUG] CLI rgb-all command successful")
        else:
            print(f"[DEBUG] CLI rgb-all failed: {result.stderr}")

    except Exception as e:
        print(f"[DEBUG] CLI LED operation failed: {e}")
        raise

def led_set_rc(row: int, col: int, colour: str):
    print(f"[DEBUG] Setting LED at row={row}, col={col} to color: {colour} using CLI")
    try:

        # Parse color same as leds_set_all
        if colour.lower() in ["red", "green", "blue", "white", "black", "yellow", "cyan", "magenta", "orange", "purple", "pink"]:
            color_arg = colour.lower()
        elif colour.startswith("#") and len(colour) == 7:
            color_arg = colour
        elif colour.startswith("rgb("):
            rgb_str = colour[4:-1]
            parts = [int(x.strip()) for x in rgb_str.split(",")]
            color_arg = f"#{parts[0]:02x}{parts[1]:02x}{parts[2]:02x}"
        else:
            color_arg = "red"

        # Use row,col format as position
        position = f"{row},{col}"

        # Set to Direct effect mode first to preserve other LEDs
        effect_result = subprocess.run(['rpi-keyboard-config', 'effect', 'Direct'],
                                     capture_output=True, text=True, timeout=5)
        print(f"[DEBUG] Set Direct effect: {effect_result.returncode}")

        print(f"[DEBUG] Using CLI command: rpi-keyboard-config led set {position} -c {color_arg}")

        result = subprocess.run(['rpi-keyboard-config', 'led', 'set', position, '-c', color_arg],
                              capture_output=True, text=True, timeout=5)

        if result.returncode == 0:
            print(f"[DEBUG] CLI individual LED command successful")
        else:
            print(f"[DEBUG] CLI individual LED failed: {result.stderr}")

    except Exception as e:
        print(f"[DEBUG] CLI individual LED operation failed: {e}")
        raise

def info_ascii() -> str:
    # Convert colour string to RGB tuple and set LED by matrix position
    rgb = _parse_colour_to_rgb(colour)
    print(f"[DEBUG] Setting LED at row={row}, col={col} to RGB: {rgb}")

    try:
        # Use fresh keyboard instance
        print(f"[DEBUG] Creating fresh keyboard instance")
        fresh_keyboard = RPiKeyboardConfig()

        print(f"[DEBUG] Setting LED direct effect mode")
        fresh_keyboard.set_led_direct_effect()

        print(f"[DEBUG] Setting LED by matrix position [{row}, {col}]")
        fresh_keyboard.set_led_by_matrix(matrix=[row, col], colour=rgb)

        print(f"[DEBUG] Sending LED data to keyboard")
        fresh_keyboard.send_leds()
        print(f"[DEBUG] LED update complete")

    except Exception as e:
        print(f"[DEBUG] LED operation failed: {e}")
        raise

def info_ascii() -> str:
    # ASCII layout info is not available via library
    return "Use keyboard.model and keyboard.variant for basic info"

def _clamp(x: int) -> int:
    return max(0, min(255, int(x)))

def _rgb_to_keyboard_bgr(r: int, g: int, b: int) -> Tuple[int, int, int]:
    """Convert RGB values to BGR format with proper scaling for keyboard hardware.

    The keyboard uses BGR order and saturates at high intensities.
    Scale down values to prevent saturation to white.
    """
    # Scale down to prevent saturation - max value around 32 works well
    scale_factor = 32 / 255

    scaled_r = int(r * scale_factor)
    scaled_g = int(g * scale_factor)
    scaled_b = int(b * scale_factor)

    # Ensure minimum value of 1 for non-zero inputs to avoid complete darkness
    if r > 0 and scaled_r == 0:
        scaled_r = 1
    if g > 0 and scaled_g == 0:
        scaled_g = 1
    if b > 0 and scaled_b == 0:
        scaled_b = 1

    # Return in BGR order for the keyboard
    return (scaled_b, scaled_g, scaled_r)

def _parse_colour_to_rgb(colour: str) -> Tuple[int, int, int]:
    """Convert various color formats to BGR tuple for the keyboard (which uses BGR, not RGB)."""

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
                r, g, b = int(r * 255), int(g * 255), int(b * 255)
                return _rgb_to_keyboard_bgr(r, g, b)

            if all(k in obj for k in ("r", "g", "b")):
                r, g, b = _clamp(obj["r"]), _clamp(obj["g"]), _clamp(obj["b"])
                return _rgb_to_keyboard_bgr(r, g, b)
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
        r, g, b = color_map[colour.lower()]
        return _rgb_to_keyboard_bgr(r, g, b)

    # Handle rgb(r,g,b) format
    if colour.startswith("rgb(") and colour.endswith(")"):
        rgb_str = colour[4:-1]
        parts = [int(x.strip()) for x in rgb_str.split(",")]
        return _rgb_to_keyboard_bgr(parts[0], parts[1], parts[2])

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

            r, g, b = int(r * 255), int(g * 255), int(b * 255)
            return _rgb_to_keyboard_bgr(r, g, b)

    # Handle hex format
    if colour.startswith("#") and len(colour) == 7:
        r = int(colour[1:3], 16)
        g = int(colour[3:5], 16)
        b = int(colour[5:7], 16)
        return _rgb_to_keyboard_bgr(r, g, b)

    # Default to white if we can't parse
    return _rgb_to_keyboard_bgr(255, 255, 255)

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

    # Debug output for incoming messages
    print(f"[DEBUG] Received message:")
    print(f"  Topic: {topic}. Payload: '{payload}', length: {len(payload)}")
   

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
            print(f"[DEBUG] Processing clear command")
            leds_clear()
            return

        if topic == f"{BASE}/brightness":
            print(f"[DEBUG] Processing brightness command: {payload}")
            set_brightness(int(payload))
            return

        if topic == f"{BASE}/hue":
            print(f"[DEBUG] Processing hue command: {payload}")
            set_hue(int(payload))
            return

        if topic == f"{BASE}/preset/index":
            print(f"[DEBUG] Processing preset index command: {payload}")
            set_preset_index(int(payload))
            return

        if topic == f"{BASE}/effect":
            print(f"[DEBUG] Processing effect command: {payload}")
            if payload.startswith("{"):
                obj = json.loads(payload)
                print(f"[DEBUG] Effect JSON parsed: {obj}")
                set_effect(
                    obj.get("effect", ""),
                    speed=obj.get("speed"),
                    hue=obj.get("hue"),
                    saturation=obj.get("saturation"),
                )
            else:
                print(f"[DEBUG] Effect string: {payload}")
                set_effect(payload)
            return

        if topic == f"{BASE}/led":
            print(f"[DEBUG] Processing LED all command: {payload}")
            colour = parse_colour(payload)
            print(f"[DEBUG] Parsed colour: {colour}")
            leds_set_all(colour)
            return

        # /led/<row,col>
        if len(parts) == 4 and parts[2] == "led" and re.fullmatch(r"\d+,\d+", parts[3]):
            row, col = (int(x) for x in parts[3].split(","))
            print(f"[DEBUG] Processing LED row,col command: row={row}, col={col}, payload={payload}")
            colour = parse_colour(payload)
            print(f"[DEBUG] Parsed colour: {colour}")
            led_set_rc(row, col, colour)
            return

        # /led/key/<KEY>
        if len(parts) == 5 and parts[2] == "led" and parts[3] == "key":
            key = parts[4].upper()
            print(f"[DEBUG] Processing LED key command: key={key}, payload={payload}")
            if key not in KEYMAP:
                print(f"[DEBUG] Unknown key '{key}'. Populate KEYMAP or use row,col.")
                return
            row, col = KEYMAP[key]
            print(f"[DEBUG] Key '{key}' mapped to row={row}, col={col}")
            colour = parse_colour(payload)
            print(f"[DEBUG] Parsed colour: {colour}")
            led_set_rc(row, col, colour)
            return

        print(f"[DEBUG] Unhandled topic: {topic}")

    except Exception as e:
        print(f"[DEBUG] Error processing message: {e}")
        print(f"[DEBUG] Topic: {topic}, Payload: {payload}")

def on_connect(client, userdata, flags, rc):
    print(f"[DEBUG] Connected to MQTT broker with result code {rc}")
    if rc == 0:
        print(f"[DEBUG] Successfully connected to {MQTT_HOST}:{MQTT_PORT}")
    else:
        print(f"[DEBUG] Failed to connect to MQTT broker, result code {rc}")

def main():
    # Check if we have proper permissions
    print(f"[DEBUG] Running as user: {os.getuid()}")

    # Test keyboard access at startup
    print(f"[DEBUG] Testing keyboard access at startup...")
    try:
        keyboard.set_led_direct_effect()
        print(f"[DEBUG] Keyboard access test: SUCCESS")
    except Exception as e:
        print(f"[DEBUG] Keyboard access test: FAILED - {e}")
        print(f"[DEBUG] Try running with: sudo python3 rpi_mqtt.py")

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"[DEBUG] Attempting to connect to MQTT broker at {MQTT_HOST}:{MQTT_PORT}")
    try:
        client.connect(MQTT_HOST, MQTT_PORT, 60)
    except Exception as e:
        print(f"[DEBUG] Connection error: {e}")
        return

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
