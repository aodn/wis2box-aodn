# Copilot Instructions for wis2box-aodn

This repository implements a WIS 2.0 (WMO Information System 2.0) node for the Australian Ocean Data Network (AODN) using the wis2box reference implementation.

## Project Overview

- **Purpose**: Deploy and manage wis2box for distributing ocean and weather data following WMO WIS 2.0 standards
- **Organization**: Integrated Marine Observing System (IMOS), part of AODN
- **Primary Data**: Wave buoy observations from Australian coastal monitoring stations

## Repository Structure

- `wis2box/` - Docker Compose configuration and control scripts for wis2box deployment
- `wis2-pipeline/wis2box-data/` - Metadata, mappings, and scripts for data management
  - `metadata/discovery/` - MCF YAML files for dataset discovery metadata
  - `metadata/station/` - CSV files containing WIGOS-compliant station information
  - `mappings/` - JSON templates for CSV to BUFR data conversion
  - `scripts/` - Shell scripts for metadata publishing/unpublishing
- `wis2-terraform/` - Terraform configurations for AWS EC2 infrastructure
- `resources/` - Additional project resources

## Coding Standards

### Python

- Use Python 3.11+ as specified in `.python-version`
- Use `uv` as the package manager (see `pyproject.toml` and `uv.lock`)
- Follow PEP 8 style guidelines
- Use type hints where appropriate

### Shell Scripts

- Use bash for shell scripts
- Include proper error handling and set appropriate shell options
- Add comments for complex operations
- Scripts interact with wis2box containers via `docker exec`

### YAML/MCF Files

- Discovery metadata follows the WMO MCF (Metadata Control File) specification
- Use ISO 19115-compliant metadata structures
- Maintain consistent indentation (2 spaces)
- Include required wis2box configuration blocks:
  - `wis2box:` - retention, topic_hierarchy, country, centre_id
  - `metadata:` - identifier, hierarchylevel
  - `identification:` - title, abstract, extents

### JSON Templates

- BUFR mapping templates follow csv2bufr format
- Include proper data validation ranges
- Map CSV fields to BUFR parameters following WMO standards

## WIS 2.0 Specific Conventions

- **Topic Hierarchy**: Follow format `{centre_id}/data/core/{domain}/{observation-type}/{dataset-name}`
- **WIGOS Station IDs**: Use format `0-{issuer}-0-{station_id}` (e.g., `0-22000-0-7811080`)
- **Centre ID**: Use `au-imos` for IMOS/AODN data
- **Data Policy**: Default to "core" for publicly available data

## External References

- [wis2box Documentation](https://docs.wis2box.wis.wmo.int/)
- [WMO WIS 2.0 Standards](https://community.wmo.int/en/activity-areas/wis)
- [IMOS/AODN](https://imos.org.au/)
