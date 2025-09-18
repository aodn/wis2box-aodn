#!/bin/bash

# =============================================================================
# WIS2Box Metadata Update Script
# =============================================================================
# This script is used for updating the wis2box metadata files in the
# wis2box-management ECS container by pulling the latest metadata from GitHub.
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

# Function to cleanup on error
cleanup() {
    print_warning "Cleaning up temporary files..."
    if [ -d "wis2box-aodn" ]; then
        rm -rf wis2box-aodn 2>/dev/null || true
    fi
}

# Set up error handling
trap cleanup EXIT ERR

# Function to backup existing metadata
backup_metadata() {
    local backup_dir="/tmp/wis2box-metadata-backup-$(date +%Y%m%d_%H%M%S)"

    if [ -d "/data/wis2box/metadata/" ]; then
        print_status "Creating backup of existing metadata..."
        if cp -r /data/wis2box/metadata/ "$backup_dir" 2>/dev/null; then
            print_success "Backup created at: $backup_dir"
            echo "$backup_dir"
        else
            print_error "Failed to create backup"
            return 1
        fi
    else
        print_warning "No existing metadata directory to backup"
        echo ""
    fi
}

# Function to restore from backup
restore_backup() {
    local backup_dir="$1"
    if [ -n "$backup_dir" ] && [ -d "$backup_dir" ]; then
        print_warning "Restoring from backup..."
        if cp -r "$backup_dir"/* /data/wis2box/ 2>/dev/null; then
            print_success "Metadata restored from backup"
        else
            print_error "Failed to restore from backup"
        fi
    fi
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

print_status "Starting WIS2Box metadata update process..."

BACKUP_DIR=""

# Step 1: Create backup of existing metadata
if BACKUP_DIR=$(backup_metadata); then
    print_success "Backup process completed"
else
    print_error "Backup failed, aborting update"
    exit 1
fi

# Step 2: Clone the repository
print_status "Cloning wis2box-aodn repository..."
if git clone https://github.com/aodn/wis2box-aodn.git 2>/dev/null; then
    print_success "Repository cloned successfully"
else
    print_error "Failed to clone repository"
    restore_backup "$BACKUP_DIR"
    exit 1
fi

# Step 3: Verify the source metadata exists
if [ ! -d "wis2box-aodn/wis2-pipeline/wis2box-data/metadata" ]; then
    print_error "Source metadata directory not found in cloned repository"
    restore_backup "$BACKUP_DIR"
    exit 1
fi

# Step 4: Remove existing metadata directory
print_status "Removing existing metadata directory..."
if rm -rf /data/wis2box/metadata/ 2>/dev/null; then
    print_success "Existing metadata removed"
else
    print_warning "No existing metadata to remove or removal failed"
fi

# Step 5: Copy new metadata
print_status "Copying new metadata files..."
if cp -r wis2box-aodn/wis2-pipeline/wis2box-data/metadata /data/wis2box/metadata 2>/dev/null; then
    print_success "New metadata copied successfully"
else
    print_error "Failed to copy new metadata"
    restore_backup "$BACKUP_DIR"
    exit 1
fi

# Step 6: Verify the copy was successful
if [ -d "/data/wis2box/metadata" ] && [ "$(ls -A /data/wis2box/metadata 2>/dev/null)" ]; then
    print_success "Metadata directory exists and contains files"
else
    print_error "Metadata copy verification failed"
    restore_backup "$BACKUP_DIR"
    exit 1
fi

# Step 7: Cleanup temporary files
print_status "Cleaning up temporary files..."
if rm -rf wis2box-aodn 2>/dev/null; then
    print_success "Temporary files cleaned up"
else
    print_warning "Failed to clean up some temporary files"
fi

# Step 8: Remove backup if everything succeeded
if [ -n "$BACKUP_DIR" ] && [ -d "$BACKUP_DIR" ]; then
    print_status "Removing backup (update successful)..."
    rm -rf "$BACKUP_DIR" 2>/dev/null || print_warning "Failed to remove backup directory"
fi

print_success "WIS2Box metadata update completed successfully!"
print_status "Updated metadata is now available at: /data/wis2box/metadata/"

# Optional: List the updated metadata structure
print_status "Updated metadata structure:"
if command -v tree >/dev/null 2>&1; then
    tree /data/wis2box/metadata/ 2>/dev/null || ls -lR /data/wis2box/metadata/
else
    ls -lR /data/wis2box/metadata/ 2>/dev/null || print_warning "Could not list metadata directory"
fi
