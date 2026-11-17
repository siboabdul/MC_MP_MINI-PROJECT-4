# Mobile Communications — Mini Projects (Unit 4)

Implementation for the three Unit-4 mini projects in the Mobile Communications lab manual:

- **4.1 — MQTT Publish/Subscribe + LPWAN Link-Budget Comparison**
  - Part A: an MQTT publisher, a dashboard subscriber, and a threshold-alert subscriber, demonstrating QoS, retained messages, and Last Will and Testament (LWT).
  - Part B: a link-budget and battery-life comparison of NB-IoT, LTE-M CE Mode B, and LoRaWAN SF12 for a 200-sensor precision-agriculture deployment.
- **4.2 — Rule-Based IoT Connectivity Technology Selector** — scores NB-IoT, LTE-M, LoRaWAN, 5G RedCap, and BLE/Zigbee against six requirement axes and produces a ranked recommendation.
- **4.3 — Multi-Sensor MQTT Monitoring Dashboard** — several publishers on a shared topic hierarchy, one wildcard aggregator, per-topic alerting, retained message, and LWT.

## Requirements

- **Python 3.9 or newer** (only the standard library plus one MQTT package is used).
- **`paho-mqtt >= 2.0`** (`pip install paho-mqtt`).
- Optional: a **local Mosquitto broker** or a **public test broker** (e.g. `test.mosquitto.org`, `broker.hivemq.com`).

No numpy, pandas, or matplotlib is needed.

## Repository layout
