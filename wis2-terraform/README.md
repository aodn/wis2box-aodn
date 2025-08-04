# IMOS WIS2.0 Terraform

Infrastructure as Code (IaC) configuration for deploying AODN's wis2box implementation on cloud infrastructure.

## Overview

This directory contains Terraform configurations for provisioning the infrastructure required to run the AODN wis2box deployment. The infrastructure supports the metadata management and data processing pipeline documented in the main project.

## Infrastructure Components

The Terraform configuration provisions resources to support:

- **wis2box Services**: Core WIS 2.0 data processing and distribution
- **Metadata Management**: Storage and processing of station and discovery metadata
- **Data Pipeline**: Infrastructure for CSV to BUFR conversion and data distribution
- **Monitoring**: Observability and alerting for the WIS 2.0 services

## Integration with Metadata

This infrastructure supports the metadata management features described in [METADATA.md](../METADATA.md):

- Persistent storage for metadata files and configurations
- Compute resources for data processing pipelines
- Network configuration for WIS 2.0 data distribution
- Security and access control for AODN data

For detailed deployment instructions and infrastructure specifications, refer to the Terraform configuration files in this directory.
