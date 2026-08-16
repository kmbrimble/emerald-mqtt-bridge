# Emerald to MQTT Bridge

This project bridges an Emerald Electricity Advisor to an MQTT broker via a Raspberry Pi using Bluetooth Low Energy (BLE). It reads real-time power usage and pulse data from the Emerald device and publishes it to MQTT for ingestion by Home Assistant.

## Hardware Requirements
* Emerald Electricity Advisor
* Raspberry Pi (Zero 2W or similar) with Bluetooth
* Home Assistant instance with an MQTT Broker

## 1. Raspberry Pi Setup
1. Clone this repository to your Raspberry Pi:
   ```bash
   git clone [https://github.com/YOUR_USERNAME/emerald-mqtt-bridge.git](https://github.com/YOUR_USERNAME/emerald-mqtt-bridge.git)
   cd emerald-mqtt-bridge
   ```
2. Install the required Python dependencies:
   ```bash
   sudo apt update
   sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 python3-paho-mqtt python3-pytz python3-pydbus
   ```
3. Copy `emerald.py` to your preferred directory (e.g., `/home/dietpi/emerald-bridge/`).

## 2. Service Configuration
1. Open `emerald-bridge.service` and edit the `Environment` variables to match your setup:
   * `DEVICE`: The MAC address of your Emerald Advisor.
   * `MQTT_HOSTNAME`: The IP address of your MQTT Broker.
   * `MQTT_BASE_TOPIC`: Base topic for MQTT messages (default: `home/emerald`).
2. Copy the service file to the systemd directory:
   ```bash
   sudo cp emerald-bridge.service /etc/systemd/system/
   ```
3. Reload systemd, enable, and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable emerald-bridge.service
   sudo systemctl start emerald-bridge.service
   ```
4. Check the status to ensure it is running:
   ```bash
   sudo systemctl status emerald-bridge.service
   ```

## 3. Home Assistant Configuration
Add the configuration from `ha_configuration.yaml` into your Home Assistant `configuration.yaml` file to create the Power and Energy sensors. Restart Home Assistant to apply.