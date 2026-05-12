#!/bin/bash

# =============================================================================
# WIS2Box Discovery Metadata Publisher
# =============================================================================
# Publishes dataset discovery metadata (.yml) to wis2box.
#
# Usage:
#   ./publish_discovery_metadata.sh [collection1 collection2 ...]
#
#   collection1 collection2   File stems to publish (no .yml extension).
#                             If omitted, all files in the discovery directory
#                             are published (manual full-publish mode).
#
# Metadata location: /data/wis2box/metadata/discovery/
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

publish_collection() {
    local COLLECTION_NAME=$1
    print_status "Publishing discovery metadata for $COLLECTION_NAME ..."

    if ! wis2box data add-collection /data/wis2box/metadata/discovery/$COLLECTION_NAME.yml; then
        print_error "Failed to add collection for $COLLECTION_NAME"
        return 1
    fi

    if ! wis2box metadata discovery publish /data/wis2box/metadata/discovery/$COLLECTION_NAME.yml; then
        print_error "Failed to publish discovery metadata for $COLLECTION_NAME"
        return 1
    fi

    print_success "$COLLECTION_NAME published successfully"
}

list_all_collections() {
    ls /data/wis2box/metadata/discovery/*.yml | xargs -n 1 basename | sed 's/\.yml$//'
}

# =============================================================================
# MAIN
# =============================================================================

print_status "Starting discovery metadata publishing..."

if [ "$#" -gt 0 ]; then
    # Collection names were passed as arguments (e.g. from the workflow).
    # Only publish the specified collections.
    print_status "Selective publish: $# collection(s) specified"
    COLLECTIONS=("$@")
else
    # No arguments provided — assume this is a manual full-publish run.
    # Read all .yml file stems from the discovery directory into the array
    # so the same for-loop below handles both cases without duplicating logic.
    print_status "No collections specified — publishing all discovery metadata"
    mapfile -t COLLECTIONS < <(list_all_collections)
fi

for collection in "${COLLECTIONS[@]}"; do
    publish_collection "$collection"
done

print_success "Discovery metadata publishing completed!"

# =============================================================================
# MANUAL ALTERNATIVE
# =============================================================================
# To run individual commands inside the container:
#
#   wis2box data add-collection /data/wis2box/metadata/discovery/wave-buoys.yml
#   wis2box metadata discovery publish /data/wis2box/metadata/discovery/wave-buoys.yml
# =============================================================================
