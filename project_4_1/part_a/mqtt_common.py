"""Shared helpers for Mini Project 4.1 / 4.3 MQTT scripts (paho-mqtt >= 2.0)."""
import datetime as dt
import os
import sys

import paho.mqtt.client as mqtt

BROKER_HOST = os.environ.get("MQTT_HOST", "localhost")
BROKER_PORT = int(os.environ.get("MQTT_PORT", "1883"))


def make_client(client_id: str, clean_session: bool = True) -> mqtt.Client:
    """Create a paho 2.x client (callback API v2, MQTT v3.1.1)."""
    return mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=client_id,
        clean_session=clean_session,
        protocol=mqtt.MQTTv311,
    )


def ts() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def log(msg: str) -> None:
    print(f"[{ts()}] {msg}", flush=True)


def fatal(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr, flush=True)
    sys.exit(1)