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
# - Currently does not support removing station metadata collections by commands
# - Must unpublish station metadata on wis2box-webapp manually with token.
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

unpublish_metadata(){
    WIS2_BUOY_SITE_NAME=$1

    print_status "Unpublishing discovery metadata for $WIS2_BUOY_SITE_NAME ..."

    # Unpublish discovery metadata and delete collection
    wis2box metadata discovery unpublish "urn:wmo:md:au-bom-imos:$WIS2_BUOY_SITE_NAME" && \
    wis2box data delete-collection "urn:wmo:md:au-bom-imos:$WIS2_BUOY_SITE_NAME" && \
    print_success "$WIS2_BUOY_SITE_NAME metadata unpublished successfully" || \
    print_error "Failed to unpublish $WIS2_BUOY_SITE_NAME metadata"
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

print_status "Starting WIS2Box metadata unpublishing process..."

# Confirm destructive operation
confirm_unpublish

# -----------------------------------------------------------------------------
# 1. Unpublish Discovery Metadata for Apollo Bay
# -----------------------------------------------------------------------------
unpublish_metadata wave-buoy-appollo-bay

# -----------------------------------------------------------------------------
# 2. Unpublish Discovery Metadata for Storm Bay
# -----------------------------------------------------------------------------
unpublish_metadata wave-buoy-storm-bay


# =============================================================================
# MANUAL ALTERNATIVE
# =============================================================================
# If you prefer to unpublish metadata manually, follow these steps:
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
# 3. Inside the container, run the unpublish commands individually:
#    wis2box metadata discovery unpublish /data/wis2box/metadata/discovery/wave-buoy-apollo-bay.yml
#    wis2box data delete-collection urn:wmo:md:au-bom-imos:wave-buoy-apollo-bay
#
# 4. Repeat for other metadata files as needed:
#    wis2box metadata discovery unpublish /data/wis2box/metadata/discovery/wave-buoy-storm-bay.yml
#    wis2box data delete-collection urn:wmo:md:au-bom-imos:wave-buoy-storm-bay
#
# =============================================================================
