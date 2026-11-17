#!/usr/bin/env python3
"""Mini Project 4.1 (Part A) - threshold alerting on a wildcard subscription."""
import argparse
import threading

from mqtt_common import BROKER_HOST, BROKER_PORT, fatal, log, make_client


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--subscription", default="factory/+/temperature")
    p.add_argument("--threshold", type=float, default=90.0)
    p.add_argument("--humidity-threshold", type=float, default=80.0)
    p.add_argument("--duration", type=float, default=0)
    p.add_argument("--client-id", default="line3-alert")
    p.add_argument("--verbose", action="store_true")
    a = p.parse_args()

    thresholds = {"temperature": a.threshold, "humidity": a.humidity_threshold}
    client = make_client(a.client_id)

    def on_connect(c, userdata, flags, reason_code, properties=None):
        log(f"[alert] connected, subscription '{a.subscription}', thresholds {thresholds}")
        c.subscribe(a.subscription, qos=1)

    def on_message(c, userdata, msg):
        measurement = msg.topic.rsplit("/", 1)[-1]
        try:
            value = float(msg.payload.decode())
        except ValueError:
            if a.verbose:
                log(f"[alert] ignored non-numeric {msg.topic} = {msg.payload.decode()!r}")
            return
        limit = thresholds.get(measurement)
        if limit is not None and value > limit:
            log(f"[alert] ALERT {msg.topic} = {value:.1f} exceeds {limit:.1f}")
        elif a.verbose:
            log(f"[alert] ok    {msg.topic} = {value:.1f}")

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