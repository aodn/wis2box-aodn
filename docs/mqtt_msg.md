# WIS2.0 MQTT Message Structure

This document explains the structure and fields of the notification messages (GeoJSON format) used in the WIS2.0 (WMO Information System 2.0) data sharing protocol.

## Sample Message

```json
{
  "id": "a2e4ef00-f179-41a7-9b76-1e7eda002637",
  "type": "Feature",
  "conformsTo": [
    "http://wis.wmo.int/spec/wnm/1/conf/core"
  ],
  "geometry": {
    "coordinates": [
      143.72265,
      -38.75337
    ],
    "type": "Point"
  },
  "properties": {
    "data_id": "au-imos:wave-buoys/WIGOS_0-22000-0-7811080_20260507T000000",
    "datetime": "2026-05-07T00:00:00Z",
    "pubtime": "2026-05-07T00:32:44Z",
    "integrity": {
      "method": "sha512",
      "value": "qOFmMSz7+jL1YziF17BBsbqJ4h3qMVIZD8jqPtscWomQGAiGwraxyyQxCLRgzTa/7vkXEBKk07PAoWX0iUySUA=="
    },
    "metadata_id": "urn:wmo:md:au-imos:wave-buoys",
    "content": {
      "encoding": "base64",
      "value": "QlVGUgAAegQAABYAAAH//wAAAAZuKQAH6gUHAAAAAAAJAAABgMgPAABPACIrSP/////////////////v1KOAAnGRu9vsU//68Dn/////+ElQH/8lf///////gP//////wH//7A///+A//////8RAP///////4Dc3Nzc=",
      "size": 122
    },
    "wigos_station_identifier": "0-22000-0-7811080",
    "id": "a2e4ef00-f179-41a7-9b76-1e7eda002637"
  },
  "links": [
    {
      "rel": "canonical",
      "type": "application/bufr",
      "href": "https://wis2box.production.aodn.org.au/data/2026-05-07/wis/urn:wmo:md:au-imos:wave-buoys/WIGOS_0-22000-0-7811080_20260507T000000.bufr4",
      "length": 122
    },
    {
      "rel": "via",
      "type": "text/html",
      "href": "https://oscar.wmo.int/surface/#/search/station/stationReportDetails/0-22000-0-7811080"
    }
  ],
  "generated_by": "wis2box 1.0.0"
}
```

## Field Definitions

### Root Elements
- **`id`**: A unique UUID for this specific notification message.
- **`type`**: Set to `Feature` following the GeoJSON specification.
- **`conformsTo`**: A list of WMO Information System schemas this message adheres to.
- **`geometry`**: Spatial information about the observation location.
  - **`coordinates`**: `[longitude, latitude]` of the station.
  - **`type`**: Usually `Point`.

### Properties (Metadata)
- **`data_id`**: A unique string identifying the specific data granule.
- **`datetime`**: The timestamp of the observation (ISO 8601 format).
- **`pubtime`**: The timestamp when this message was published.
- **`metadata_id`**: A URN pointing to the collection-level metadata record for this dataset.
- **`wigos_station_identifier`**: The WMO Integrated Global Observing System (WIGOS) ID of the station.

### Data Integrity (`integrity`)
Used to verify that the data has not been corrupted or tampered with during transmission.
- **`method`**: The hashing algorithm used (e.g., `sha512`).
- **`value`**: The resulting hash of the **original binary data**, encoded in Base64.
  > **Note**: To verify, you must decode the payload, calculate its SHA-512 hash, and compare it with this value.

### Content Payload (`content`)
The actual observation data. For smaller files, the data is often embedded directly in the message.
- **`encoding`**: The encoding method for binary data. **"base64"** is standard for JSON.
- **`value`**: The Base64 encoded binary string.
  - **Note**: Decoded strings starting with `BUFR` indicate the file is in WMO BUFR (Binary Universal Form for the Representation of meteorological data) format.
- **`size`**: The size of the original binary data in bytes (not the length of the Base64 string).

### Links
- **`rel: canonical`**: A direct HTTPS link to download the original data file (BUFR4 in this case).
- **`rel: via`**: A reference link, usually pointing to the station's record in the **WMO OSCAR/Surface** database.

### Generator
- **`generated_by`**: The software and version used to create the message (e.g., `wis2box 1.0.0`).

---

## `resources/mqtt` — Scripts and Sample Data

The [`resources/mqtt/`](../resources/mqtt/) directory contains utilities for subscribing to WIS2 MQTT notifications and decoding the embedded BUFR data.

### Prerequisites

```bash
uv add paho-mqtt eccodes
```

---

### `sub_mqtt.py` — Subscribe and capture notifications

Connects to an MQTT broker, subscribes to a WIS2 topic, prints a summary for each received notification, and saves every message as a JSON file.

#### Defaults

| Parameter | Default value |
|-----------|--------------|
| Broker host | `globalbroker.meteo.fr` |
| Port | `8883` (TLS) |
| Username / password | `everyone` / `everyone` |
| Topic | `origin/a/wis2/au-imos/data/core/ocean/surface-based-observations/wave-buoys` |
| Output directory | `mqtt_messages/` |

#### Usage

```bash
# Use all defaults (WMO Global Broker, IMOS wave buoys topic)
uv run resources/mqtt/sub_mqtt.py

# Connect to the IMOS production broker (plain, port 1883)
uv run resources/mqtt/sub_mqtt.py \
    --host wis2box-broker.production.aodn.org.au \
    --port 1883 \
    --username wis2box \
    --password <secret> \
    --no-tls

# Subscribe to all IMOS topics
uv run resources/mqtt/sub_mqtt.py --topic "origin/a/wis2/au-imos/#"

# Subscribe to all WIS2 topics worldwide
uv run resources/mqtt/sub_mqtt.py --topic "origin/a/wis2/#"

# Write output to a custom directory
uv run resources/mqtt/sub_mqtt.py --output-dir /tmp/mqtt_messages
```

Saved files are named `<wigos_station_identifier>-<datetime>.json`.

#### Options

| Flag | Description |
|------|-------------|
| `--host` | MQTT broker hostname |
| `--port` | MQTT broker port |
| `--username` | MQTT username |
| `--password` | MQTT password |
| `--topic` | Subscription topic (supports `+` and `#` wildcards) |
| `--output-dir` | Directory for saved JSON files |
| `--no-tls` | Disable TLS (required for plain port 1883 connections) |
| `--client-id` | MQTT client ID (default: `aodn-wis2-subscriber`) |

---

### `decode_mqtt_bufr.py` — Decode BUFR embedded in a notification JSON

Reads a WIS2 notification JSON, decodes the Base64 BUFR payload in `properties.content.value`, and writes a human-readable decode report covering all BUFR sections (0–5).

> Use this when the BUFR data is **embedded** in the JSON (i.e. `properties.content.encoding == "base64"`).

```bash
# Decode to a .txt report alongside the JSON
uv run resources/mqtt/decode_mqtt_bufr.py <mqtt_message.json>

# Specify a custom output path
uv run resources/mqtt/decode_mqtt_bufr.py <mqtt_message.json> report.txt
```

---

### `decode_bufr.py` — Download and decode a BUFR file via canonical URL

Two modes:

**JSON mode (default):** reads `links[rel=canonical].href` from a notification JSON, downloads the `.bufr4` file, and writes a full decode report.

**BUFR mode (`--bufr`):** decodes a local `.bufr4` file directly without any JSON.

> Use this when you want to download the canonical BUFR file, or when you already have a `.bufr4` file on disk.

```bash
# JSON mode — download from canonical URL then decode
uv run resources/mqtt/decode_bufr.py <mqtt_message.json>
uv run resources/mqtt/decode_bufr.py <mqtt_message.json> report.txt

# BUFR mode — decode a local BUFR file directly
uv run resources/mqtt/decode_bufr.py --bufr <file.bufr4>
uv run resources/mqtt/decode_bufr.py --bufr <file.bufr4> report.txt
```

---

### Sample files

The directory includes a real notification captured from the IMOS production wis2box for station **`0-22000-0-5501868`** (wave buoy at approximately 38.4°S 141.3°E), observation at **2026-05-04T04:45:00Z**:

| File | Description |
|------|-------------|
| `0-22000-0-5501868-2026-05-04T04_45_00Z.json` | WIS2 notification message (GeoJSON / WNM format) |
| `0-22000-0-5501868-2026-05-04T04_45_00Z.bufr4` | Raw BUFR4 file downloaded via the canonical link |
| `0-22000-0-5501868-2026-05-04T04_45_00Z.txt` | Human-readable BUFR decode report (all sections 0–5) |

The BUFR file uses descriptor sequence **3 08 015** (wave buoys) and contains the following key observations:

| Parameter | Value |
|-----------|-------|
| Latitude / Longitude | −38.3617° / 141.275° |
| Significant wave height | 3.04 m |
| Spectral peak wave period | 12.8 s |
| Average wave period | 7 s |
| Dominant wave direction | 213° |
| Directional spread | 39° |
| Mean wave direction | 247° |