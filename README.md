# Emerald to MQTT Bridge

> Development happens on a private forge; this repository is a read-only mirror. Releases are published here.

This project bridges an Emerald Electricity Advisor to an MQTT broker via a Raspberry Pi using Bluetooth Low Energy (BLE). It reads real-time power usage and pulse data from the Emerald device and publishes it to MQTT for ingestion by Home Assistant.

NOTE THIS IS A WORK IN PROGRESS. WHILE THE SCRIPTS WORK, THE INSTRUCTIONS ARE UNTESTED. USE AT YOUR OWN FRUSTRATION. 
THE FILES HAVE BEEN PULLED FROM MY WORKING ENVIRONMENT AND ARE CONFIRMED FULLY FUNCTIONING.

## Hardware Requirements
* Emerald Electricity Advisor
* Raspberry Pi (Zero 2W or similar) with Bluetooth
* Home Assistant instance with an MQTT Broker

## 1. Raspberry Pi Setup
1. Clone this repository to your Raspberry Pi:

    git clone https://github.com/YOUR_USERNAME/emerald-mqtt-bridge.git
    cd emerald-mqtt-bridge

2. Install the required Python dependencies:

    sudo apt update
    sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 python3-paho-mqtt python3-pytz python3-pydbus

3. Copy `emerald.py` to your preferred directory (e.g., `/home/dietpi/emerald-bridge/`).

## 2. Service Configuration
1. Open `emerald-bridge.service` and edit the `Environment` variables to match your setup:
   * `DEVICE`: The MAC address of your Emerald Advisor.
   * `MQTT_HOSTNAME`: The IP address of your MQTT Broker.
   * `MQTT_BASE_TOPIC`: Base topic for MQTT messages (default: `home/emerald`).
2. Copy the service file to the systemd directory:

    sudo cp emerald-bridge.service /etc/systemd/system/

3. Reload systemd, enable, and start the service:

    sudo systemctl daemon-reload
    sudo systemctl enable emerald-bridge.service
    sudo systemctl start emerald-bridge.service

4. Check the status to ensure it is running:

    sudo systemctl status emerald-bridge.service


## 3. Home Assistant Configuration
Add the configuration from `ha_configuration.yaml` into your Home Assistant `configuration.yaml` file to create the Power and Energy sensors. Restart Home Assistant to apply.


## Acknowledgements
The original Python script and concept are by ElectricBrain (https://www.electricbrain.com.au/). The project site is located at https://www.electricbrain.com.au/pages/rainforest-eagle/emerald-ems-full-hack.php . The original emerald.py was extracted from the Alpine Docker image provided by ElectricBrain at https://hub.docker.com/r/electricbraincontainers/emerald-mqtt. Modifications have been made to support newer `paho-mqtt` callback API versions and to correct byte-shifting index bugs in the payload decoding logic and a duplicate variable call: 
* `MQTT Client Initialization:` The client initialization was updated to mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, self.settings['client_id']) to explicitly define the callback API version.
* `Payload Decoding Fix:` A bug in the byte array indexing was fixed for calculating dataReturned. The first byte shift was corrected from ndata[6] << 24 to ndata[5] << 24.
* `Code Comments:` A comment # FIXED: Uses index 5, 6, 7, 8 was added above the corrected decoding logic.
* `Typo:` The variable declaration gatt_uuid = "" was accidentally duplicated on consecutive lines.  
