#!/bin/bash

# =============================================================================
# WIS2Box Metadata Publisher Script
# =============================================================================
# This script is used to publish dataset discovery metadata and weather station
# metadata to WIS2Box instead of manually creating metadata from WIS2Box webapp.
#
# File locations:
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

# Function to check if container is running
check_container() {
    if ! docker ps | grep -q "wis2box-management"; then
        print_error "wis2box-management container is not running!"
        print_warning "Please start WIS2Box services first: python3 wis2box-ctl.py start"
        exit 1
    fi
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

print_status "Starting WIS2Box metadata publishing process..."

# Check if the management container is running
check_container

# -----------------------------------------------------------------------------
# 1. Publish Discovery Metadata for Apollo Bay
# -----------------------------------------------------------------------------
print_status "Publishing discovery metadata for Apollo Bay..."

docker exec -it wis2box-management bash -c '
    wis2box data add-collection /data/wis2box/metadata/discovery/apollo-bay.yml &&
    wis2box metadata discovery publish /data/wis2box/metadata/discovery/apollo-bay.yml
' && print_success "Apollo Bay metadata published successfully" || print_error "Failed to publish Apollo Bay metadata"

# -----------------------------------------------------------------------------
# 2. Publish Discovery Metadata for Storm Bay
# -----------------------------------------------------------------------------
print_status "Publishing discovery metadata for Storm Bay..."

docker exec -it wis2box-management bash -c '
    wis2box data add-collection /data/wis2box/metadata/discovery/storm-bay.yml &&
    wis2box metadata discovery publish /data/wis2box/metadata/discovery/storm-bay.yml
' && print_success "Storm Bay metadata published successfully" || print_error "Failed to publish Storm Bay metadata"

# -----------------------------------------------------------------------------
# 3. Publish Station Metadata for Wave Buoys
# -----------------------------------------------------------------------------
print_status "Publishing station metadata for wave buoys..."

docker exec -it wis2box-management bash -c '
    wis2box metadata station publish-collection \
        -p /data/wis2box/metadata/station/station_list.csv \
        -th origin/a/wis2/au-imos/data/core/ocean/surface-based-observations/wave-buoys
' && print_success "Wave buoy station metadata published successfully" || print_error "Failed to publish station metadata"

print_status "Metadata publishing process completed!"

# =============================================================================
# MANUAL ALTERNATIVE
# =============================================================================
# If you prefer to update metadata manually, follow these steps:
#
# 1. Navigate to your wis2box directory:
#    cd ~/wis2box
#
# 2. Login to the management container:
#    python3 wis2box-ctl.py login
#
# 3. Inside the container, run the commands individually:
#    wis2box data add-collection /data/wis2box/metadata/discovery/apollo-bay.yml
#    wis2box metadata discovery publish /data/wis2box/metadata/discovery/apollo-bay.yml
#
# 4. Repeat for other metadata files as needed
# =============================================================================
