#!/usr/bin/env python3
"""
Subscribe to WIS2 notifications from the WMO Global Broker (or any MQTT broker).

Usage:
    pip install paho-mqtt
    python3 sub_mqtt.py [OPTIONS]

Examples:
    # Use defaults (WMO Global Broker, IMOS wave buoys topic)
    python3 sub_mqtt.py

    # Connect to IMOS edge broker (no TLS, port 1883)
    python3 sub_mqtt.py --host wis2box-broker.edge.aodn.org.au --port 1883 \\
        --username wis2box --password <secret> --no-tls

    # Subscribe to all IMOS topics
    python3 sub_mqtt.py --topic "origin/a/wis2/au-imos/#"

    # Subscribe to all WIS2 topics worldwide
    python3 sub_mqtt.py --topic "origin/a/wis2/#"

    # Custom output directory
    python3 sub_mqtt.py --output-dir /tmp/mqtt_messages

Messages are saved to --output-dir as JSON files named:
    <wigos_station_identifier>-<datetime>.json
"""

import argparse
import json
import re
import ssl
from pathlib import Path

import paho.mqtt.client as mqtt

# ── Defaults ───────────────────────────────────────────────────────────────────
DEFAULT_HOST = "globalbroker.meteo.fr"
DEFAULT_PORT = 8883
DEFAULT_USERNAME = "everyone"
DEFAULT_PASSWORD = "everyone"
DEFAULT_TOPIC = "origin/a/wis2/au-imos/data/core/ocean/surface-based-observations/wave-buoys"
DEFAULT_OUTPUT_DIR = "mqtt_messages"


def _safe_filename(value: str) -> str:
    """Replace characters that are invalid in filenames."""
    return re.sub(r"[^\w\-]", "_", value)


def _save_message(payload: dict, output_dir: Path) -> Path:
    """Save payload to output_dir/<station>-<datetime>.json and return the path."""
    output_dir.mkdir(parents=True, exist_ok=True)

    props = payload.get("properties", {})
    station = props.get("wigos_station_identifier") or payload.get("id", "unknown")
    dt = props.get("datetime") or props.get("pubtime", "unknown")

    filename = output_dir / f"{_safe_filename(station)}-{_safe_filename(dt)}.json"
    filename.write_text(json.dumps(payload, indent=2))
    return filename


# ── Callbacks ──────────────────────────────────────────────────────────────────
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"Connected to {userdata['host']}:{userdata['port']}")
        print(f"Subscribing to : {userdata['topic']}")
        print(f"Saving to      : {userdata['output_dir'].resolve()}\n")
        client.subscribe(userdata["topic"])
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

        saved = _save_message(payload, userdata["output_dir"])
        print(f"Saved        : {saved}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        print(f"Raw payload  : {msg.payload}")


def on_disconnect(client, userdata, flags, reason_code, properties):
    print(f"\nDisconnected (reason code: {reason_code})")


def on_subscribe(client, userdata, mid, reason_code_list, properties):
    print(f"Subscription confirmed (mid={mid}, reason={reason_code_list})\n")


# ── CLI ────────────────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Subscribe to WIS2 MQTT notifications and save messages to JSON files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--host", default=DEFAULT_HOST,
                        help="MQTT broker hostname")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help="MQTT broker port")
    parser.add_argument("--username", default=DEFAULT_USERNAME,
                        help="MQTT username")
    parser.add_argument("--password", default=DEFAULT_PASSWORD,
                        help="MQTT password")
    parser.add_argument("--topic", default=DEFAULT_TOPIC,
                        help="MQTT subscription topic (supports + and # wildcards)")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR,
                        help="Directory to save JSON message files")
    parser.add_argument("--no-tls", action="store_true",
                        help="Disable TLS (required for plain port 1883 connections)")
    parser.add_argument("--client-id", default="aodn-wis2-subscriber",
                        help="MQTT client ID")
    return parser.parse_args()


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    args = parse_args()
    output_dir = Path(args.output_dir)

    userdata = {
        "host": args.host,
        "port": args.port,
        "topic": args.topic,
        "output_dir": output_dir,
    }

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=args.client_id,
        clean_session=True,
        userdata=userdata,
    )
    client.username_pw_set(args.username, args.password)

    if not args.no_tls:
        client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS_CLIENT)

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.on_subscribe = on_subscribe

    print(f"Connecting to {args.host}:{args.port} ...")
    client.connect(args.host, args.port, keepalive=60)

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nStopped by user.")
        client.disconnect()


if __name__ == "__main__":
    main()
