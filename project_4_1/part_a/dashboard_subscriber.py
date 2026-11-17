#!/usr/bin/env python3
"""Mini Project 4.1 (Part A) - operator dashboard subscriber."""
import argparse
import threading

from mqtt_common import BROKER_HOST, BROKER_PORT, fatal, log, make_client

TOPICS = [("factory/line3/temperature", 1), ("factory/line3/status", 1)]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--client-id", default="line3-dashboard")
    p.add_argument("--duration", type=float, default=0)
    p.add_argument("--topic", action="append")
    a = p.parse_args()

    topics = TOPICS + [(t, 1) for t in (a.topic or [])]
    client = make_client(a.client_id)

    def on_connect(c, userdata, flags, reason_code, properties=None):
        log(f"[dashboard] connected, subscribing to {[t for t, _ in topics]}")
        c.subscribe(topics)

    def on_message(c, userdata, msg):
        tag = "  <-- RETAINED (delivered at subscribe time)" if msg.retain else ""
        log(f"[dashboard] {msg.topic:<32} {msg.payload.decode():>8}  (qos={msg.qos}){tag}")

    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(BROKER_HOST, BROKER_PORT, keepalive=30)
    except OSError as exc:
        fatal(f"cannot reach broker ({exc})")
    client.loop_start()
    try:
        threading.Event().wait(a.duration or None)
    except KeyboardInterrupt:
        pass
    client.disconnect()
    client.loop_stop()


if __name__ == "__main__":
    main()