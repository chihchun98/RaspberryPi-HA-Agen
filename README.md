# RaspberryPi-HA-Agent

A lightweight and practical edge agent for Raspberry Pi that bridges Docker containers, dynamic USB mounts, and GPIO to Home Assistant via auto-discovery.

## 🌟 Overview

When using a Raspberry Pi as an edge node or peripheral device for a main Home Assistant server, it can be difficult to monitor Docker containers, safely mount/unmount USB drives, and control GPIO pins without writing messy one-off scripts. 

**RaspberryPi-HA-Agent** is an all-in-one, plug-and-play solution. It acts as an intelligent bridge between the Raspberry Pi's hardware/OS layer and Home Assistant.

## ✨ Core Features

*   🐳 **Docker Integration**: Automatically detects running Docker containers (e.g., `mosquitto`, `portainer`) and exposes them as switch entities in Home Assistant. You can start/stop containers directly from the HA UI.
*   💾 **Dynamic USB Storage (Hot-plug & Self-Healing)**: 
    *   Automatically detects when a new USB hard drive is plugged in.
    *   Exposes a switch in HA. Turning it ON safely mounts the drive with root permissions (via carefully scoped `sudoers`); turning it OFF unmounts it safely.
    *   **Self-Healing Ghost Cleanup**: If the Pi loses power or the drive is unplugged ungracefully, the agent automatically detects orphaned mount points and wipes them, preventing read-only filesystem locks.
*   🔌 **GPIO via MQTT Auto-Discovery**: Includes a lightweight Python script (`pi_mqtt_gpio.py`) that maps Raspberry Pi GPIO pins to an MQTT broker. It automatically publishes HA Discovery payloads so your GPIO pins instantly pop up as controllable switches in Home Assistant.
*   🔄 **Real-Time Auto-Discovery**: Uses Home Assistant's `DataUpdateCoordinator`. If you run a new Docker container or plug in a new USB drive, a new switch will automatically appear on your HA dashboard within 10 seconds. No code changes required!
*   🌡️ **Hardware Metrics**: Real-time reporting of CPU usage, RAM usage, and CPU temperature.

## 🏗️ Architecture

This repository consists of three main parts:

1.  **`pi_agent_server/` (The Edge Agent)**: A lightweight Python FastAPI server running as a `systemd` background service on the Raspberry Pi. It polls system stats, `lsblk` for USBs, and Docker status.
2.  **`custom_components/pi_agent/` (The HA Integration)**: A custom component for Home Assistant that dynamically communicates with the Edge Agent REST API and handles Entity Registry creation/deletion.
3.  **`pi_mqtt_gpio.py` (The MQTT Bridge)**: A standalone `systemd` service that bridges `RPi.GPIO` to MQTT, supporting HA Auto-Discovery.

## 🚀 Quick Setup Overview

1.  **On the Raspberry Pi (One-Click Install)**:
    Just run the following command in your Raspberry Pi terminal to automatically download, install dependencies, setup sudoers, and start the background services:
    ```bash
    curl -sSL https://raw.githubusercontent.com/chihchun98/RaspberryPi-HA-Agen/main/install.sh | bash
    ```
2.  **On Home Assistant**:
    *   Copy the `custom_components/pi_agent` folder into your HA `config/custom_components` directory.
    *   Restart Home Assistant.
    *   Go to **Settings -> Devices & Services -> Add Integration**, search for "Raspberry Pi Agent", and enter your Pi's IP address.
3.  **MQTT (Optional but recommended for GPIO)**:
    *   Ensure an MQTT broker (like Mosquitto) is running.
    *   The `pi_mqtt_gpio.py` script will automatically populate the MQTT integration in HA with the configured GPIO pins.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

## 📄 License

This project is open-source and available under the MIT License.
