# Walkthrough — Publishing WIS2 Data

> A step-by-step operational guide for AODN staff to publish wave buoy data through the IMOS WIS 2.0 node using `wis2box-aodn`.

---

## Prerequisites

Before starting, make sure you have:

- **MQTT Explorer** installed — download from https://mqtt-explorer.com/
- **AWS CLI** configured with access to the AODN edge account (`ap-southeast-2`)
- **AWS Session Manager plugin** installed — required for `aws ecs execute-command` (see below)
- A running **wis2box-edge** ECS cluster with the `wis2box-management` container active
- The **exercise metadata files** from this repository (`wis2-pipeline/wis2box-data/`)

### Install the AWS Session Manager Plugin

The Session Manager plugin is required to open interactive shells into ECS containers. Without it, `aws ecs execute-command` will fail with `SessionManagerPlugin is not found`.

**macOS:**
```bash
curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/mac_arm64/session-manager-plugin.pkg" -o "session-manager-plugin.pkg"

sudo installer -pkg session-manager-plugin.pkg -target / 
```

**Linux (x86_64):**
```bash
curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o session-manager-plugin.deb
sudo dpkg -i session-manager-plugin.deb
```

**Verify:**
```bash
session-manager-plugin --version
```

> Full installation guide: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html

### Logging into wis2box-management (ECS)

Several steps in this walkthrough require a shell inside the `wis2box-management` container. Use the following command each time a step says **"Login to wis2box-management"**:

```bash
aws ecs execute-command \
  --region ap-southeast-2 \
  --cluster wis2box-edge \
  --task <TASK_ID> \
  --container wis2box-management \
  --command "sh" \
  --interactive
```

> **Tip:** Find the current task ID with:
> ```bash
> aws ecs list-tasks --region ap-southeast-2 --cluster wis2box-edge --query 'taskArns[0]' --output text
> ```

---

## 1. Connect to the MQTT Broker

**Learning outcomes:** By the end of this section you will be able to connect to both the WMO Global Broker and the IMOS WIS2 node broker using MQTT Explorer, and understand the WIS2 topic structure and notification message format.

### 1.1 What is MQTT?

WIS 2.0 uses the **MQTT protocol** to advertise the availability of weather, climate, and ocean data. The publish/subscribe model means:

- **Data producers** (like IMOS) publish notification messages to their local MQTT broker.
- The **WMO Global Broker** subscribes to all WIS2 nodes and republishes the messages.
- **Data consumers** subscribe to topics of interest and download data from the URLs in the notifications.

When setting up MQTT subscriptions you can use the following wildcards:

| Wildcard | Scope | Example |
|---|---|---|
| `+` | Single level — replaces one topic level | `origin/a/wis2/+/data/core/ocean/#` |
| `#` | Multi level — replaces all remaining levels | `origin/a/wis2/#` |

### 1.2 Connect to the WMO Global Broker

Open MQTT Explorer and add a new connection:

| Field | Value |
|---|---|
| **Name** | WMO Global Broker |
| **Host** | `globalbroker.meteo.fr` |
| **Port** | `8883` |
| **Username** | `everyone` |
| **Password** | `everyone` |

Click **ADVANCED**, remove any pre-configured topics, and add the subscription topic:

```
origin/a/wis2/#
```

Click **BACK** → **SAVE** → **CONNECT**. Messages from WIS2 nodes worldwide should start appearing.

> **Note:** The `origin` topic carries original messages from WIS2 nodes. The `cache` topic carries messages republished by the Global Cache with updated download URLs. Only `core` data (freely available) is cached.

### 1.3 Connect to the IMOS WIS2 Node

Add a second connection for the IMOS non-production broker:

| Field | Value |
|---|---|
| **Name** | IMOS WIS2 Edge |
| **Host** | `wis2box-broker.edge.aodn.org.au` |
| **Port** | `1883` |
| **Username** | `wis2box` |
| **Password** | *(see below)* |

> **Production** uses the same settings with host `wis2box-broker.production.aodn.org.au`. For this walkthrough we use the **edge (non-production)** environment.

**How to retrieve the broker password:**

1. Open the [AWS Systems Manager Parameter Store](https://ap-southeast-2.console.aws.amazon.com/systems-manager/parameters?region=ap-southeast-2)
2. Search for `wis2`
3. Select `/apps/wis2box/edge/mosquitto_broker_password`
4. Click **Show** and copy the value

After connecting, verify that internal Mosquitto statistics appear under the `$SYS` topic. Keep MQTT Explorer open — you will use it to verify each publishing step below.

### 1.4 Understanding the WIS2 Notification Message

When data is published, a **WIS Notification Message (WNM)** is sent to the broker. The message is a GeoJSON Feature containing:

| Field | Purpose |
|---|---|
| `properties.data_id` | Unique data identifier |
| `properties.datetime` | Observation timestamp |
| `properties.pubtime` | Publication timestamp |
| `properties.integrity` | SHA-512 hash for verification |
| `properties.wigos_station_identifier` | Station that produced the data |
| `links[].href` | Canonical URL to download the data file |

---

## 2. Publish Dataset Discovery Metadata

**Learning outcomes:** By the end of this section you will be able to publish a WCMP2 (WMO Core Metadata Profile 2) discovery record so that the dataset appears in the WIS2 Global Discovery Catalogue.

### 2.1 Background

**Discovery metadata** tells the WIS2 network *what data is available, from whom, and how to access it*. wis2box uses **MCF (Metadata Control File)** — a human-readable YAML format — as the source of truth. When published, wis2box converts it into a WCMP2 record and sends a WIS2 notification with a canonical link to that record.

The MCF file for AODN wave buoys is version-controlled at:
`wis2-pipeline/wis2box-data/metadata/discovery/wave-buoys-workshop.yml` for the workshop and 
`wis2-pipeline/wis2box-data/metadata/discovery/wave-buoys.yml` for production.

Key sections of the MCF file:

| Section | Purpose |
|---|---|
| `wis2box` | Retention policy, topic hierarchy, data mappings (csv2bufr/bufr2geojson plugins) |
| `metadata` | Unique identifier (`urn:wmo:md:au-imos:wave-buoys`) and hierarchy level |
| `identification` | Title, abstract, keywords, spatial/temporal extents, WMO data policy |
| `contact` | Host organisation details (IMOS) |

### 2.2 Method 1 — Via wis2box CLI (Recommended)

This method keeps discovery metadata version-controlled in git.

**Step 1.** Login to wis2box-management (see [Prerequisites](#logging-into-wis2box-management-ecs)).

**Step 2.** Add the dataset collection to the API backend:

```bash
wis2box data add-collection /data/wis2box/metadata/discovery/wave-buoys-workshop.yml
```

**Step 3.** Publish the discovery metadata to the catalogue:

```bash
wis2box metadata discovery publish /data/wis2box/metadata/discovery/wave-buoys-workshop.yml
```

**Step 4.** Verify in MQTT Explorer — a notification should appear on topic:

```
origin/a/wis2/au-imos/metadata
```

The notification contains a canonical link to the WCMP2 record. Copy the link and open it in a browser to inspect the full metadata.

**Step 5.** Verify in the webapp — open the [Dataset Editor](https://wis2box.edge.aodn.org.au/wis2box-webapp/dataset_editor) and confirm the new dataset appears in the list.

### 2.3 Method 2 — Via wis2box-webapp (Manual)

> **Note:** This method is useful for quick edits but does not persist metadata as code. In the AODN deployment, the webapp method may not be fully available depending on the service configuration.

1. Create an authorization token inside wis2box-management:
   ```bash
   wis2box auth add-token --path processes/wis2box
   ```
2. Open the [wis2box-webapp Dataset Editor](https://wis2box.edge.aodn.org.au/wis2box-webapp/dataset_editor).
3. Click **Create New…** → Set Centre ID to `au-imos`, Data Type to `other`.
4. Fill in the metadata fields: title, keywords, description, spatial/temporal extents, and contact information.
5. Configure data mappings with the `wave_buoy_template` plugin.
6. Click **VALIDATE FORM** to check for errors.
7. Enter the `processes/wis2box` token → click **Submit**.

### 2.4 Managing Discovery Metadata

```
wis2box metadata discovery publish    <MCF_FILE>   # Insert or update a record
wis2box metadata discovery republish                # Republish all records
wis2box metadata discovery unpublish  <IDENTIFIER>  # Delete a record
wis2box data add-collection           <MCF_FILE>   # Register collection in API
wis2box data delete-collection        <IDENTIFIER>  # Remove collection from API
```

---

## 3. Publish Station Metadata

**Learning outcomes:** By the end of this section you will be able to register observation stations with WIGOS-compliant identifiers so that wis2box can associate incoming data with the correct station.

### 3.1 Background

The **WMO Integrated Global Observing System (WIGOS)** provides a framework for station identification. Every station that publishes data through WIS2 must have a **WIGOS Station Identifier (WSI)** registered in [OSCAR/Surface](https://oscar.wmo.int/surface/). But the OSCAR service would not block publishing data to WIS2.

WIGOS ID format: `{series}-{issuer}-{issue_number}-{local_id}`

Example: `0-22000-0-7811080` → Apollo Bay wave buoy

> **⚠ Important:** WIS2 cannot publish data without a registered WIGOS ID. Verify IDs at [OSCAR/Surface](https://oscar.wmo.int/surface/) and [OceanOPS](https://www.ocean-ops.org/) before proceeding.

### 3.2 Prepare the Station CSV

The station metadata CSV must contain exactly these columns:

```
station_name,wigos_station_identifier,traditional_station_identifier,facility_type,latitude,longitude,elevation,barometer_height,territory_name,wmo_region
```

Example row:

```csv
APOLLO-BAY,0-22000-0-7811080,7811080,seaFixed,-38.7541,143.7232,0,0,AUS,southWestPacific
```

| Field | Description |
|---|---|
| `wigos_station_identifier` | Globally unique station ID from OSCAR/Surface |
| `facility_type` | `seaFixed` for moored wave buoys |
| `wmo_region` | `southWestPacific` for all Australian stations |

See the full list: [`wis2-pipeline/wis2box-data/metadata/station/station_list.csv`](../wis2-pipeline/wis2box-data/metadata/station/station_list.csv)

### 3.3 Method 1 — Via wis2box CLI (Recommended)

**Step 1.** Login to wis2box-management (see [Prerequisites](#logging-into-wis2box-management-ecs)).

**Step 2.** Publish the station collection:

```bash
wis2box metadata station publish-collection \
    -p /data/wis2box/metadata/station/station_list.csv \
    -th origin/a/wis2/au-imos/data/core/ocean/surface-based-observations/wave-buoys-workshop
```

**Step 3.** Verify — open the [Stations page](https://wis2box.edge.aodn.org.au/wis2box-webapp/station) in the webapp and confirm the stations appear on the map.

You can also query the API:

```bash
curl -s https://wis2box.edge.aodn.org.au/oapi/collections/stations/items | python3 -m json.tool
```

### 3.4 Method 2 — Via wis2box-webapp (Manual)

1. Create an authorization token for `collections/stations`:
   ```bash
   wis2box auth add-token --path collections/stations
   ```
2. Open the webapp → **Stations** page.
3. Enter a WIGOS ID → click **Search** → the station info is fetched from OSCAR/Surface.
4. Select the corresponding topic hierarchy.
5. Enter the `collections/stations` token → click **Save and Publish**.

> **Admin note:** Ensure authorization tokens are created before the workshop:
> ```bash
> wis2box auth add-token --path processes/wis2box
> wis2box auth add-token --path collections/stations
> ```

---

## 4. Publish Observation Data

**Learning outcomes:** By the end of this section you will be able to ingest wave buoy observation data into wis2box and verify that BUFR messages and WIS2 notifications are published.

### 4.1 Background

Once station and discovery metadata are in place, wis2box is ready to receive observation data. The data pipeline works as follows:

```
CSV file uploaded to MinIO incoming bucket
        │
        ▼
wis2box-management detects new file (MQTT event)
        │
        ▼
csv2bufr plugin converts CSV → BUFR4
(using wave_buoy_template.json)
        │
        ├──► BUFR file stored in wis2box-public bucket
        ├──► bufr2geojson converts BUFR → GeoJSON (indexed in Elasticsearch)
        └──► WIS2 notification published to MQTT broker
             topic: origin/a/wis2/au-imos/data/core/ocean/surface-based-observations/wave-buoys-workshop
```

### 4.2 Ingest Data via MinIO (mc)

**Step 1.** Set up the MinIO client alias:

```bash
mc alias set wis2-edge https://wis2box.edge.aodn.org.au <ACCESS_KEY> <SECRET_KEY>
```

**Step 2.** Upload a CSV observation file to the incoming bucket:

```bash
mc cp observation.csv \
    wis2-edge/wis2box-incoming/urn:wmo:md:au-imos:wave-buoys/
```

The bucket path must match the `metadata.identifier` defined in the discovery metadata MCF file.

### 4.3 Ingest Data via wis2box CLI

Alternatively, you can ingest data directly from inside the wis2box-management container:

```bash
wis2box data ingest \
    -p /path/to/observation.csv \
    -th au-imos/data/core/ocean/surface-based-observations/wave-buoys-workshop
```

### 4.4 Verify Publication

1. **MQTT Explorer** — Check for a new notification on:
   ```
   origin/a/wis2/au-imos/data/core/ocean/surface-based-observations/wave-buoys-workshop
   ```
   The notification should contain a `links[].href` pointing to the BUFR file in the public bucket.

2. **API** — Query for published observations:
   ```bash
   curl -s "https://wis2box.edge.aodn.org.au/oapi/collections/messages/items?datetime=2026-04-30/2026-05-01&limit=10" | python3 -m json.tool
   ```

3. **MinIO** — Confirm the BUFR file exists in the public bucket:
   ```bash
   mc ls wis2-edge/wis2box-public/ --recursive | head
   ```

4. **Webapp** — Open the [Monitoring page](https://wis2box.edge.aodn.org.au/wis2box-webapp/monitoring) to see data notification counts.

5. **MQTT Subscribed Message** 
   The wis2box should publish a message to the MQTT broker that looks like this:
   ```
   origin/a/wis2/au-imos/data/core/ocean/surface-based-observations/wave-buoys-workshop
   ```
   The message should contain a `links[].href` pointing to the BUFR file in the public bucket. Save this message to a file, for example:
   ```bash
   uv run resources/mqtt/sub_mqtt.py --host wis2box-broker.edge.aodn.org.au --port 1883 --username wis2box --password <secret> --no-tls
   ```  
