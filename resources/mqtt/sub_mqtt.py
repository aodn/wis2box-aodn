#!/usr/bin/env python3
"""
Subscribe to WIS2 wave buoy notifications from the WMO Global Broker.

Usage:
    pip install paho-mqtt
    python3 sub_mqtt.py

The WMO Global Broker publishes WIS2 notifications under the full topic path:
    origin/a/wis2/<centre_id>/data/<policy>/<discipline>/...

For IMOS wave buoys:
    origin/a/wis2/au-imos/data/core/ocean/surface-based-observations/wave-buoys


Messages are saved to OUTPUT_DIR as JSON files named:
    <wigos_station_identifier>-<datetime>.json
"""

import json
import re
import ssl
from pathlib import Path

import paho.mqtt.client as mqtt

# ── Connection settings ────────────────────────────────────────────────────────
BROKER_HOST = "globalbroker.meteo.fr"
BROKER_PORT = 8883
USERNAME = "everyone"
PASSWORD = "everyone"

# WMO Global Broker prefixes the centre topic with origin/a/wis2/
TOPIC = "origin/a/wis2/au-imos/data/core/ocean/surface-based-observations/wave-buoys"

# Directory to save messages
OUTPUT_DIR = Path("mqtt_messages")


def _safe_filename(value: str) -> str:
    """Strip characters that are invalid in filenames."""
    return re.sub(r"[^\w\-]", "_", value)


def _save_message(payload: dict) -> Path:
    """Save payload to OUTPUT_DIR/<station>-<datetime>.json and return the path."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    props = payload.get("properties", {})
    station = props.get("wigos_station_identifier") or payload.get("id", "unknown")
    dt = props.get("datetime") or props.get("pubtime", "unknown")

    filename = OUTPUT_DIR / f"{_safe_filename(station)}-{_safe_filename(dt)}.json"
    filename.write_text(json.dumps(payload, indent=2))
    return filename


# ── Callbacks ──────────────────────────────────────────────────────────────────
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"Connected to {BROKER_HOST}:{BROKER_PORT}")
        print(f"Subscribing to: {TOPIC}")
        print(f"Saving messages to: {OUTPUT_DIR.resolve()}\n")
        client.subscribe(TOPIC)
    else:
        print(f"Connection failed with reason code: {reason_code}")


def on_message(client, userdata, msg):
    print(f"{'─' * 60}")
    print(f"Topic : {msg.topic}")
    try:
        payload = json.loads(msg.payload.decode())
        props = payload.get("properties", {})
        links = payload.get("links", [])

        print(f"ID           : {payload.get('id', 'N/A')}")
        print(f"Station      : {props.get('wigos_station_identifier', 'N/A')}")
        print(f"Datetime     : {props.get('datetime', 'N/A')}")
        print(f"Published at : {props.get('pubtime', 'N/A')}")
        print(f"Data ID      : {props.get('data_id', 'N/A')}")

        canonical = next((l["href"] for l in links if l.get("rel") == "canonical"), None)
        if canonical:
            print(f"Download URL : {canonical}")

        saved = _save_message(payload)
        print(f"Saved        : {saved}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        print(f"Raw payload  : {msg.payload}")


def on_disconnect(client, userdata, flags, reason_code, properties):
    print(f"\nDisconnected (reason code: {reason_code})")


def on_subscribe(client, userdata, mid, reason_code_list, properties):
    print(f"Subscription confirmed (mid={mid}, reason={reason_code_list})\n")


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="aodn-wis2-subscriber",
        clean_session=True,
    )
    client.username_pw_set(USERNAME, PASSWORD)

    # Port 8883 requires TLS
    client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS_CLIENT)

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.on_subscribe = on_subscribe

    print(f"Connecting to {BROKER_HOST}:{BROKER_PORT} ...")
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nStopped by user.")
        client.disconnect()


if __name__ == "__main__":
    main()
