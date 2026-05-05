#!/usr/bin/env python3
"""
decode_bufr.py - Decode a BUFR message embedded in a WIS2 MQTT notification JSON.

Usage:
    python decode_bufr.py <mqtt_message.json> [output.txt]

If output path is omitted the result is written alongside the input file with a .txt extension.
All BUFR sections (0-5) are decoded and written to the output file.
"""

import argparse
import base64
import json
import os
import re
import sys
import tempfile
from typing import Any

import eccodes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get(handle: int, key: str, default: Any = "N/A") -> Any:
    """Get a single BUFR key value, returning *default* on missing key."""
    try:
        return eccodes.codes_get(handle, key)
    except eccodes.KeyValueNotFoundError:
        return default
    except Exception as exc:
        return f"<error: {exc}>"


def _get_array(handle: int, key: str, default: Any = None) -> Any:
    """Get an array BUFR key value, returning *default* on missing key."""
    try:
        return eccodes.codes_get_array(handle, key)
    except eccodes.KeyValueNotFoundError:
        return default if default is not None else []
    except Exception as exc:
        return [f"<error: {exc}>"]


def _fmt_value(v: Any) -> str:
    """Format a decoded value for display, mapping missing-value sentinels."""
    MISSING_DOUBLE = eccodes.CODES_MISSING_DOUBLE
    MISSING_LONG = eccodes.CODES_MISSING_LONG
    if isinstance(v, float):
        if v == MISSING_DOUBLE:
            return "MISSING"
        return f"{v:g}"
    if isinstance(v, int) and v == MISSING_LONG:
        return "MISSING"
    return str(v)


# ---------------------------------------------------------------------------
# Section decoders (before unpack)
# ---------------------------------------------------------------------------

def decode_section0(handle: int) -> list[str]:
    lines = [
        "=" * 70,
        "SECTION 0 – Indicator Section",
        "=" * 70,
        f"  Edition number          : {_get(handle, 'edition')}",
        f"  Total message length    : {_get(handle, 'totalLength')} bytes",
    ]
    return lines


def decode_section1(handle: int) -> list[str]:
    typical_year  = _get(handle, "typicalYear")
    typical_month = _get(handle, "typicalMonth")
    typical_day   = _get(handle, "typicalDay")
    typical_hour  = _get(handle, "typicalHour")
    typical_min   = _get(handle, "typicalMinute")
    typical_sec   = _get(handle, "typicalSecond")

    lines = [
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
        f"  Typical date/time (Y-M-D h:m:s): "
        f"{typical_year}-{typical_month:02d}-{typical_day:02d} "
        f"{typical_hour:02d}:{typical_min:02d}:{typical_sec:02d}",
    ]
    return lines


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
    lines = [
        "",
        "=" * 70,
        "SECTION 3 – Data Description Section",
        "=" * 70,
        f"  Section 3 length              : {_get(handle, 'section3Length')} bytes",
        f"  Number of subsets             : {_get(handle, 'numberOfSubsets')}",
        f"  Observed data flag            : {_get(handle, 'observedData')}",
        f"  Compressed data flag          : {_get(handle, 'compressedData')}",
    ]

    n_unexpanded = _get(handle, "numberOfUnexpandedDescriptors", 0)
    unexpanded = _get_array(handle, "unexpandedDescriptors")
    lines.append(f"  Unexpanded descriptors ({n_unexpanded})    : {list(unexpanded)}")

    # Expanded descriptor table
    names   = _get_array(handle, "expandedNames")
    units   = _get_array(handle, "expandedUnits")
    codes   = _get_array(handle, "expandedOriginalCodes")
    abbrevs = _get_array(handle, "expandedAbbreviations")

    if names:
        lines.append("")
        lines.append(f"  Expanded descriptor sequence ({len(names)} entries):")
        lines.append(f"    {'#':<4}  {'F XX YYY':<10}  {'Abbreviation':<55}  {'Unit'}")
        lines.append(f"    {'-'*4}  {'-'*10}  {'-'*55}  {'-'*20}")
        for i, (code, abbr, name, unit) in enumerate(zip(codes, abbrevs, names, units)):
            f_xx_yyy = f"{code // 1000 // 64} {(code // 1000) % 64:02d} {code % 1000:03d}"
            abbr_str = f"{abbr}"
            lines.append(f"    {i:<4}  {f_xx_yyy:<10}  {abbr_str:<55}  {unit}")

    return lines


def decode_section4(handle: int) -> list[str]:
    """Decode section 4 data values using eccodes' key iterator + seen_keys counting."""
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
    unit_by_abbrev: dict[str, str] = {
        str(a): u
        for a, u in zip(raw_abbrevs, raw_units)
        if a and not str(a).isdigit()
    }
    data_abbrevs = set(unit_by_abbrev)

    # Use the key iterator for correct enumeration order.  The iterator
    # returns plain key names (no #N# prefix) for EVERY occurrence, so we
    # must still track seen_keys ourselves to build the correct #N# key
    # that eccodes uses for codes_get on repeated descriptors.
    seen_keys: dict[str, int] = {}
    it = eccodes.codes_keys_iterator_new(handle)
    try:
        while eccodes.codes_keys_iterator_next(it):
            base = eccodes.codes_keys_iterator_get_name(it)
            if base not in data_abbrevs:
                continue
            count = seen_keys.get(base, 0)
            seen_keys[base] = count + 1
            eccodes_key = base if count == 0 else f"#{count + 1}#{base}"
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
    end_marker = _get(handle, "7777", "N/A")
    lines = [
        "",
        "=" * 70,
        "SECTION 5 – End Section",
        "=" * 70,
        f"  End marker (7777)             : {end_marker}",
        f"  Section 5 length              : {_get(handle, 'section5Length')} bytes",
    ]
    return lines


# ---------------------------------------------------------------------------
# Main decode function
# ---------------------------------------------------------------------------

def decode_mqtt_bufr(json_path: str, output_path: str) -> None:
    """Extract and decode the BUFR message from a WIS2 MQTT notification JSON."""

    # 1. Load and validate the MQTT notification
    with open(json_path, encoding="utf-8") as fh:
        notification = json.load(fh)

    content = notification.get("properties", {}).get("content", {})
    if not content:
        sys.exit("ERROR: 'properties.content' not found in the JSON file.")

    encoding = content.get("encoding", "").lower()
    if encoding != "base64":
        sys.exit(f"ERROR: Unsupported content encoding '{encoding}' (expected 'base64').")

    b64_value = content.get("value", "")
    if not b64_value:
        sys.exit("ERROR: 'properties.content.value' is empty.")

    bufr_bytes = base64.b64decode(b64_value)

    # 2. Write BUFR bytes to a temporary file (eccodes requires a real file descriptor)
    with tempfile.NamedTemporaryFile(suffix=".bufr4", delete=False) as tmp:
        tmp.write(bufr_bytes)
        tmp_path = tmp.name

    output_lines: list[str] = []

    try:
        with open(tmp_path, "rb") as fh:
            handle = eccodes.codes_bufr_new_from_file(fh)

        if handle is None:
            sys.exit("ERROR: eccodes could not parse the BUFR data.")

        try:
            # Sections 0-3 can be read before unpacking
            output_lines += decode_section0(handle)
            output_lines += decode_section1(handle)
            output_lines += decode_section2(handle)
            output_lines += decode_section3(handle)

            # Section 4 requires the data to be unpacked first
            eccodes.codes_set(handle, "unpack", 1)
            output_lines += decode_section4(handle)
            output_lines += decode_section5(handle)

        finally:
            eccodes.codes_release(handle)

    finally:
        os.unlink(tmp_path)

    # 3. Prepend a summary header
    props = notification.get("properties", {})
    header = [
        "WIS2 MQTT Notification – BUFR Decode Report",
        "=" * 70,
        f"  Source file             : {os.path.basename(json_path)}",
        f"  Data ID                 : {props.get('data_id', 'N/A')}",
        f"  Observation datetime    : {props.get('datetime', 'N/A')}",
        f"  Published at            : {props.get('pubtime', 'N/A')}",
        f"  WIGOS station ID        : {props.get('wigos_station_identifier', 'N/A')}",
        f"  BUFR size               : {len(bufr_bytes)} bytes",
        "",
    ]
    output_lines = header + output_lines + [""]

    # 4. Write output
    text = "\n".join(output_lines)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(text)

    print(f"Decoded BUFR written to: {output_path}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Decode a BUFR message from a WIS2 MQTT notification JSON file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("json_file", help="Path to the MQTT notification JSON file")
    parser.add_argument(
        "output_file",
        nargs="?",
        help="Output text file path (default: <input>.txt)",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.json_file):
        sys.exit(f"ERROR: File not found: {args.json_file}")

    output_path = args.output_file or os.path.splitext(args.json_file)[0] + ".txt"
    decode_mqtt_bufr(args.json_file, output_path)


if __name__ == "__main__":
    main()
