---
applyTo: "wis2-pipeline/wis2box-data/**/*.yml,wis2-pipeline/wis2box-data/**/*.yaml,wis2-pipeline/wis2box-data/**/*.csv,wis2-pipeline/wis2box-data/**/*.json,wis2-pipeline/wis2box-data/**/*.sh"
---

# wis2box-aodn Data Pipeline Conventions

This repository manages WIS 2.0 data publishing for AODN using [wis2box](https://docs.wis2box.wis.wmo.int/). The pipeline has three main artefact types — discovery metadata (MCF YAML), station metadata (CSV), and BUFR mapping templates (JSON). Keep them consistent with each other and with the station inventory.

## Discovery Metadata (`metadata/discovery/*.yml`)

Each `.yml` file is a WMO MCF (Metadata Control File) that registers a dataset collection in the WIS 2.0 global catalogue.

### Required top-level blocks

| Block | Purpose |
|---|---|
| `wis2box:` | wis2box runtime config — retention, topic hierarchy, data mappings |
| `mcf:` | MCF spec version (`1.0`) |
| `metadata:` | `identifier` and `hierarchylevel` |
| `identification:` | Title, abstract, keywords, extents, data policy |
| `contact:` | Host organisation contact details |

### When to update

| Change | Field(s) to update |
|---|---|
| New dataset or collection | Create a new `.yml`; set `metadata.identifier` to `urn:wmo:md:au-imos:<dataset-name>` |
| Topic hierarchy change | `wis2box.topic_hierarchy` and `publish_metadata.sh` `-th` argument |
| Temporal extent change | `identification.extents.temporal.begin` / `end` / `resolution` |
| Spatial coverage change | `identification.extents.spatial[].bbox` |
| Data retention policy change | `wis2box.retention` (ISO 8601 duration, e.g. `P30D`) |
| CSV-to-BUFR template change | `wis2box.data_mappings.plugins.csv[].template` |
| Data policy change | `identification.wmo_data_policy` (`core` or `recommended`) |

### Conventions

- `metadata.identifier` format: `urn:wmo:md:au-imos:<dataset-name>` (lowercase, hyphenated)
- `wis2box.topic_hierarchy` format: `au-imos/data/core/<domain>/<subdomain>/<dataset-name>`
- `wis2box.centre_id` is always `au-imos`
- `wis2box.country` is always `AUS`
- Dates use `YYYY-MM-DD`; `end: null` means ongoing

## Station Metadata (`metadata/station/*.csv`)

Station CSV files are loaded into wis2box via `wis2box metadata station publish-collection`.

### Required columns

| Column | Format / Example |
|---|---|
| `station_name` | Uppercase hyphenated, e.g. `APOLLO-BAY` |
| `wigos_station_identifier` | `0-<issuer>-0-<id>`, e.g. `0-22000-0-7811080` |
| `traditional_station_identifier` | Numeric string, e.g. `7811080` |
| `facility_type` | `seaFixed` for fixed ocean buoys |
| `latitude` / `longitude` | Decimal degrees (negative south/west) |
| `elevation` / `barometer_height` | Metres above sea level; use `0` if not applicable |
| `territory_name` | `AUS` |
| `wmo_region` | `southWestPacific` for Australian stations |

### When to update

| Change | Action |
|---|---|
| New station added | Append a row to `station_list.csv`; run `publish_metadata.sh` to push to wis2box |
| Station decommissioned | Remove or comment out the row; re-publish |
| Coordinates corrected | Update `latitude` / `longitude` in place |
| WIGOS ID assigned or corrected | Update `wigos_station_identifier` and `traditional_station_identifier` |

## BUFR Mapping Templates (`mappings/*.json`)

Templates follow the [csv2bufr](https://csv2bufr.readthedocs.io/) `csv2bufr-template-v2.json` schema and define how CSV observation columns map to BUFR parameters.

### When to update

| Change | Field(s) to update |
|---|---|
| New CSV input column mapped | Add entry to `data[]` array with correct `eccodes_key` and `valid_min`/`valid_max` |
| CSV delimiter or quoting change | `delimiter`, `quoting`, `quotechar` at top level |
| WIGOS station identifier source column changes | `wigos_station_identifier` key |
| BUFR edition or category change | `header[]` entries (`edition`, `dataCategory`, `internationalDataSubCategory`) |
| Template version bump | `metadata.version` and `metadata.dateModified` |

### Conventions

- `metadata.id` is a UUID — generate a new one only when creating a brand-new template
- Valid range constraints (`valid_min`, `valid_max`) must align with WMO BUFR table definitions
- Do **not** duplicate the `_prototype` file; it exists as a reference only

## Scripts (`scripts/`)

`publish_metadata.sh` and `unpublish_metadata.sh` run inside the `wis2box-management` Docker container via `docker exec`.

### When to update

| Change | Script section to update |
|---|---|
| New topic hierarchy for station publish | `-th` flag in the `wis2box metadata station publish-collection` call |
| New discovery metadata file added | No change needed — the script auto-discovers all `*.yml` files |
| Container or cluster name change | Update the inline AWS ECS command in the manual-alternative comment block |

### Conventions

- Always `set -e` at the top; never suppress errors silently
- Use the existing `print_status` / `print_success` / `print_error` helpers for output — do not use bare `echo`
- `wis2box` CLI commands must reference paths inside the container (`/data/wis2box/…`), not host paths
