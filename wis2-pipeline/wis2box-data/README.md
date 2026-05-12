# Wis2box-data
This section documents the metadata management implementation for AODN's wis2box deployment, covering station metadata, discovery metadata, and data mappings as referenced in the [official wis2box documentation](https://docs.wis2box.wis.wmo.int/en/1.0.0/reference/running/concepts.html).

## Directory Structure

```
wis2box-data/
├── metadata/
│   ├── discovery/          # Discovery metadata (MCF YAML files)
│   │   └── wave-buoys.yml  # wave buoy metadata
│   └── station/           # Station metadata   
│       └── station_list.csv # Station information registry
├── mappings/              # Data format mappings
│   ├── wave_buoy_template.json          # BUFR template for wave data
│   └── wave_buoy_template_prototype.json # Template prototype
└── scripts/               # Metadata management automation scripts
    ├── publish_metadata.sh   # Automated metadata publishing
    └── unpublish_metadata.sh # Automated metadata removal
```

## Metadata Management
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
| `territory_name` | Territory or country code | "AUS" |
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

##### Apollo Bay Wave Buoy (`wave-buoys.yml`)

```yaml
wis2box:
    retention: P30D
    topic_hierarchy: au-imos/data/core/ocean/surface-based-observations/wave-buoys
    country: AUS
    centre_id: au-imos

metadata:
    identifier: urn:wmo:md:au-imos:wave-buoys
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
- **Centre ID**: `au-imos` following WMO centre identification

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


## Metadata Configuration Files

### Station Metadata
- **Purpose**: Defines observing stations and their characteristics
- **Format**: CSV file with WIGOS-compliant station information
- **Location**: `metadata/station/station_list.csv`

### Discovery Metadata
- **Purpose**: Provides dataset-level metadata for data discovery and access
- **Format**: YAML files following MCF (Metadata Control File) specification
- **Location**: `metadata/discovery/*.yml`

### Data Mappings
- **Purpose**: Defines how CSV data is converted to BUFR format
- **Format**: JSON templates for csv2bufr processing
- **Location**: `mappings/*.json`

## Wave Buoy Data Processing

This pipeline is configured to process wave buoy observations from IMOS coastal monitoring stations:

1. **Data Ingestion**: CSV files containing wave parameters
2. **Format Conversion**: CSV to BUFR using configured templates
3. **Metadata Association**: Links data to station and discovery metadata
4. **Publication**: Makes data available through WIS 2.0 protocols

For detailed metadata management information, see the main [README.md](../README.md#metadata-management).


For detailed information on metadata management, refer to the official wis2box documentation:
- [Station Metadata](https://docs.wis2box.wis.wmo.int/en/1.0.0/reference/running/station-metadata.html)
- [Discovery Metadata](https://docs.wis2box.wis.wmo.int/en/1.0.0/reference/running/discovery-metadata.html)
- [Core Concepts](https://docs.wis2box.wis.wmo.int/en/1.0.0/reference/running/concepts.html)
