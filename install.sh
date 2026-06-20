#!/bin/bash
set -e

echo "====================================================="
echo "   Raspberry Pi HA Edge Agent - One-Click Installer  "
echo "====================================================="

# Check if running as root
CURRENT_USER=$(whoami)
if [ "$CURRENT_USER" = "root" ]; then
    echo "❌ Please run this script as your normal user (not root/sudo)!"
    exit 1
fi

INSTALL_DIR="$HOME/pi_ha_agent"
VENV_DIR="$INSTALL_DIR/.venv"

echo "➡️  Step 1: Downloading repository..."
if [ -d "$INSTALL_DIR" ]; then
    echo "Directory $INSTALL_DIR already exists. Updating..."
    cd "$INSTALL_DIR"
    git pull
else
    git clone https://github.com/chihchun98/RaspberryPi-HA-Agen.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

echo "➡️  Step 2: Setting up Python virtual environment..."
sudo apt-get update -y
sudo apt-get install -y python3-venv python3-pip git
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install -r pi_agent_server/requirements.txt
"$VENV_DIR/bin/pip" install paho-mqtt RPi.GPIO

echo "➡️  Step 3: Configuring sudo permissions for USB auto-mount..."
sudo cp pi_agent_sudoers /etc/sudoers.d/pi_agent
sudo chmod 0440 /etc/sudoers.d/pi_agent

echo "➡️  Step 4: Creating system background services..."

# Create pi_agent.service dynamically to match the current user
cat <<EOF | sudo tee /etc/systemd/system/pi_agent.service > /dev/null
[Unit]
Description=Raspberry Pi Agent for Home Assistant
After=network.target docker.service

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$INSTALL_DIR/pi_agent_server
ExecStart=$VENV_DIR/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Create pi_mqtt_gpio.service
# Note: GPIO often needs root access, so User=root is used here
cat <<EOF | sudo tee /etc/systemd/system/pi_mqtt_gpio.service > /dev/null
[Unit]
Description=MQTT GPIO Agent for HA
After=network.target docker.service

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=$VENV_DIR/bin/python $INSTALL_DIR/pi_mqtt_gpio.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "➡️  Step 5: Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable --now pi_agent.service
sudo systemctl enable --now pi_mqtt_gpio.service

echo "====================================================="
echo " 🎉 Installation Complete! "
echo " 1. The Pi Agent API is running on port 8001"
echo " 2. GPIO MQTT Bridge is running in the background"
echo " 3. USB hot-plug detection is active"
echo "====================================================="
