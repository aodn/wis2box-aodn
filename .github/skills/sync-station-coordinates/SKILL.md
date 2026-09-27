---
name: sync-station-coordinates
description: >
  Use when auditing or updating the latitude/longitude values in
  wis2-pipeline/wis2box-data/metadata/station/station_list.csv against the
  authoritative AODN wave buoy data on THREDDS. Handles requests such as
  "check how far the station coordinates drifted", "are any stations more than
  20 km off", "update the station list to the latest positions", or
  investigating where a station's coordinates came from.
---

# Sync Station Coordinates

`station_list.csv` is hand-maintained and has drifted from reality more than once — one past
commit moved CORAL-BAY 50 km inland while claiming to "fix" it. This skill compares each station
against the real buoy positions published on AODN THREDDS and, optionally, rewrites the CSV.

## Sources of truth

| What | Where |
|---|---|
| Station list being audited | `wis2-pipeline/wis2box-data/metadata/station/station_list.csv` |
| Site prefix ↔ WIGOS ID mapping | `WAVE_BUOYS.yaml` in the `dataflow-orchestration` repo (`projects/wis2/`), **outside this workspace** |
| Actual positions | `https://thredds.aodn.org.au/thredds` — `IMOS/COASTAL-WAVE-BUOYS/WAVE-BUOYS/REALTIME/WAVE-PARAMETERS/<SITE>/<YEAR>/*_monthly.nc` |

The site directory name is **not** the station name: CORAL-BAY lives under `CORAL-BAY-02`,
SHARK-BAY under `SHARK-BAY-02`. Always resolve the prefix from `WAVE_BUOYS.yaml` and join to the
CSV row by `wigos_station_identifier`, never by name.

## Workflow

1. Locate `WAVE_BUOYS.yaml`. If the user has not given a path, ask — it is in a sibling repo.
2. Run the audit (read-only):

   ```sh
   python3 .github/skills/sync-station-coordinates/scripts/check_station_coordinates.py \
     --targets /path/to/dataflow-orchestration/projects/wis2/WAVE_BUOYS.yaml
   ```

   The script is stdlib-only, takes under a minute for ~23 stations, and prints per-station
   `d_med` (CSV vs monthly median), `d_last` (CSV vs final fix) and `spread` (widest excursion
   within the month).
3. Report the stations over the threshold (default 20 km) and any station whose own `spread`
   exceeds it — see **Interpreting the output**.
4. Only if the user asks for an update, re-run with `--apply`, then re-run without it to confirm
   every `d_med` is `0.00`.
5. Remind the user to republish station metadata
   (`wis2-pipeline/wis2box-data/scripts/publish_station_metadata.sh`); editing the CSV alone does
   not change what wis2box serves.

## How positions are derived

Use the **median of the per-record `LATITUDE`/`LONGITUDE` arrays** over the latest monthly file,
fetched via OPeNDAP ASCII (`<file>.nc.ascii?LATITUDE,LONGITUDE`).

Do **not** use the `geospatial_lat_min/max` / `geospatial_lon_min/max` global attributes from the
`.das` endpoint. Their midpoint is only valid for a buoy that stayed put; for SHARK-BAY and
OCEAN-BEACH the bbox midpoint lands between two deployment sites and falsely reports a >20 km
error. The bbox is fine as a cheap sanity probe, not as the answer.

"Latest month" means the highest-numbered file in the highest-numbered year directory — some
sites stopped reporting months ago (ROBE, KARUMBA), so never assume the current month exists.

## Interpreting the output

| Signal | Meaning | Action |
|---|---|---|
| `d_med` large, `spread` small | CSV is simply wrong, or the buoy was redeployed elsewhere | Update the CSV |
| `d_med` small, `spread` large | One monthly file contains two locations — redeployment, mooring failure, or bad GPS fixes | Do not blindly update; flag for the data team |
| `d_last` >> `d_med` | Buoy drifting at the end of the record, probably during recovery | Keep the median |

Sub-kilometre differences are normal watch-circle movement on a mooring and are not errors.

## Guardrails

- Never write to `WAVE_BUOYS.yaml` — it belongs to another repository.
- Keep coordinates at 5 decimal places and preserve the CSV column order and the absence of a
  trailing newline.
- `elevation` and `barometer_height` stay `0` for `seaFixed` buoys; this skill only touches
  `latitude` and `longitude`.
