# WIS2 pygeoAPI — AODN Usage Guide

The wis2box-aodn deployment exposes an [OGC API — Features](https://ogcapi.ogc.org/features/) endpoint powered by [pygeoapi](https://pygeoapi.io/). It provides machine-readable access to discovery metadata, station information, data notifications (WIS Notification Messages), and observation data.

## Base URL

| Environment | Base URL |
|---|---|
| Production | `https://wis2box.production.aodn.org.au/oapi` |
| Edge (non-production) | `https://wis2box.edge.aodn.org.au/oapi` |

Interactive API documentation (Swagger UI):
```
https://wis2box.production.aodn.org.au/oapi/openapi?f=html
```

---

## Collections

The API exposes four collections:

| Collection ID | Title | Contents |
|---|---|---|
| `discovery-metadata` | Discovery metadata | WCMP2 dataset records |
| `stations` | Stations | WIGOS-registered wave buoy stations |
| `messages` | Data notifications | WIS Notification Messages (WNM) for all published data |
| `urn:wmo:md:au-imos:wave-buoys` | Observations | Decoded wave buoy observations (GeoJSON) |

List all collections:

```bash
curl "https://wis2box.production.aodn.org.au/oapi/collections?f=json"
```

---

## Common Query Parameters

These parameters apply to all `/items` endpoints:

| Parameter | Description | Example |
|---|---|---|
| `limit` | Max items to return (default: 10) | `limit=50` |
| `offset` | Skip first N items (for pagination) | `offset=100` |
| `bbox` | Bounding box `minLon,minLat,maxLon,maxLat` | `bbox=112,-44,155,-10` |
| `datetime` | Single instant or closed/open interval (ISO 8601) | `datetime=2026-05-01/2026-05-07` |
| `f` | Response format: `json`, `jsonld`, `html` | `f=json` |

Each collection also supports filtering by its own **queryable properties** (see sections below).

---

## Collection: `discovery-metadata`

Returns WCMP2 (WMO Core Metadata Profile 2) discovery records describing published datasets.

```bash
# List all discovery records
curl "https://wis2box.production.aodn.org.au/oapi/collections/discovery-metadata/items?f=json"

# Get the wave-buoys dataset record directly
curl "https://wis2box.production.aodn.org.au/oapi/collections/discovery-metadata/items/urn:wmo:md:au-imos:wave-buoys?f=json"
```

**Example response (abbreviated):**
```json
{
  "id": "urn:wmo:md:au-imos:wave-buoys",
  "properties": {
    "title": "Wave buoy observations made as part of the -- IMOS-WIS2.0",
    "wmo:dataPolicy": "core"
  }
}
```

---

## Collection: `stations`

Returns all 23 WIGOS-registered wave buoy stations registered with this wis2box node.

### Queryable properties

| Property | Type | Description |
|---|---|---|
| `wigos_station_identifier` | string | WIGOS station ID (e.g. `0-22000-0-7811080`) |
| `name` | string | Station name (e.g. `APOLLO-BAY`) |
| `facility_type` | string | `seaFixed` for all moored buoys |
| `territory_name` | string | Country code (e.g. `AUS`) |
| `wmo_region` | string | WMO region (e.g. `southWestPacific`) |
| `status` | string | `operational` |
| `topic` | string | MQTT topic the station publishes to |

### Examples

```bash
# List all stations
curl "https://wis2box.production.aodn.org.au/oapi/collections/stations/items?f=json"

# Get a specific station by WIGOS ID
curl "https://wis2box.production.aodn.org.au/oapi/collections/stations/items/0-22000-0-7811080?f=json"

# Filter stations by bounding box (Australian east coast)
curl "https://wis2box.production.aodn.org.au/oapi/collections/stations/items?bbox=148,-38,154,-25&f=json"
```

**Example response:**
```json
{
  "id": "0-22000-0-7811080",
  "type": "Feature",
  "geometry": { "type": "Point", "coordinates": [143.7232, -38.7541, 0] },
  "properties": {
    "name": "APOLLO-BAY",
    "wigos_station_identifier": "0-22000-0-7811080",
    "traditional_station_identifier": "7811080",
    "facility_type": "seaFixed",
    "territory_name": "AUS",
    "wmo_region": "southWestPacific",
    "status": "operational",
    "url": "https://oscar.wmo.int/surface/#/search/station/stationReportDetails/0-22000-0-7811080",
    "topic": "origin/a/wis2/au-imos/data/core/ocean/surface-based-observations/wave-buoys"
  }
}
```

---

## Collection: `messages`

Returns **WIS Notification Messages (WNM)** — one per published BUFR observation file. Each message includes a download link to the BUFR4 file and optionally an inline base64-encoded copy of the data.

### Queryable properties

| Property | Type | Description |
|---|---|---|
| `wigos_station_identifier` | string | WIGOS station ID |
| `data_id` | string | Unique data identifier (matches BUFR filename) |
| `datetime` | string (ISO 8601) | Observation timestamp |
| `pubtime` | string (ISO 8601) | Publication timestamp |
| `metadata_id` | string | Linked discovery metadata record |

### Examples

```bash
# All notifications for Apollo Bay (station 0-22000-0-7811080)
curl "https://wis2box.production.aodn.org.au/oapi/collections/messages/items?wigos_station_identifier=0-22000-0-7811080&limit=10"

# Filter by datetime range
curl "https://wis2box.production.aodn.org.au/oapi/collections/messages/items?wigos_station_identifier=0-22000-0-7811080&datetime=2026-05-01/2026-05-07&limit=10"

# Free-text search by partial data_id
curl "https://wis2box.production.aodn.org.au/oapi/collections/messages/items?q=WIGOS_0-22000-0-7811080&limit=10"

# Spatial filter — notifications within a bounding box
curl "https://wis2box.production.aodn.org.au/oapi/collections/messages/items?bbox=143.0,-39.0,144.5,-38.0&limit=10"
```

**Example response:**
```json
{
  "type": "FeatureCollection",
  "numberMatched": 2763,
  "numberReturned": 1,
  "features": [
    {
      "id": "0f5f3593-5864-426e-926b-914d08839ab1",
      "type": "Feature",
      "geometry": { "type": "Point", "coordinates": [143.72267, -38.75463] },
      "properties": {
        "data_id": "au-bom-imos:wave-buoy-apollo-bay/WIGOS_0-22000-0-7811080_20251111T102000",
        "datetime": "2025-11-11T10:20:00Z",
        "pubtime": "2025-11-11T11:18:09Z",
        "wigos_station_identifier": "0-22000-0-7811080",
        "metadata_id": "urn:wmo:md:au-bom-imos:wave-buoy-apollo-bay",
        "integrity": {
          "method": "sha512",
          "value": "1rccrEuBUo6d..."
        }
      },
      "links": [
        {
          "rel": "canonical",
          "type": "application/bufr",
          "href": "https://wis2box.production.aodn.org.au/data/2025-11-11/wis/urn:wmo:md:au-bom-imos:wave-buoy-apollo-bay/WIGOS_0-22000-0-7811080_20251111T102000.bufr4",
          "length": 122
        }
      ]
    }
  ]
}
```

The `links[0].href` with `rel: "canonical"` is the direct download URL for the BUFR4 file.

---

## Pagination

The API uses **offset-based pagination**. Use `numberMatched` and `numberReturned` to drive iteration:

```python
import requests

base = "https://wis2box.production.aodn.org.au/oapi/collections/messages/items"
params = {
    "wigos_station_identifier": "0-22000-0-7811080",
    "datetime": "2026-05-01/2026-05-07",
    "limit": 100,
    "offset": 0,
    "f": "json",
}

all_features = []
while True:
    r = requests.get(base, params=params).json()
    all_features.extend(r["features"])
    if len(all_features) >= r["numberMatched"]:
        break
    params["offset"] += params["limit"]

print(f"Retrieved {len(all_features)} notifications")
```

---

## Downloading BUFR Files

Each message notification contains a canonical link to its BUFR4 file:

```python
import requests

# 1. Query notifications for a station
url = "https://wis2box.production.aodn.org.au/oapi/collections/messages/items"
params = {
    "wigos_station_identifier": "0-22000-0-7811080",
    "datetime": "2026-05-06/2026-05-07",
    "limit": 10,
    "f": "json",
}
resp = requests.get(url, params=params).json()

print(f"Total matched: {resp['numberMatched']}")

# 2. Download each BUFR file
for feature in resp["features"]:
    props = feature["properties"]
    bufr_url = next(
        link["href"] for link in feature["links"] if link["rel"] == "canonical"
    )
    print(f"{props['datetime']}  →  {bufr_url}")

    bufr_data = requests.get(bufr_url).content
    filename = bufr_url.split("/")[-1]
    with open(filename, "wb") as f:
        f.write(bufr_data)
    print(f"  Saved {filename} ({len(bufr_data)} bytes)")
```

---

## Quick Reference

```bash
BASE="https://wis2box.production.aodn.org.au/oapi"
WIGOS="0-22000-0-7811080"

# Landing page
curl "$BASE?f=json"

# All collections
curl "$BASE/collections?f=json"

# Queryable fields for messages
curl "$BASE/collections/messages/queryables?f=json"

# All stations
curl "$BASE/collections/stations/items?f=json"

# One station
curl "$BASE/collections/stations/items/$WIGOS?f=json"

# Latest 10 notifications for a station
curl "$BASE/collections/messages/items?wigos_station_identifier=$WIGOS&limit=10&f=json"

# Notifications in a date range
curl "$BASE/collections/messages/items?wigos_station_identifier=$WIGOS&datetime=2026-05-01/2026-05-07&f=json"

# Notifications in a bounding box (all Australian waters)
curl "$BASE/collections/messages/items?bbox=112,-44,155,-10&limit=10&f=json"

# Discovery metadata record
curl "$BASE/collections/discovery-metadata/items/urn:wmo:md:au-imos:wave-buoys?f=json"
```

---

## Further Reading

- [pygeoapi documentation](https://docs.pygeoapi.io/)
- [OGC API — Features standard](https://ogcapi.ogc.org/features/)
- [WIS 2.0 Notification Message spec](http://wis.wmo.int/spec/wnm/1/conf/core)
- [wis2box documentation](https://docs.wis2box.wis.wmo.int/)
