# wis2box-pipeline

Data pipeline configuration for AODN wis2box implementation, containing metadata and mapping definitions for ocean observation data processing.

## Directory Structure

```
wis2box-data/
├── metadata/
│   ├── discovery/          # Discovery metadata (MCF YAML files)
│   │   ├── apollo-bay.yml  # Apollo Bay wave buoy metadata
│   │   └── storm-bay.yml   # Storm Bay wave buoy metadata
│   └── station/           # Station metadata
│       └── station_list.csv # Station information registry
└── mappings/              # Data format mappings
    ├── wave_buoy_template.json          # BUFR template for wave data
    └── wave_buoy_template_prototype.json # Template prototype
```

## Configuration Files

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

