# wis2box-pipeline


## Metadata Management

This section documents the metadata management implementation for AODN's wis2box deployment, covering station metadata, discovery metadata, and data mappings as referenced in the [official wis2box documentation](https://docs.wis2box.wis.wmo.int/en/1.0.0/reference/running/concepts.html).

### Station Metadata

Station metadata defines the observing stations and platforms that provide data to the WIS 2.0 system. In this AODN implementation, station information is managed through a CSV file following the [wis2box station metadata specifications](https://docs.wis2box.wis.wmo.int/en/1.0.0/reference/running/station-metadata.html).

#### Station List Configuration

Location: `wis2-pipeline/wis2box-data/metadata/station/station_list.csv`

The station list contains the following fields:

| Field | Description | Example |
|-------|-------------|---------|
| `station_name` | Human-readable station name | "Apollo-bay" |
| `wigos_station_identifier` | WIGOS station identifier | "0-22000-0-7811080" |
| `traditional_station_identifier` | Traditional WMO station ID | "7811080" |
| `facility_type` | Type of observing facility | "seaFixed" |
| `latitude` | Station latitude in decimal degrees | "-38.7541" |
| `longitude` | Station longitude in decimal degrees | "143.7232" |
| `elevation` | Station elevation in meters | "1" |
| `barometer_height` | Barometer height in meters | "1" |
| `territory_name` | Territory or country code | "FSM" |
| `wmo_region` | WMO region | "southWestPacific" |

#### Current Stations

The AODN implementation currently includes the following stations:

1.  **Apollo Bay Wave Buoy** (Sea-based)
   - WIGOS ID: 0-22000-0-7811080
   - Location: 38.7541°S, 143.7232°E

### Discovery Metadata

Discovery metadata provides detailed information about datasets published through the WIS 2.0 system. This follows the [wis2box discovery metadata specifications](https://docs.wis2box.wis.wmo.int/en/1.0.0/reference/running/discovery-metadata.html) using Metadata Control Files (MCF) in YAML format.

#### Metadata Structure

Location: `wis2-pipeline/wis2box-data/metadata/discovery/`

Each discovery metadata file contains:

- **wis2box Configuration**: Data processing and retention settings
- **MCF Metadata**: ISO 19115-compliant metadata following WMO standards
- **Identification**: Dataset title, abstract, keywords, and extents
- **Contact Information**: Organization and contact details

#### Wave Buoy Datasets

##### Apollo Bay Wave Buoy (`apollo-bay.yml`)

```yaml
wis2box:
    retention: P30D
    topic_hierarchy: au-bom-imos/data/core/ocean/surface-based-observations/wave-buoys
    country: AUS
    centre_id: au-bom-imos

metadata:
    identifier: urn:wmo:md:au-bom-imos:wave-buoy-apollo-bay
    hierarchylevel: dataset

identification:
    title: Wave buoy observations made as part of the -- IMOS-WIS2.0
    abstract: Australian IMOS-WIS2.0 costal wave buoys observation
    extents:
        spatial:
            - bbox: [143.72230,-38.75452,143.72362,-38.75350]
              crs: 4326
        temporal:
            - begin: 2025-08-30
              end: null
              resolution: PT30M
```

##### Storm Bay Wave Buoy (`storm-bay.yml`)

Similar structure with different spatial extents:
- Bounding box: [147.44728,-43.19308,147.44785,-43.1926]
- Start date: 2025-07-15
- Same 30-minute temporal resolution

#### Key Configuration Elements

- **Topic Hierarchy**: `au-bom-imos/data/core/ocean/surface-based-observations/wave-buoys`
- **Data Policy**: Core data following WMO Unified Data Policy
- **Retention**: 30 days (P30D)
- **Contact**: Integrated Marine Observing System (IMOS)

### Data Mappings

Data mappings define how incoming data is processed and converted to WIS 2.0 formats, particularly BUFR (Binary Universal Form for the Representation of meteorological data).

#### Wave Buoy Template

Location: `wis2-pipeline/wis2box-data/mappings/wave_buoy_template.json`

This template follows the csv2bufr format and defines:

- **BUFR Message Structure**: Headers and data descriptors
- **Data Field Mappings**: CSV columns to BUFR parameters
- **Validation Ranges**: Min/max values for each parameter

Key wave parameters mapped:

| CSV Field | BUFR Parameter | Description |
|-----------|----------------|-------------|
| `SSWMD` | `meanDirectionFromWhichWavesAreComing` | spectral sea surface wave mean direction |
| `WMDS` | `directionalSpreadOfWaves` | spectral sea surface wave mean directional spread |
| `WPDI` | `directionFromWhichDominantWavesAreComing` | spectral peak wave direction |
| `WPDS` | `directionalSpreadOfDominantWave` | spectral sea surface wave peak directional spread|
| `WPFM` | `averageWavePeriod` | sea surface wave spectral mean period|
| `WPPE` | `spectralPeakWavePeriod` | peak wave spectral period |
| `WSSH` | `significantWaveHeight` | sea surface wave spectral significant height |

#### Data Processing Pipeline

The discovery metadata configures data processing through plugins:

1. **CSV to BUFR**: Converts incoming CSV data to BUFR format using the wave buoy template

```yaml
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
```

### AODN-Specific Configuration

This implementation is specifically configured for AODN's requirements:

- **Organization**: Integrated Marine Observing System (IMOS)
- **Data Source**: Coastal wave buoys providing near real-time observations
- **Geographic Focus**: Australian coastal waters
- **Data Access**: Integration with THREDDS data server
- **Centre ID**: `au-bom-imos` following WMO centre identification

### Managing Metadata

#### Adding New Stations

1. Add station information to `station_list.csv`
2. Create corresponding discovery metadata file in YAML format
3. Configure data mappings if new data formats are required
4. Update wis2box configuration and restart services

#### Updating Discovery Metadata

Discovery metadata can be updated by modifying the YAML files. Key considerations:

- Maintain unique dataset identifiers
- Update spatial/temporal extents as needed
- Ensure contact information remains current
- Follow MCF and ISO 19115 standards

For detailed information on metadata management, refer to the official wis2box documentation:
- [Station Metadata](https://docs.wis2box.wis.wmo.int/en/1.0.0/reference/running/station-metadata.html)
- [Discovery Metadata](https://docs.wis2box.wis.wmo.int/en/1.0.0/reference/running/discovery-metadata.html)
- [Core Concepts](https://docs.wis2box.wis.wmo.int/en/1.0.0/reference/running/concepts.html)
