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