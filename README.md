# Install

# 1) Install the official firmware + config tool (per docs)
sudo apt update
sudo apt install -y rpi-keyboard-fw-update
sudo rpi-keyboard-fw-update
sudo apt install -y rpi-keyboard-config

# 2) Set up Python environment

## Option A: System-wide installation (simple)
```bash
sudo apt install -y python3-paho-mqtt
python3 rpi_mqtt.py
```

## Option B: Virtual environment (recommended for development)

### Create virtual environment with system site packages
This is required to access the `rpi-keyboard-config` library which is installed system-wide:
```bash
python3 -m venv --system-site-packages venv
source venv/bin/activate
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run the application
```bash
python3 rpi_mqtt.py
```

### Note about system site packages
The `--system-site-packages` flag is essential because:
- `RPiKeyboardConfig` is installed as a system package via `apt`
- It's not available through PyPI/pip
- Without this flag, the virtual environment cannot access the keyboard library

---

## MQTT Commands

The keyboard MQTT bridge listens to topics under `home/keyboard` and supports the following commands:

### Basic LED Controls

#### Set All LEDs to Same Color
**Topic:** `home/keyboard/led`

**Supported color formats:**
- **Named colors:** `red`, `green`, `blue`, `white`, `black`, `yellow`, `cyan`, `magenta`, `orange`, `purple`, `pink`
- **Hex format:** `#FF0000` (red), `#00FF00` (green), `#0000FF` (blue)
- **RGB format:** `rgb(255,0,0)` or `255,0,0` (comma-separated values)
- **HSV format:** `120,255,255` (hue, saturation, value - all 0-255)
- **JSON RGB:** `{"r":255,"g":0,"b":0}`
- **JSON HSV:** `{"h":120,"s":255,"v":255}`

**Examples:**
```bash
# Set all LEDs to red
mosquitto_pub -h localhost -t "home/keyboard/led" -m "red"
mosquitto_pub -h localhost -t "home/keyboard/led" -m "#FF0000"
mosquitto_pub -h localhost -t "home/keyboard/led" -m "255,0,0"

# Set all LEDs to green using JSON
mosquitto_pub -h localhost -t "home/keyboard/led" -m '{"r":0,"g":255,"b":0}'
```

#### Set Individual LED by Row/Column
**Topic:** `home/keyboard/led/<row>,<col>`

**Examples:**
```bash
# Set LED at row 2, column 6 to blue
mosquitto_pub -h localhost -t "home/keyboard/led/2,6" -m "blue"
mosquitto_pub -h localhost -t "home/keyboard/led/2,6" -m "#0000FF"
```

#### Set Individual LED by Key Name
**Topic:** `home/keyboard/led/key/<KEY>`

**Note:** Requires populating the `KEYMAP` dictionary in the code with key positions.

**Examples:**
```bash
# Set specific keys to colors (requires KEYMAP configuration)
mosquitto_pub -h localhost -t "home/keyboard/led/key/A" -m "red"
mosquitto_pub -h localhost -t "home/keyboard/led/key/ESC" -m "yellow"
```

### Lighting Effects

#### Clear All LEDs
**Topic:** `home/keyboard/clear`

**Examples:**
```bash
# Turn off all LEDs
mosquitto_pub -h localhost -t "home/keyboard/clear" -m ""
```

#### Set Effect
**Topic:** `home/keyboard/effect`

**Supported effects:** `clear`, `off`, `solid`

**Formats:**
- **Simple string:** Effect name only
- **JSON with parameters:** `{"effect":"effectname","speed":140,"hue":120,"saturation":255}`

**Examples:**
```bash
# Simple effect
mosquitto_pub -h localhost -t "home/keyboard/effect" -m "clear"

# Effect with parameters
mosquitto_pub -h localhost -t "home/keyboard/effect" -m '{"effect":"solid","speed":100,"hue":180,"saturation":255}'
```

### Global Controls

#### Set Brightness
**Topic:** `home/keyboard/brightness`
**Value:** Integer 0-255

**Examples:**
```bash
# Set brightness to 50%
mosquitto_pub -h localhost -t "home/keyboard/brightness" -m "128"

# Full brightness
mosquitto_pub -h localhost -t "home/keyboard/brightness" -m "255"
```

#### Set Global Hue
**Topic:** `home/keyboard/hue`
**Value:** Integer 0-255

**Examples:**
```bash
# Set hue to red (0)
mosquitto_pub -h localhost -t "home/keyboard/hue" -m "0"

# Set hue to green (85)
mosquitto_pub -h localhost -t "home/keyboard/hue" -m "85"

# Set hue to blue (170)
mosquitto_pub -h localhost -t "home/keyboard/hue" -m "170"
```

#### Set Preset
**Topic:** `home/keyboard/preset/index`
**Value:** Integer 0-6

**Examples:**
```bash
# Load preset 1
mosquitto_pub -h localhost -t "home/keyboard/preset/index" -m "1"
```

### Testing Connection

You can test if the bridge is working by publishing to any of the topics:

```bash
# Quick test - turn all LEDs red
mosquitto_pub -h 192.168.1.152 -t "home/keyboard/led" -m "red"

# Turn off all LEDs
mosquitto_pub -h 192.168.1.152 -t "home/keyboard/clear" -m ""
```

### Configuration

- **MQTT Broker:** `192.168.1.152:1883` (configured in `rpi_mqtt.py`)
- **Base Topic:** `home/keyboard`
- **Debug Output:** All received messages are logged with detailed debugging information

---

## Install as a service

Save to `/etc/systemd/system/keyboard-mqtt.service`

```ini
[Unit]
Description=MQTT bridge for Raspberry Pi 500+ keyboard LEDs
After=network-online.target mosquitto.service
Wants=network-online.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/keyboard_mqtt.py
User=pi
Group=pi
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

---

## Install with 
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now keyboard-mqtt.service
```

---