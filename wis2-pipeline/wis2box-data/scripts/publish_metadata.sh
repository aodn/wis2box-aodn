#!/bin/bash

# =============================================================================
# WIS2Box Metadata Publisher Script
# =============================================================================
# This script is used to publish dataset discovery metadata and weather station
# metadata to WIS2Box instead of manually creating metadata from WIS2Box webapp.
#
# Metadata File locations:
# - Discovery metadata: .yml files stored in ../metadata/discovery/
# - Weather station metadata: .csv files stored in ../metadata/station/
# =============================================================================

set -e  # Exit on any error

# Colors for output formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

publish_metadata(){
    WIS2_BUOY_SITE_NAME=$1
    print_status "Publishing discovery metadata for $WIS2_BUOY_SITE_NAME ..."

    wis2box data add-collection /data/wis2box/metadata/discovery/$WIS2_BUOY_SITE_NAME.yml && \
    wis2box metadata discovery publish /data/wis2box/metadata/discovery/$WIS2_BUOY_SITE_NAME.yml && \
    print_success "$WIS2_BUOY_SITE_NAME metadata published successfully" || \
    print_error "Failed to publish $WIS2_BUOY_SITE_NAME metadata"

}
# =============================================================================
# MAIN EXECUTION
# =============================================================================

print_status "Starting WIS2Box metadata publishing process..."

# -----------------------------------------------------------------------------
# 1. Publish Discovery Metadata for Apollo Bay
# -----------------------------------------------------------------------------
publish_metadata wave-buoy-apollo-bay
# -----------------------------------------------------------------------------
# 2. Publish Discovery Metadata for Storm Bay
# -----------------------------------------------------------------------------
publish_metadata wave-buoy-storm-bay

# -----------------------------------------------------------------------------
# 3. Publish Station Metadata for Wave Buoys
# -----------------------------------------------------------------------------
print_status "Publishing station metadata for wave buoys..."

#TODO: if more topics will be published, can refactor codes here to manage weather station metadata.
wis2box metadata station publish-collection \
    -p /data/wis2box/metadata/station/station_list.csv \
    -th origin/a/wis2/au-imos/data/core/ocean/surface-based-observations/wave-buoys && print_success "Wave buoy station metadata published successfully" || print_error "Failed to publish station metadata"

print_status "Metadata publishing process completed!"

# =============================================================================
# MANUAL ALTERNATIVE
# =============================================================================
# If you prefer to update metadata manually, follow these steps:
#
# 1. LOGIN AWS account:
#    aws sso login
#
# 2. Login to the wis2 ecs:
#    aws ecs execute-command \
        # --region ap-southeast-2 \
        # --cluster imos-wis2-test-edge \
        # --task 9b862868d5ef467eb355d9aed1d568e3 \
        # --container wis2box-management \
        # --command "sh" \
        # --interactive
#
# 3. Inside the container, run the commands individually:
#    wis2box data add-collection /data/wis2box/metadata/discovery/wave-buoy-apollo-bay.yml
#    wis2box metadata discovery publish /data/wis2box/metadata/discovery/wave-buoy-apollo-bay.yml
#
# 4. Repeat for other metadata files as needed
# =============================================================================
