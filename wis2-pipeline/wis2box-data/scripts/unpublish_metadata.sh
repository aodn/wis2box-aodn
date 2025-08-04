#!/bin/bash

# =============================================================================
# WIS2Box Metadata Unpublisher Script
# =============================================================================
# This script is used to unpublish dataset discovery metadata and remove
# weather station metadata from WIS2Box.
#
# This script performs the reverse operations of publish_metadata.sh:
# - Unpublishes discovery metadata from the catalogue
# - Deletes collections from the API backend
# - Currently does not support removing station metadata collections by cli
#
# File locations:
# - Discovery metadata: .yml files stored in ../metadata/discovery/
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

# Function to confirm destructive operation
confirm_unpublish() {
    print_warning "This will UNPUBLISH and DELETE metadata from WIS2Box!"
    print_warning "This operation cannot be easily undone."
    echo
    read -p "Are you sure you want to continue? (yes/no): " confirmation

    if [ "$confirmation" != "yes" ]; then
        print_status "Operation cancelled by user."
        exit 0
    fi
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

print_status "Starting WIS2Box metadata unpublishing process..."

# Confirm destructive operation
confirm_unpublish

# Check if the management container is running
check_container

# -----------------------------------------------------------------------------
# 1. Unpublish Discovery Metadata for Apollo Bay
# -----------------------------------------------------------------------------
print_status "Unpublishing discovery metadata for Apollo Bay..."

docker exec -it wis2box-management bash -c '
    wis2box metadata discovery unpublish urn:wmo:md:au-bom-imos:wave-buoy-apollo-bay &&
    wis2box data delete-collection urn:wmo:md:au-bom-imos:wave-buoy-apollo-bay
' && print_success "Apollo Bay metadata unpublished successfully" || print_error "Failed to unpublish Apollo Bay metadata"

# -----------------------------------------------------------------------------
# 2. Unpublish Discovery Metadata for Storm Bay
# -----------------------------------------------------------------------------
print_status "Unpublishing discovery metadata for Storm Bay..."

docker exec -it wis2box-management bash -c '
    wis2box metadata discovery unpublish urn:wmo:md:au-bom-imos:wave-buoy-storm-bay &&
    wis2box data delete-collection urn:wmo:md:au-bom-imos:wave-buoy-storm-bay
' && print_success "Storm Bay metadata unpublished successfully" || print_error "Failed to unpublish Storm Bay metadata"


# =============================================================================
# MANUAL ALTERNATIVE
# =============================================================================
# If you prefer to unpublish metadata manually, follow these steps:
#
# 1. Navigate to your wis2box directory:
#    cd ~/wis2box
#
# 2. Login to the management container:
#    python3 wis2box-ctl.py login
#
# 3. Inside the container, run the unpublish commands individually:
#    wis2box metadata discovery unpublish /data/wis2box/metadata/discovery/apollo-bay.yml
#    wis2box data delete-collection urn:wmo:md:au-bom-imos:apollo-bay
#
# 4. Repeat for other metadata files as needed:
#    wis2box metadata discovery unpublish /data/wis2box/metadata/discovery/storm-bay.yml
#    wis2box data delete-collection urn:wmo:md:au-bom-imos:storm-bay
#
# =============================================================================
