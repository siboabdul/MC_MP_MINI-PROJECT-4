#!/usr/bin/env python3
"""Mini Project 4.3 - multi-sensor MQTT publisher.

Publishes one measurement on a shared hierarchy (plant1/lineX/measurement).
Run several instances with different --location / --measurement / --client-id.
"""
import argparse
import random
import signal
import threading

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "project_4_1" / "part_a"))

from mqtt_common import BROKER_HOST, BROKER_PORT, fatal, log, make_client

RANGES = {
    "temperature": (20.0, 45.0),
    "vibration":   (0.0, 5.0),
    "humidity":    (30.0, 90.0),
}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--location", default="plant1/lineA")
    p.add_argument("--measurement", default="temperature", choices=RANGES)
    p.add_argument("--client-id", required=True)
    p.add_argument("--interval", type=float, default=3.0)
    p.add_argument("--qos", type=int, choices=(0, 1, 2), default=1)
    p.add_argument("--with-lwt", action="store_true", help="register LWT on <location>/<measurement>/status")
    p.add_argument("--retain-all", action="store_true")
    p.add_argument("--seed", type=int)
    a = p.parse_args()

    if a.seed is not None:
        random.seed(a.seed)
    topic = f"{a.location}/{a.measurement}"
    status_topic = f"{a.location}/{a.measurement}/status"
    lo, hi = RANGES[a.measurement]

    client = make_client(a.client_id)
    connected = threading.Event()

    def on_connect(c, userdata, flags, reason_code, properties=None):
        if reason_code != 0:
            log(f"connection refused: {reason_code}")
            return
        log(f"[{a.client_id}] connected, publishing on {topic}")
        c.publish(status_topic, "online", qos=1, retain=True)
        connected.set()

    client.on_connect = on_connect
    if a.with_lwt:
        client.will_set(status_topic, payload="offline", qos=1, retain=True)

    try:
        client.connect(BROKER_HOST, BROKER_PORT, keepalive=5)
    except OSError as exc:
        fatal(f"cannot reach broker: {exc}")
    client.loop_start()

    stop = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    if not connected.wait(10):
        fatal("no CONNACK")

    n = 0
    while not stop.is_set():
        v = round(random.uniform(lo, hi), 2)
        retain = a.retain_all or n == 0
        client.publish(topic, f"{v}", qos=a.qos, retain=retain)
        log(f"[{a.client_id}] PUBLISH {topic} = {v} (qos={a.qos}{', retain' if retain else ''})")
        n += 1
        stop.wait(a.interval)

    # clean shutdown -> explicit offline
    info = client.publish(status_topic, "offline", qos=1, retain=True)
    info.wait_for_publish(2)
    client.disconnect()
    client.loop_stop()


if __name__ == "__main__":
    main()