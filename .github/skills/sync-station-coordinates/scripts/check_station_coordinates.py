#!/usr/bin/env python3
"""Compare station_list.csv coordinates against the latest monthly AODN THREDDS file.

Positions come from the per-record LATITUDE/LONGITUDE arrays (median over the
month), not the geospatial_lat/lon bounding box — a buoy that was moved or
recovered mid-month makes the bbox midpoint land in open water.

Stdlib only. Usage:

    python3 check_station_coordinates.py --targets /path/to/WAVE_BUOYS.yaml
    python3 check_station_coordinates.py --targets ... --apply
"""

from __future__ import annotations

import argparse
import csv
import math
import re
import statistics
import sys
import urllib.request
from pathlib import Path

THREDDS = "https://thredds.aodn.org.au/thredds"
DEFAULT_CSV = Path("wis2-pipeline/wis2box-data/metadata/station/station_list.csv")
DEFAULT_THRESHOLD_KM = 20.0
PRECISION = 5


def fetch(url: str) -> str:
    with urllib.request.urlopen(url, timeout=120) as resp:
        return resp.read().decode("utf-8", errors="replace")


def load_targets(path: Path) -> list[dict]:
    """Parse name/prefix/wigos_id triples out of the WAVE_BUOYS.yaml targets list."""
    targets: list[dict] = []
    name = prefix = None
    for line in path.read_text().splitlines():
        m = re.match(r"- name:\s*(\S+)", line)
        if m:
            name, prefix = m.group(1), None
        m = re.search(r"prefix:\s*(\S+)", line)
        if m:
            prefix = m.group(1)
        m = re.search(r"wigos_id:\s*(\S+)", line)
        if m:
            targets.append({"name": name, "prefix": prefix, "wigos": m.group(1)})
    return targets


def latest_file(prefix: str) -> str | None:
    """Return the THREDDS urlPath of the most recent monthly file under a site prefix."""
    base = f"{THREDDS}/catalog/{prefix.rstrip('/')}"
    years = sorted(re.findall(r'xlink:href="(\d{4})/catalog\.xml"', fetch(f"{base}/catalog.xml")))
    for year in reversed(years):
        paths = sorted(re.findall(r'urlPath="([^"]+\.nc)"', fetch(f"{base}/{year}/catalog.xml")))
        if paths:
            return paths[-1]
    return None


def positions(url_path: str) -> list[tuple[float, float]]:
    txt = fetch(f"{THREDDS}/dodsC/{url_path}.ascii?LATITUDE,LONGITUDE")
    values: dict[str, list[float]] = {}
    for var in ("LATITUDE", "LONGITUDE"):
        m = re.search(rf"^{var}\[\d+\]\n(.*?)(?=\n\w|\Z)", txt, re.S | re.M)
        if m is None:
            raise RuntimeError(f"{var} not found in DAP response")
        values[var] = [float(v) for v in m.group(1).replace("\n", " ").split(",") if v.strip()]
    return [
        (la, lo)
        for la, lo in zip(values["LATITUDE"], values["LONGITUDE"])
        if -90 <= la <= 90 and -180 <= lo <= 180 and abs(la) > 1e-6
    ]


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dlam = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlam / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="path to station_list.csv")
    ap.add_argument("--targets", type=Path, required=True, help="path to WAVE_BUOYS.yaml")
    ap.add_argument("--threshold-km", type=float, default=DEFAULT_THRESHOLD_KM)
    ap.add_argument("--apply", action="store_true", help="rewrite the CSV with the median positions")
    args = ap.parse_args()

    with args.csv.open(newline="") as fh:
        reader = csv.DictReader(fh)
        fieldnames = reader.fieldnames or []
        rows = list(reader)
    by_wigos = {r["wigos_station_identifier"]: r for r in rows}

    hdr = (
        f"{'station':23}{'csv_lat':>11}{'csv_lon':>11}{'med_lat':>11}{'med_lon':>11}"
        f"{'d_med':>8}{'d_last':>8}{'spread':>8}  flag"
    )
    print(hdr)
    print("-" * len(hdr))

    over: list[tuple[str, float]] = []
    wide: list[tuple[str, float]] = []
    changed = 0
    for target in load_targets(args.targets):
        row = by_wigos.get(target["wigos"])
        if row is None:
            print(f"{target['name']:23}  MISSING from {args.csv.name} (wigos {target['wigos']})")
            continue
        csv_lat, csv_lon = float(row["latitude"]), float(row["longitude"])
        try:
            path = latest_file(target["prefix"])
            if path is None:
                raise RuntimeError("no .nc files in catalog")
            fixes = positions(path)
            if not fixes:
                raise RuntimeError("no valid positions in file")
        except Exception as exc:  # noqa: BLE001 - report per station and continue
            print(f"{target['name']:23}{csv_lat:11.5f}{csv_lon:11.5f}  ERROR: {exc}")
            continue

        med_lat = round(statistics.median(f[0] for f in fixes), PRECISION)
        med_lon = round(statistics.median(f[1] for f in fixes), PRECISION)
        last_lat, last_lon = fixes[-1]
        d_med = haversine(csv_lat, csv_lon, med_lat, med_lon)
        d_last = haversine(csv_lat, csv_lon, last_lat, last_lon)
        spread = max(haversine(med_lat, med_lon, la, lo) for la, lo in fixes)

        flag = "OVER" if max(d_med, d_last) > args.threshold_km else "ok"
        if flag == "OVER":
            over.append((target["name"], d_med))
        if spread > args.threshold_km:
            wide.append((target["name"], spread))
        print(
            f"{target['name']:23}{csv_lat:11.5f}{csv_lon:11.5f}{med_lat:11.5f}{med_lon:11.5f}"
            f"{d_med:8.2f}{d_last:8.2f}{spread:8.2f}  {flag}"
        )

        if args.apply and (round(csv_lat, PRECISION), round(csv_lon, PRECISION)) != (med_lat, med_lon):
            row["latitude"], row["longitude"] = f"{med_lat}", f"{med_lon}"
            changed += 1

    print(f"\nstations over {args.threshold_km:.0f} km: {len(over)}")
    for name, dist in sorted(over, key=lambda x: -x[1]):
        print(f"  {name}: {dist:.2f} km")
    if wide:
        print(f"\nstations whose own monthly spread exceeds {args.threshold_km:.0f} km (inspect manually):")
        for name, spread in sorted(wide, key=lambda x: -x[1]):
            print(f"  {name}: {spread:.2f} km")

    if args.apply:
        lines = [",".join(fieldnames)]
        lines += [",".join(row[f] for f in fieldnames) for row in rows]
        # station_list.csv is stored without a trailing newline
        args.csv.write_text("\n".join(lines))
        print(f"\nupdated {changed} row(s) in {args.csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
