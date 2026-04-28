# WIS 2.0 & wis2box Workshop — AODN Staff

> **System under discussion:** `wis2box-aodn` — IMOS wave buoy observations published via the `au-imos` centre.

---

## Slide 1 — Why WIS 2.0?

The World Meteorological Organization (WMO) Information System 2.0 (WIS 2.0) replaces the legacy GTS (Global Telecommunication System) with a modern, web-friendly architecture for sharing weather, climate, and ocean data.

### Key design goals

| Goal | How WIS 2.0 achieves it |
|------|------------------------|
| **Open standards** | HTTP/HTTPS, MQTT, OGC APIs |
| **Pub/sub messaging** | Real-time notifications via MQTT brokers |
| **Machine-readable metadata** | WCMP2 discovery metadata (ISO 19115 profile) |
| **Decentralised** | Each centre runs its own WIS 2.0 node; Global Services aggregate |

### Architecture at a glance

```
Data Producer ──► WIS 2.0 Node ──► Global Broker ──► Global Cache / Discovery
  (au-imos)        (wis2box)        (WMO)              (WMO)
```

**Key takeaway:** IMOS operates as a **data producer**. Our `wis2box-aodn` deployment is the WIS 2.0 Node that publishes wave buoy observations to the WMO network.

### References

- [WIS 2.0 Technical Regulations](https://community.wmo.int/en/activity-areas/wis)
- [WMO Unified Data Policy (Resolution 1, Cg-Ext 2021)](https://ane4bf-datap1.s3-eu-west-1.amazonaws.com/wmocms/s3fs-public/ckeditor/files/Cg-Ext2021-d04-1-WMO-UNIFIED-POLICY-FOR-THE-INTERNATIONAL-approved_en.pdf)

---

## Slide 2 — Topic Hierarchy

WIS 2.0 organises data using a **topic hierarchy** — a structured path that identifies who publishes what kind of data.

### Format

```
{centre_id}/data/{data_policy}/{earth_system_discipline}/{observation_type}/{dataset_name}
```

### AODN example

```
au-imos/data/core/ocean/surface-based-observations/wave-buoys
│        │    │    │     │                           │
│        │    │    │     │                           └─ Dataset name
│        │    │    │     └─ Observation type
│        │    │    └─ Earth system discipline
│        │    └─ WMO data policy (core = free & open)
│        └─ Literal "data"
└─ Centre ID registered with WMO
```

### Breakdown

| Segment | Value | Meaning |
|---------|-------|---------|
| Centre ID | `au-imos` | Integrated Marine Observing System, Australia |
| Data policy | `core` | Freely available under WMO Unified Data Policy |
| Discipline | `ocean` | Earth system discipline |
| Observation type | `surface-based-observations` | In-situ surface instruments |
| Dataset | `wave-buoys` | Coastal wave buoy measurements |

### How it is used

- **MQTT topics:** Notifications are published to broker topics derived from this hierarchy.
- **Discovery metadata:** The topic hierarchy links datasets to [WIS 2.0 catalogues](https://wis2-gdc.weather.gc.ca/collections/wis2-discovery-metadata/items).
- **Data storage:** MinIO bucket paths mirror the hierarchy for incoming/published data.

> See `wis2-pipeline/wis2box-data/metadata/discovery/wave-buoys.yml` → `wis2box.topic_hierarchy`

---

## Slide 3 — Data Formats

### TODO: Wave Buoy Observation Data Format -- NetCDF
Source data files: [IMOS Coastal Wave Bouys](https://thredds5.production.aodn.org.au/thredds/catalog/IMOS/COASTAL-WAVE-BUOYS/WAVE-BUOYS/REALTIME/WAVE-PARAMETERS/catalog.html)

Source data format: NetCDF4 (.nc)   


### Bufr format
Target data format: [BUFR](https://community.wmo.int/en/activity-areas/wis/bufr)
**BUFR** (Binary Universal Form for the Representation of meteorological data) is the WMO standard binary format for exchanging observational data.

### Why BUFR?

| Property | Benefit |
|----------|---------|
| Compact binary encoding | Efficient for transmission and storage |
| Self-describing | Each message carries its own table references |
| Internationally standardised | Interoperable across all WMO member states |
| Supports quality flags | Built-in metadata for data quality |

### BUFR message structure

```
┌──────────────────────┐
│  Section 0: Indicator │  ← "BUFR" magic bytes
│  Section 1: Header    │  ← Data category, centre, timestamp
│  Section 3: Descriptors│ ← What parameters are encoded
│  Section 4: Data      │  ← Actual observation values
│  Section 5: End       │  ← "7777" end marker
└──────────────────────┘
```

### csv2bufr — converting CSV to BUFR

wis2box uses the `csv2bufr` library to transform tabular CSV data into BUFR messages. The conversion is driven by a **JSON template** that maps CSV columns to BUFR descriptors.

#### AODN wave buoy template

Location: `wis2-pipeline/wis2box-data/mappings/wave_buoy_template.json`

Uses BUFR descriptor **3 08 015** (ocean wave spectral observations):

| CSV Column | BUFR Key | Parameter |
|-----------|----------|-----------|
| `SSWMD` | `meanDirectionFromWhichWavesAreComing` | Mean wave direction (°) |
| `WMDS` | `directionalSpreadOfWaves` | Directional spread (°) |
| `WPDI` | `directionFromWhichDominantWavesAreComing` | Peak wave direction (°) |
| `WPDS` | `directionalSpreadOfDominantWave` | Peak directional spread (°) |
| `WPFM` | `averageWavePeriod` | Mean wave period (s) |
| `WPPE` | `spectralPeakWavePeriod` | Peak wave period (s) |
| `WSSH` | `significantWaveHeight` | Significant wave height (m) |

### Data processing pipeline

```
CSV file  ──►  csv2bufr (template)  ──►  BUFR4 message  ──►  bufr2geojson  ──►  GeoJSON (API)
                                               │
                                               └──► Published via MQTT notification
```

> **Hands-on:** Inspect the template at `wis2-pipeline/wis2box-data/mappings/wave_buoy_template.json`

---

## Slide 4 — wis2box Reference Implementation

**wis2box** is the WMO's official open-source reference implementation for running a WIS 2.0 Node. It provides a complete, containerised stack for data ingest, conversion, publication, and discovery.

### Component architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        wis2box stack                        │
│                                                             │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │  nginx   │  │  wis2box-ui  │  │  wis2box-webapp        │ │
│  │  (proxy) │  │  (map view)  │  │  (admin interface)     │ │
│  └────┬─────┘  └──────┬───────┘  └───────────┬────────────┘ │
│       │               │                      │              │
│  ┌────▼───────────────▼──────────────────────▼────────────┐ │
│  │                  wis2box-api (pygeoapi)                 │ │
│  │              OGC API — Features / Records               │ │
│  └────────────────────────┬───────────────────────────────┘ │
│                           │                                 │
│  ┌────────────────────────▼───────────────────────────────┐ │
│  │              wis2box-management                         │ │
│  │    metadata publishing · data ingest · MQTT subscribe   │ │
│  └───────────┬────────────────────────────┬───────────────┘ │
│              │                            │                 │
│  ┌───────────▼──────┐         ┌───────────▼──────────────┐  │
│  │   Elasticsearch  │         │   Mosquitto (MQTT)       │  │
│  │   (search index) │         │   (message broker)       │  │
│  └──────────────────┘         └──────────────────────────┘  │
│              │                            │                 │
│  ┌───────────▼────────────────────────────▼──────────────┐  │
│  │                 MinIO (S3 storage)                     │  │
│  │         wis2box-incoming / wis2box-public              │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Service breakdown

| Service | Container | Role |
|---------|-----------|------|
| **nginx** | `nginx` | Reverse proxy, TLS termination |
| **wis2box-ui** | `wis2box-ui` | Public-facing map and data viewer |
| **wis2box-webapp** | `wis2box-webapp` | Admin web application |
| **wis2box-api** | `wis2box-api` | OGC API endpoint (pygeoapi), serves data & metadata |
| **wis2box-management** | `wis2box-management` | Core engine — subscribes to MQTT, processes data |
| **wis2box-auth** | `wis2box-auth` | Token-based auth for data ingest |
| **Elasticsearch** | `elasticsearch` | Backend index for API queries |
| **Mosquitto** | `mosquitto` | MQTT broker for pub/sub messaging |
| **MinIO** | `wis2box-minio` | S3-compatible object storage |

### Key URLs (AODN dev deployment)

| Endpoint | URL |
|----------|-----|
| Homepage | `http://imos-wis.dev.aodn.org.au` |
| OGC API | `http://imos-wis.dev.aodn.org.au/oapi` |
| MinIO Console | `http://imos-wis.dev.aodn.org.au:9001` |
| MQTT Broker | `mqtt://imos-wis.dev.aodn.org.au:1883` |

---

## Slide 5 — AODN Deployment: wis2box-aodn

### Repository layout

```
wis2box-aodn/
├── wis2box/                        # Docker Compose & runtime config
│   ├── docker-compose.yml          # Service definitions
│   ├── wis2box.env.example         # Environment template
│   └── wis2box-ctl.py              # Control script
├── wis2-pipeline/wis2box-data/     # Data pipeline configuration
│   ├── metadata/
│   │   ├── discovery/wave-buoys.yml   # Dataset discovery metadata (MCF)
│   │   └── station/station_list.csv   # WIGOS station registry
│   ├── mappings/
│   │   └── wave_buoy_template.json    # CSV→BUFR mapping template
│   └── scripts/
│       ├── publish_metadata.sh        # Publish metadata to wis2box
│       └── unpublish_metadata.sh      # Remove published metadata
├── wis2-terraform/                 # AWS infrastructure (Terraform)
└── workshop/                       # This workshop
```

### Station network

The deployment currently registers **23 wave buoy stations** around the Australian coast:

| Region | Example Stations |
|--------|-----------------|
| Victoria | Apollo Bay, Central, Cape Bridgewater, Wilsons Prom |
| Tasmania | Storm Bay |
| Western Australia | Coral Bay, Shark Bay, Hillarys, Ocean Beach, Torbay West |
| South Australia | Brighton, North Kangaroo Island, Robe, Ceduna |
| New South Wales | Wooli, Collaroy-Narrabeen, Bengello, Tathra |
| Queensland | Karumba, Mission Beach |
| Northern Territory | Fenton Patches, Maningrida |

All stations use WIGOS identifiers in the format `0-{issuer}-0-{station_id}` (e.g. `0-22000-0-7811080` for Apollo Bay).

### Data flow — end to end

```
  IMOS wave buoys
        │
        ▼
  CSV observation file
  (SSWMD, WMDS, WPDI, WPDS, WPFM, WPPE, WSSH)
        │
        ▼
  Upload to MinIO (wis2box-incoming bucket)
  path: au-imos/data/core/ocean/surface-based-observations/wave-buoys/
        │
        ▼
  wis2box-management detects new file (MQTT event)
        │
        ▼
  csv2bufr plugin converts CSV → BUFR4
  using wave_buoy_template.json
        │
        ├──► BUFR file stored in wis2box-public bucket
        │
        ├──► bufr2geojson converts to GeoJSON
        │    └──► Indexed in Elasticsearch → served via OGC API
        │
        └──► WIS 2.0 notification published to MQTT broker
             topic: origin/a/wis2/au-imos/data/core/ocean/surface-based-observations/wave-buoys
```

---

## Slide 6 — Metadata Deep-Dive

### Station metadata

File: `wis2-pipeline/wis2box-data/metadata/station/station_list.csv`

```csv
station_name,wigos_station_identifier,traditional_station_identifier,facility_type,latitude,longitude,elevation,barometer_height,territory_name,wmo_region
APOLLO-BAY,0-22000-0-7811080,7811080,seaFixed,-38.7541,143.7232,0,0,AUS,southWestPacific
```

Key fields:
- **`wigos_station_identifier`** — Globally unique station ID registered with OSCAR/Surface.
- **`facility_type`** — All buoys are `seaFixed` (moored platforms).
- **`wmo_region`** — All Australian stations fall under `southWestPacific`.

### Discovery metadata (MCF)

File: `wis2-pipeline/wis2box-data/metadata/discovery/wave-buoys.yml`

```yaml
wis2box:
    retention: P30D                          # Keep data for 30 days
    topic_hierarchy: au-imos/data/core/ocean/surface-based-observations/wave-buoys
    country: AUS
    centre_id: au-imos
    data_mappings:
        plugins:
            csv:
                - plugin: wis2box.data.csv2bufr.ObservationDataCSV2BUFR
                  template: wave_buoy_template
                  notify: true
                  file-pattern: '.*\.csv$'
            bufr4:
                - plugin: wis2box.data.bufr2geojson.ObservationDataBUFR2GeoJSON
                  file-pattern: '.*\.bufr4$'

metadata:
    identifier: urn:wmo:md:au-imos:wave-buoys   # Globally unique dataset URN
    hierarchylevel: dataset

identification:
    title: Wave buoy observations made as part of the -- IMOS-WIS2.0
    wmo_data_policy: core                        # Free and unrestricted access
    extents:
        spatial:
            - bbox: [112.0, -44.0, 155.0, -10.0]   # Australian coastal waters
        temporal:
            - begin: 2025-08-30
              resolution: PT30M                      # 30-minute observation interval
```

### How metadata is published

```bash
# Publish station metadata + discovery metadata to wis2box
docker exec wis2box-management \
    wis2box metadata discovery publish \
    /data/wis2box/metadata/discovery/wave-buoys.yml
```

> See `wis2-pipeline/wis2box-data/scripts/publish_metadata.sh` for the automated version.

---

## Slide 7 — Infrastructure (Terraform)

The `wis2-terraform/` directory contains Terraform configurations for provisioning the wis2box-aodn deployment on AWS.

### Key infrastructure components

| Resource | Purpose |
|----------|---------|
| EC2 instance | Hosts the Docker Compose stack |
| EFS volume | Persistent storage for MinIO data (`/mnt/efs-mount-point`) |
| Security groups | Controls access to HTTP (80/443), MQTT (1883), and MinIO (9000/9001) |
| Elastic IP | Stable public address for `imos-wis.dev.aodn.org.au` |

### AODN-specific customisations

1. **No wis2downloader** — IMOS is a data *publisher*, not a consumer; the downloader service is disabled.
2. **EFS for MinIO** — Data persists on AWS EFS rather than local Docker volumes.
3. **SFTP ingest** — MinIO is configured with SFTP (`--sftp` flag on port 8022) for automated data upload.

---

## Slide 8 — Walkthrough: Publishing Data

### Prerequisites

- SSH access to the wis2box EC2 instance
- Docker and Docker Compose running
- `wis2box.env` configured from the example template

### Step 1 — Start the stack

```bash
cd wis2box
python wis2box-ctl.py start
```

### Step 2 — Publish metadata

```bash
# Publish station list
docker exec wis2box-management \
    wis2box metadata station publish-collection

# Publish discovery metadata
docker exec wis2box-management \
    wis2box metadata discovery publish \
    /data/wis2box/metadata/discovery/wave-buoys.yml
```

### Step 3 — Ingest observation data

Upload a CSV file to the MinIO incoming bucket at the path matching the topic hierarchy:

```bash
# Via MinIO client (mc)
mc cp observation.csv \
    wis2box/wis2box-incoming/au-imos/data/core/ocean/surface-based-observations/wave-buoys/
```

Or via SFTP:

```bash
sftp -P 8022 wis2box@<host>
put observation.csv au-imos/data/core/ocean/surface-based-observations/wave-buoys/
```

### Step 4 — Verify

```bash
# Check the API for published observations
curl -s http://imos-wis.dev.aodn.org.au/oapi/collections | python -m json.tool

# Subscribe to MQTT notifications
mosquitto_sub -h imos-wis.dev.aodn.org.au -t "origin/a/wis2/au-imos/#" -v
```

---

## Slide 9 — Key Concepts Summary

| Concept | In our deployment |
|---------|-------------------|
| **WIS 2.0 Node** | `wis2box-aodn` Docker stack |
| **Centre ID** | `au-imos` |
| **Data policy** | `core` (open) |
| **Topic hierarchy** | `au-imos/data/core/ocean/surface-based-observations/wave-buoys` |
| **Data format** | CSV → BUFR4 → GeoJSON |
| **Station IDs** | WIGOS format `0-{issuer}-0-{id}` |
| **Metadata standard** | MCF (YAML) / ISO 19115 / WCMP2 |
| **Message broker** | Mosquitto (MQTT) |
| **Object storage** | MinIO (S3-compatible) |
| **API** | OGC API via pygeoapi |
| **Observation interval** | Every 30 minutes (`PT30M`) |

---

## Slide 10 — Further Reading & Resources

### Official documentation

- [wis2box Documentation](https://docs.wis2box.wis.wmo.int/)
- [wis2box GitHub Repository](https://github.com/wmo-im/wis2box)
- [WIS 2.0 Guide](https://guide.wis2box.wis.wmo.int/)
- [WMO WIS 2.0 Standards](https://community.wmo.int/en/activity-areas/wis)

### AODN / IMOS

- [IMOS Homepage](https://imos.org.au/)
- [AODN Portal](https://portal.aodn.org.au/)
- [THREDDS Catalogue — Wave Buoys](https://thredds.aodn.org.au/thredds/catalog/IMOS/COASTAL-WAVE-BUOYS/WAVE-BUOYS/REALTIME/WAVE-PARAMETERS/catalog.html)

### Tools

- [csv2bufr — CSV to BUFR converter](https://github.com/wmo-im/csv2bufr)
- [pymetdecoder — BUFR decoder](https://github.com/wmo-im/pymetdecoder)
- [pywis-pubsub — WIS 2.0 pub/sub client](https://github.com/wmo-im/pywis-pubsub)
- [OSCAR/Surface — WMO station registry](https://oscar.wmo.int/surface/)

### This repository

- [`wis2-pipeline/wis2box-data/README.md`](../wis2-pipeline/wis2box-data/README.md) — Detailed metadata management docs
- [`wis2box/wis2box.env.example`](../wis2box/wis2box.env.example) — Environment configuration reference
