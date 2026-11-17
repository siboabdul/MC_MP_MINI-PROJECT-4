#!/usr/bin/env python3
"""Mini Project 4.1 (Part A) - simulated temperature / humidity sensor publisher."""
import argparse
import random
import signal
import threading
import time

from mqtt_common import BROKER_HOST, BROKER_PORT, fatal, log, make_client

RANGES = {"temperature": (60.0, 95.0), "humidity": (30.0, 90.0)}
DEFAULT_IDS = {"temperature": "line3-temp-sensor", "humidity": "line3-humidity-sensor"}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--measurement", choices=RANGES, default="temperature")
    p.add_argument("--client-id")
    p.add_argument("--interval", type=float, default=5.0)
    p.add_argument("--qos", type=int, choices=(0, 1, 2), default=1)
    p.add_argument("--count", type=int, default=0)
    p.add_argument("--keepalive", type=int, default=5)
    p.add_argument("--retain-all", action="store_true")
    p.add_argument("--no-offline-on-exit", action="store_true")
    p.add_argument("--seed", type=int)
    a = p.parse_args()

    if a.seed is not None:
        random.seed(a.seed)
    client_id = a.client_id or DEFAULT_IDS[a.measurement]
    topic = f"factory/line3/{a.measurement}"
    status_topic = "factory/line3/status" if a.measurement == "temperature" else f"factory/line3/{a.measurement}_status"
    lo, hi = RANGES[a.measurement]

    client = make_client(client_id)
    connected = threading.Event()

    def on_connect(c, userdata, flags, reason_code, properties=None):
        if reason_code != 0:
            log(f"connection refused: {reason_code}")
            return
        log(f"connected to {BROKER_HOST}:{BROKER_PORT} as '{client_id}'")
        c.publish(status_topic, "online", qos=1, retain=True)
        log(f"PUBLISH {status_topic} = online (retain)")
        connected.set()

    def on_disconnect(c, userdata, flags, reason_code, properties=None):
        connected.clear()
        log(f"disconnected (reason={reason_code})")

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.will_set(status_topic, payload="offline", qos=1, retain=True)
    client.reconnect_delay_set(min_delay=1, max_delay=2)

    try:
        client.connect(BROKER_HOST, BROKER_PORT, keepalive=a.keepalive)
    except OSError as exc:
        fatal(f"cannot reach broker {BROKER_HOST}:{BROKER_PORT} ({exc}). Start Mosquitto first.")
    client.loop_start()

    stop = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    signal.signal(signal.SIGTERM, lambda *_: stop.set())

    if not connected.wait(10):
        fatal("no CONNACK within 10 s")

    n = 0
    while not stop.is_set():
        value = round(random.uniform(lo, hi), 1)
        retain = a.retain_all or n == 0
        client.publish(topic, f"{value:.1f}", qos=a.qos, retain=retain)
        log(f"PUBLISH {topic} = {value:.1f} (qos={a.qos}{', retain' if retain else ''})")
        n += 1
        if a.count and n >= a.count:
            break
        stop.wait(a.interval)

    if a.no_offline_on_exit:
        log("clean disconnect - LWT will NOT fire, retained status stays 'online'")
    else:
        info = client.publish(status_topic, "offline", qos=1, retain=True)
        info.wait_for_publish(2)
        log(f"PUBLISH {status_topic} = offline (explicit, graceful shutdown)")
    client.disconnect()
    client.loop_stop()


if __name__ == "__main__":
    main()