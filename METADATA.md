# AODN Metadata Management Guide

This guide provides detailed information about managing metadata in the AODN wis2box implementation, following WIS 2.0 standards and best practices.

## Quick Reference

| Component | Location | Purpose |
|-----------|----------|---------|
| Station Metadata | `wis2-pipeline/wis2box-data/metadata/station/` | Station/platform definitions |
| Discovery Metadata | `wis2-pipeline/wis2box-data/metadata/discovery/` | Dataset-level metadata |
| Data Mappings | `wis2-pipeline/wis2box-data/mappings/` | Data format conversion templates |

## Station Metadata Management

### Adding a New Station

1. **Add to Station List**: Edit `station_list.csv` to include the new station:

```csv
station_name,wigos_station_identifier,traditional_station_identifier,facility_type,latitude,longitude,elevation,barometer_height,territory_name,wmo_region
"New-Station",0-22000-0-1234567,1234567,seaFixed,-35.1234,138.5678,5,5,AUS,southWestPacific
```

2. **Required Fields**:
   - `wigos_station_identifier`: Must follow WIGOS format (see [WIGOS station identifiers](https://oscar.wmo.int/geoserver/wigos/ows))
   - `facility_type`: Use controlled vocabulary (e.g., `seaFixed`, `landFixed`, `mobile`)
   - `wmo_region`: Must match WMO regional association

### Station Types in AODN

- **`seaFixed`**: Ocean buoys and platforms (e.g., wave buoys)
- **`landFixed`**: Land-based weather stations
- **`mobile`**: Ships or drifting platforms

## Discovery Metadata Management

### Creating Discovery Metadata

Discovery metadata follows the MCF (Metadata Control File) format. Here's a template for a new wave buoy dataset:

```yaml
wis2box:
    retention: P30D
    topic_hierarchy: au-bom-imos/data/core/ocean/surface-based-observations/wave-buoys
    country: AUS
    centre_id: au-bom-imos
    data_mappings:
        plugins:
            csv:
                - plugin: wis2box.data.csv2bufr.ObservationDataCSV2BUFR
                  template: wave_buoy_template
                  notify: true
                  buckets:
                    - ${WIS2BOX_STORAGE_INCOMING}
                  file-pattern: '.*\.csv$'
            bufr4:
                - plugin: wis2box.data.bufr2geojson.ObservationDataBUFR2GeoJSON
                  buckets:
                    - ${WIS2BOX_STORAGE_INCOMING}
                  file-pattern: '.*\.bufr4$'

mcf:
    version: 1.0

metadata:
    identifier: urn:wmo:md:au-bom-imos:wave-buoy-[STATION-NAME]
    hierarchylevel: dataset

identification:
    title: Wave buoy observations made as part of the IMOS-WIS2.0
    abstract: Australian IMOS-WIS2.0 coastal wave buoy observations
    dates:
        creation: [CREATION-DATE]
    keywords:
        default:
            keywords:
                - surface weather
                - observations
                - ocean
                - surface current
        wmo:
            keywords:
                - ocean
            keywords_type: theme
            vocabulary:
                name: Earth system disciplines as defined by the WMO Unified Data Policy, Resolution 1 (Cg-Ext(2021), Annex 1.
                url: https://codes.wmo.int/wis/topic-hierarchy/earth-system-discipline
    extents:
        spatial:
            - bbox: [MIN_LON, MIN_LAT, MAX_LON, MAX_LAT]
              crs: 4326
        temporal:
            - begin: [START-DATE]
              end: null
              resolution: PT30M
    url: https://thredds.aodn.org.au/thredds/catalog/IMOS/COASTAL-WAVE-BUOYS/WAVE-BUOYS/REALTIME/WAVE-PARAMETERS/catalog.html
    wmo_data_policy: core

contact:
    host:
        organization: Integrated Marine Observing System (IMOS)
        url: https://imos.org.au/
        individualname: Integrated Marine Observing System (IMOS)
        positionname: Integrated Marine Observing System (IMOS)
        phone: "+61362267549"
        fax: null
        address: GPO Box 367, Hobart
        city: Hobart
        postalcode: "7001"
        administrativearea: Hobart
        country: Australia
        email: imos@utas.edu.au
        hoursofservice: 2200h - 0600h UTC
        contactinstructions: email
```

### Key Configuration Parameters

#### Topic Hierarchy
The topic hierarchy follows WIS 2.0 conventions:
```
au-bom-imos/data/core/ocean/surface-based-observations/wave-buoys
```
- `au-bom-imos`: Centre identifier for Australian Bureau of Meteorology - IMOS
- `data/core`: Indicates core data under WMO Data Policy
- `ocean/surface-based-observations`: Domain and observation type
- `wave-buoys`: Specific data type

#### Spatial Extents
Define the geographic coverage using WGS84 coordinates:
```yaml
spatial:
    - bbox: [min_longitude, min_latitude, max_longitude, max_latitude]
      crs: 4326
```

#### Temporal Configuration
- `begin`: Start date for data availability (ISO 8601 format)
- `end`: End date (null for ongoing datasets)
- `resolution`: Data frequency (PT30M = 30 minutes)

## Data Mapping Templates

### Wave Buoy BUFR Template

The wave buoy template maps CSV data to BUFR format for WIS 2.0 distribution. Key mappings include:

```json
{
    "eccodes_key": "#1#significantWaveHeight",
    "value": "data:WSSH",
    "valid_min": "const:0.0",
    "valid_max": "const:81.91"
}
```

### Common Wave Parameters

| Parameter | CSV Column | BUFR Code | Description |
|-----------|------------|-----------|-------------|
| Significant Wave Height | WSSH | significantWaveHeight | Height of waves (m) |
| Peak Wave Period | WPPE | spectralPeakWavePeriod | Period at spectral peak (s) |
| Mean Wave Direction | SSWMD | meanDirectionFromWhichWavesAreComing | Direction (degrees) |
| Wave Spread | WMDS | directionalSpreadOfWaves | Directional spread (degrees) |

## Best Practices

### Metadata Consistency
- Use consistent naming conventions for stations and datasets
- Maintain accurate spatial and temporal extents
- Keep contact information current
- Follow ISO 19115 metadata standards

### Station Management
- Use official WIGOS station identifiers when available
- Ensure station coordinates are accurate (WGS84)
- Set appropriate facility types based on platform characteristics

### Data Quality
- Validate BUFR templates against incoming data formats
- Test data processing pipelines before production deployment
- Monitor data flow and error logs

## Troubleshooting

### Common Issues

1. **Invalid WIGOS Identifier**: Ensure format follows `series-issuer-issue-local` pattern
2. **Spatial Extent Errors**: Verify coordinates are in WGS84 (longitude: -180 to 180, latitude: -90 to 90)
3. **Template Mapping Failures**: Check CSV column names match template expectations
4. **Retention Policy**: Ensure retention periods comply with data sharing agreements

### Validation Tools

- Use wis2box CLI tools to validate metadata files
- Check MCF syntax using online validators
- Test BUFR templates with sample data before deployment

## References

- [WIS 2.0 Guide](https://community.wmo.int/en/activity-areas/wmo-information-system-wis)
- [wis2box Documentation](https://docs.wis2box.wis.wmo.int/en/1.0.0/)
- [MCF Specification](https://docs.wis2box.wis.wmo.int/en/1.0.0/reference/metadata-control-file.html)
- [WIGOS Station Identifiers](https://oscar.wmo.int/geoserver/wigos/ows)
- [WMO Code Registry](https://codes.wmo.int/)