#!/bin/bash

# =============================================================================
# WIS2Box Station Metadata Publisher
# =============================================================================
# Publishes weather station metadata (station_list.csv) to wis2box,
# associating stations with their WIS2 topic hierarchy.
#
# Usage:
#   ./publish_station_metadata.sh
#
# Metadata location: /data/wis2box/metadata/station/station_list.csv
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status()  { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

# =============================================================================
# MAIN
# =============================================================================

print_status "Starting station metadata publishing..."

# TODO: if more topics will be published, refactor here to loop over topics.
print_status "Publishing station metadata for wave buoys..."

if ! wis2box metadata station publish-collection \
    -p /data/wis2box/metadata/station/station_list.csv \
    -th origin/a/wis2/au-imos/data/core/ocean/surface-based-observations/wave-buoys; then
    print_error "Failed to publish station metadata"
    exit 1
fi

print_success "Wave buoy station metadata published successfully!"

# =============================================================================
# MANUAL ALTERNATIVE
# =============================================================================
# To add a topic before publishing (only needed once):
#   wis2box metadata station add-topic \
#     origin/a/wis2/au-imos/data/core/ocean/surface-based-observations/wave-buoys
# =============================================================================
