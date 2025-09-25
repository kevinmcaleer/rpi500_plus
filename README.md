# Install

# 1) Install the official firmware + config tool (per docs)
sudo apt update
sudo apt install -y rpi-keyboard-fw-update
sudo rpi-keyboard-fw-update
sudo apt install -y rpi-keyboard-config

# 2) Python deps
sudo apt install -y python3-paho-mqtt

# 3) Run the bridge
python3 keyboard_mqtt.py

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