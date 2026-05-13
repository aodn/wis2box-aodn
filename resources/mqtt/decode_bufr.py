#!/usr/bin/env python3
"""
decode_burf.py - Download and decode a BUFR file from a WIS2 MQTT notification JSON,
                 or decode a local BUFR file directly.

Modes:
  JSON mode  (default): reads the canonical href from the JSON links array, downloads
             the BUFR file into the same directory, and writes a decode report.
  BUFR mode  (--bufr):  decodes a local .bufr4 file directly without any JSON.

Usage:
    # JSON mode — download from canonical URL then decode
    python decode_burf.py <mqtt_message.json> [output.txt]

    # BUFR mode — decode a local BUFR file directly
    python decode_burf.py --bufr <file.bufr4> [output.txt]

If output path is omitted the report is written alongside the input file with a .txt extension.

Requires: eccodes (pip install eccodes)
"""

import argparse
from collections import Counter
import json
import os
import sys
import urllib.request
from typing import Any

import eccodes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get(handle: int, key: str, default: Any = "N/A") -> Any:
    try:
        return eccodes.codes_get(handle, key)
    except eccodes.KeyValueNotFoundError:
        return default
    except Exception as exc:
        return f"<error: {exc}>"


def _get_array(handle: int, key: str, default: Any = None) -> Any:
    try:
        return eccodes.codes_get_array(handle, key)
    except eccodes.KeyValueNotFoundError:
        return default if default is not None else []
    except Exception as exc:
        return [f"<error: {exc}>"]


def _fmt_value(v: Any) -> str:
    MISSING_DOUBLE = eccodes.CODES_MISSING_DOUBLE
    MISSING_LONG = eccodes.CODES_MISSING_LONG
    if isinstance(v, float):
        return "MISSING" if v == MISSING_DOUBLE else f"{v:g}"
    if isinstance(v, int) and v == MISSING_LONG:
        return "MISSING"
    return str(v)


# ---------------------------------------------------------------------------
# Section decoders
# ---------------------------------------------------------------------------

def decode_section0(handle: int) -> list[str]:
    return [
        "=" * 70,
        "SECTION 0 – Indicator Section",
        "=" * 70,
        f"  Edition number          : {_get(handle, 'edition')}",
        f"  Total message length    : {_get(handle, 'totalLength')} bytes",
    ]


def decode_section1(handle: int) -> list[str]:
    y  = _get(handle, "typicalYear")
    mo = _get(handle, "typicalMonth")
    d  = _get(handle, "typicalDay")
    h  = _get(handle, "typicalHour")
    mi = _get(handle, "typicalMinute")
    s  = _get(handle, "typicalSecond")
    return [
        "",
        "=" * 70,
        "SECTION 1 – Identification Section",
        "=" * 70,
        f"  Section 1 length              : {_get(handle, 'section1Length')} bytes",
        f"  Master table number           : {_get(handle, 'masterTableNumber')}",
        f"  Originating centre            : {_get(handle, 'bufrHeaderCentre')}",
        f"  Originating sub-centre        : {_get(handle, 'bufrHeaderSubCentre')}",
        f"  Update sequence number        : {_get(handle, 'updateSequenceNumber')}",
        f"  Data category                 : {_get(handle, 'dataCategory')}",
        f"  International data sub-cat.   : {_get(handle, 'internationalDataSubCategory')}",
        f"  Local data sub-category       : {_get(handle, 'dataSubCategory')}",
        f"  Master tables version         : {_get(handle, 'masterTablesVersionNumber')}",
        f"  Local tables version          : {_get(handle, 'localTablesVersionNumber')}",
        f"  Typical date/time (Y-M-D h:m:s): {y}-{mo:02d}-{d:02d} {h:02d}:{mi:02d}:{s:02d}",
    ]


def decode_section2(handle: int) -> list[str]:
    present = _get(handle, "localSectionPresent", 0)
    lines = [
        "",
        "=" * 70,
        "SECTION 2 – Optional Local Use Section",
        "=" * 70,
        f"  Present                       : {'Yes' if present else 'No'}",
    ]
    if present:
        lines.append(f"  Section 2 length              : {_get(handle, 'section2Length')} bytes")
    return lines


def decode_section3(handle: int) -> list[str]:
    n_unexpanded = _get(handle, "numberOfUnexpandedDescriptors", 0)
    unexpanded   = _get_array(handle, "unexpandedDescriptors")
    lines = [
        "",
        "=" * 70,
        "SECTION 3 – Data Description Section",
        "=" * 70,
        f"  Section 3 length              : {_get(handle, 'section3Length')} bytes",
        f"  Number of subsets             : {_get(handle, 'numberOfSubsets')}",
        f"  Observed data flag            : {_get(handle, 'observedData')}",
        f"  Compressed data flag          : {_get(handle, 'compressedData')}",
        f"  Unexpanded descriptors ({n_unexpanded})    : {list(unexpanded)}",
    ]

    names   = _get_array(handle, "expandedNames")
    units   = _get_array(handle, "expandedUnits")
    codes   = _get_array(handle, "expandedOriginalCodes")
    abbrevs = _get_array(handle, "expandedAbbreviations")

    if names:
        lines += [
            "",
            f"  Expanded descriptor sequence ({len(names)} entries):",
            f"    {'#':<4}  {'F XX YYY':<10}  {'Abbreviation':<55}  {'Unit'}",
            f"    {'-'*4}  {'-'*10}  {'-'*55}  {'-'*20}",
        ]
        for i, (code, abbr, name, unit) in enumerate(zip(codes, abbrevs, names, units)):
            f_xx_yyy = f"{code // 1000 // 64} {(code // 1000) % 64:02d} {code % 1000:03d}"
            lines.append(f"    {i:<4}  {f_xx_yyy:<10}  {str(abbr):<55}  {unit}")

    return lines


def decode_section4(handle: int) -> list[str]:
    lines = [
        "",
        "=" * 70,
        "SECTION 4 – Data Section",
        "=" * 70,
        f"  Section 4 length              : {_get(handle, 'section4Length')} bytes",
        "",
        "  Data values (from unpacked BUFR):",
        f"    {'Key':<65}  {'Value':<20}  Unit",
        f"    {'-'*65}  {'-'*20}  {'-'*30}",
    ]

    # Build unit lookup keyed by base abbreviation.
    raw_abbrevs = _get_array(handle, "expandedAbbreviations")
    raw_units   = _get_array(handle, "expandedUnits")
    data_keys = [str(a) for a in raw_abbrevs if a and not str(a).isdigit()]
    key_counts = Counter(data_keys)
    unit_by_abbrev: dict[str, str] = {}
    for abbr, unit in zip(raw_abbrevs, raw_units):
        key = str(abbr)
        if key in key_counts and key not in unit_by_abbrev:
            unit_by_abbrev[key] = unit
    data_abbrevs = set(unit_by_abbrev)

    # Use the key iterator for correct enumeration order.  The iterator
    # returns plain key names for every occurrence, while ecCodes addresses
    # repeated descriptors as #1#key, #2#key, ... including the first value.
    seen_keys: dict[str, int] = {}
    it = eccodes.codes_keys_iterator_new(handle)
    try:
        while eccodes.codes_keys_iterator_next(it):
            base = eccodes.codes_keys_iterator_get_name(it)
            if base not in data_abbrevs:
                continue
            count = seen_keys.get(base, 0)
            seen_keys[base] = count + 1
            eccodes_key = f"#{count + 1}#{base}" if key_counts[base] > 1 else base
            unit = unit_by_abbrev.get(base, "")
            try:
                raw = eccodes.codes_get(handle, eccodes_key)
                value_str = _fmt_value(raw)
            except eccodes.KeyValueNotFoundError:
                value_str = "MISSING"
            except Exception as exc:
                value_str = f"<error: {exc}>"
            lines.append(f"    {eccodes_key:<65}  {value_str:<20}  {unit}")
    finally:
        eccodes.codes_keys_iterator_delete(it)

    return lines


def decode_section5(handle: int) -> list[str]:
    return [
        "",
        "=" * 70,
        "SECTION 5 – End Section",
        "=" * 70,
        f"  End marker (7777)             : {_get(handle, '7777', 'N/A')}",
        f"  Section 5 length              : {_get(handle, 'section5Length')} bytes",
    ]


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def get_canonical_href(notification: dict) -> str:
    """Return the href from the first link with rel='canonical'."""
    for link in notification.get("links", []):
        if link.get("rel") == "canonical":
            href = link.get("href", "").strip()
            if href:
                return href
    sys.exit("ERROR: No canonical link found in the JSON notification.")


def download_bufr(url: str, dest_path: str) -> int:
    """Download *url* to *dest_path*; return the number of bytes written."""
    print(f"Downloading: {url}")
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = resp.read()
    except Exception as exc:
        sys.exit(f"ERROR: Failed to download BUFR file: {exc}")

    with open(dest_path, "wb") as fh:
        fh.write(data)
    print(f"Saved BUFR  : {dest_path} ({len(data)} bytes)")
    return len(data)


def decode_bufr_file(bufr_path: str) -> list[str]:
    """Decode all BUFR sections and return lines for the report."""
    lines: list[str] = []
    with open(bufr_path, "rb") as fh:
        handle = eccodes.codes_bufr_new_from_file(fh)

    if handle is None:
        sys.exit("ERROR: eccodes could not parse the BUFR file.")

    try:
        lines += decode_section0(handle)
        lines += decode_section1(handle)
        lines += decode_section2(handle)
        lines += decode_section3(handle)
        eccodes.codes_set(handle, "unpack", 1)
        lines += decode_section4(handle)
        lines += decode_section5(handle)
    finally:
        eccodes.codes_release(handle)

    return lines


def run_bufr(bufr_path: str, output_path: str) -> None:
    """Decode a local BUFR file directly and write the report."""
    bufr_size  = os.path.getsize(bufr_path)
    body_lines = decode_bufr_file(bufr_path)

    header = [
        "BUFR Decode Report",
        "=" * 70,
        f"  Source BUFR file        : {os.path.basename(bufr_path)}",
        f"  BUFR size               : {bufr_size} bytes",
        "",
    ]

    text = "\n".join(header + body_lines + [""])
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(text)

    print(f"Report written: {output_path}")


def run(json_path: str, output_path: str) -> None:
    with open(json_path, encoding="utf-8") as fh:
        notification = json.load(fh)

    href = get_canonical_href(notification)

    # Save the .bufr4 file next to the JSON with the same stem
    json_dir  = os.path.dirname(os.path.abspath(json_path))
    json_stem = os.path.splitext(os.path.basename(json_path))[0]
    bufr_path = os.path.join(json_dir, json_stem + ".bufr4")

    bufr_size = download_bufr(href, bufr_path)
    body_lines = decode_bufr_file(bufr_path)

    props = notification.get("properties", {})
    header = [
        "WIS2 MQTT Notification – BUFR Decode Report",
        "=" * 70,
        f"  Source file             : {os.path.basename(json_path)}",
        f"  Canonical URL           : {href}",
        f"  Downloaded BUFR         : {os.path.basename(bufr_path)}",
        f"  Data ID                 : {props.get('data_id', 'N/A')}",
        f"  Observation datetime    : {props.get('datetime', 'N/A')}",
        f"  Published at            : {props.get('pubtime', 'N/A')}",
        f"  WIGOS station ID        : {props.get('wigos_station_identifier', 'N/A')}",
        f"  BUFR size               : {bufr_size} bytes",
        "",
    ]

    text = "\n".join(header + body_lines + [""])
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(text)

    print(f"Report written: {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Decode a BUFR file from a WIS2 MQTT notification JSON (downloads via canonical URL) "
            "or decode a local BUFR file directly."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--bufr",
        metavar="BUFR_FILE",
        help="Decode a local .bufr4 file directly (skips JSON/download step)",
    )

    parser.add_argument(
        "json_file",
        nargs="?",
        help="Path to the MQTT notification JSON file (used when --bufr is not set)",
    )
    parser.add_argument(
        "output_file",
        nargs="?",
        help="Output report path (default: <input stem>.txt)",
    )
    args = parser.parse_args()

    if args.bufr:
        if not os.path.isfile(args.bufr):
            sys.exit(f"ERROR: File not found: {args.bufr}")
        if args.output_file:
            parser.error("With --bufr, provide at most one output_file argument")
        output_path = args.json_file or os.path.splitext(args.bufr)[0] + ".txt"
        run_bufr(args.bufr, output_path)
    else:
        if not args.json_file:
            parser.error("Provide a JSON file or use --bufr <file.bufr4>")
        if not os.path.isfile(args.json_file):
            sys.exit(f"ERROR: File not found: {args.json_file}")
        output_path = args.output_file or os.path.splitext(args.json_file)[0] + ".txt"
        run(args.json_file, output_path)


if __name__ == "__main__":
    main()
