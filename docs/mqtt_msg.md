# WIS2.0 MQTT Message Structure

This document explains the structure and fields of the notification messages (GeoJSON format) used in the WIS2.0 (WMO Information System 2.0) data sharing protocol.

## Sample Message

```json
{
  "id": "f6ef8700-5e0a-4e52-8abf-e15e647a7f54",
  "type": "Feature",
  "conformsTo": [
    "http://wis.wmo.int/spec/wnm/1/conf/core"
  ],
  "geometry": {
    "coordinates": [141.27452, -38.36218],
    "type": "Point"
  },
  "properties": {
    "data_id": "au-imos:wave-buoys/WIGOS_0-22000-0-5501868_20260501T024500",
    "datetime": "2026-05-01T02:45:00Z",
    "pubtime": "2026-05-01T03:32:51Z",
    "integrity": {
      "method": "sha512",
      "value": "Fb0+dCiRJGh2cfSeOBc9g8Tx6q3Gz3cOS6KCBf7MP9x91Y5UnzLJjiMmUauZh3riSLZrtR5TL8Rlb98I51WHJQ=="
    },
    "metadata_id": "urn:wmo:md:au-imos:wave-buoys",
    "content": {
      "encoding": "base64",
      "value": "QlVGUgAAegQAABYAAGL//wAAAAZuKQAH6gUBAi0AAAAJAAABgMgPAABPAAIHTP/////////////////v1KCK0nZYM9Rzuf/7kCf/////+DtSX/8x////////gP//////wH//7q///+A//////8RAP///////4Dc3Nzc=",
      "size": 122
    },
    "wigos_station_identifier": "0-22000-0-5501868"
  },
  "links": [
    {
      "rel": "canonical",
      "type": "application/bufr",
      "href": "https://wis2box.production.aodn.org.au/data/2026-05-01/wis/urn:wmo:md:au-imos:wave-buoys/WIGOS_0-22000-0-5501868_20260501T024500.bufr4",
      "length": 122
    },
    {
      "rel": "via",
      "type": "text/html",
      "href": "https://oscar.wmo.int/surface/#/search/station/stationReportDetails/0-22000-0-5501868"
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