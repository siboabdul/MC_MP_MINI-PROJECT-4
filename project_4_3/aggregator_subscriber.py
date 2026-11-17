#!/usr/bin/env python3
"""Mini Project 4.3 - aggregator/logger subscriber.

Single wildcard subscription 'plant1/+/+' captures every reading.
Per-topic thresholds. Periodic summary. Optional JSON log file.
"""
import argparse
import datetime as dt
import json
import threading
import time
from collections import defaultdict
from pathlib import Path

from mqtt_common import BROKER_HOST, BROKER_PORT, fatal, log, make_client

THRESHOLDS = {
    "temperature": 40.0,
    "vibration":   4.0,
    "humidity":    85.0,
}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--subscription", default="plant1/+/+")
    p.add_argument("--summary-interval", type=float, default=15.0)
    p.add_argument("--log-file", type=Path, default=None)
    p.add_argument("--client-id", default="plant1-aggregator")
    p.add_argument("--duration", type=float, default=0)
    a = p.parse_args()

    client = make_client(a.client_id)
    latest: dict[str, tuple[str, str]] = {}   # topic -> (value, timestamp)
    alerts: list[dict] = []
    lock = threading.Lock()
    log_file = a.log_file
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_file.write_text("")

    def on_connect(c, userdata, flags, reason_code, properties=None):
        log(f"[agg] connected, wildcard subscription '{a.subscription}'")
        c.subscribe(a.subscription, qos=1)

    def on_message(c, userdata, msg):
        ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        payload = msg.payload.decode()
        with lock:
            latest[msg.topic] = (payload, ts)
        retained = " RETAINED" if msg.retain else ""
        log(f"[agg] {msg.topic:<38} {payload:>8}  (qos={msg.qos}){retained}")
        if log_file:
            with log_file.open("a") as f:
                f.write(json.dumps({"ts": ts, "topic": msg.topic, "payload": payload,
                                    "qos": msg.qos, "retained": msg.retain}) + "\n")
        # threshold alerting
        measure = msg.topic.rsplit("/", 1)[-1]
        limit = THRESHOLDS.get(measure)
        if limit is None:
            return
        try:
            val = float(payload)
        except ValueError:
            return
        if val > limit:
            alerts.append({"ts": ts, "topic": msg.topic, "value": val, "limit": limit})
            log(f"[agg] *** ALERT *** {msg.topic} = {val} > {limit}")

    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(BROKER_HOST, BROKER_PORT, keepalive=30)
    except OSError as exc:
        fatal(f"cannot reach broker: {exc}")
    client.loop_start()

    stop = threading.Event()
    start = time.time()
    try:
        while not stop.is_set():
            stop.wait(a.summary_interval)
            with lock:
                log("[agg] --- summary ---")
                for t, (v, ts) in sorted(latest.items()):
                    log(f"[agg]   {t:<38} {v:>8}  (last {ts})")
            if a.duration and time.time() - start > a.duration:
                break
    except KeyboardInterrupt:
        pass

    client.disconnect()
    client.loop_stop()
    log(f"[agg] {len(alerts)} alert(s) total")


if __name__ == "__main__":
    main()