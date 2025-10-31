#!/bin/bash

#==============================================================================
# Tor Proxy Pool - Restore Script
# Version: 1.0.0
# Description: Restore from backup
# Usage: ./restore.sh <backup_file>
#==============================================================================

set -e

# Check argument
if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${RED}WARNING: This will replace current data!${NC}"
read -p "Are you sure? (yes/NO): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Restore cancelled."
    exit 0
fi

echo -e "${GREEN}Starting restore...${NC}"

# Extract backup
TEMP_DIR=$(mktemp -d)
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"
BACKUP_DIR=$(ls "$TEMP_DIR")

# Stop service
echo -e "${YELLOW}Stopping service...${NC}"
sudo systemctl stop tor-proxy-pool

# Restore database
echo -e "${YELLOW}Restoring database...${NC}"
if [ -f "${TEMP_DIR}/${BACKUP_DIR}/database.sql" ]; then
    sudo -u postgres psql -c "DROP DATABASE IF EXISTS torproxy;"
    sudo -u postgres psql -c "CREATE DATABASE torproxy;"
    sudo -u postgres psql -d torproxy -f "${TEMP_DIR}/${BACKUP_DIR}/database.sql"
fi

# Restore configuration
echo -e "${YELLOW}Restoring configuration...${NC}"
if [ -f "${TEMP_DIR}/${BACKUP_DIR}/config.env" ]; then
    cp "${TEMP_DIR}/${BACKUP_DIR}/config.env" /opt/tor-proxy-pool/.env
fi

# Restore Tor data (if exists)
if [ -f "${TEMP_DIR}/${BACKUP_DIR}/tor-data.tar.gz" ]; then
    echo -e "${YELLOW}Restoring Tor data...${NC}"
    tar -xzf "${TEMP_DIR}/${BACKUP_DIR}/tor-data.tar.gz" -C /
fi

# Cleanup
rm -rf "$TEMP_DIR"

# Start service
echo -e "${YELLOW}Starting service...${NC}"
sudo systemctl start tor-proxy-pool

echo -e "${GREEN}Restore completed successfully!${NC}"
