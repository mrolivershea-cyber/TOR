#!/bin/bash

#==============================================================================
# Tor Proxy Pool - Backup Script
# Version: 1.0.0
# Description: Backup database and configuration
# Usage: ./backup.sh [output_directory]
#==============================================================================

set -e

# Configuration
BACKUP_DIR="${1:-/var/backups/tor-proxy-pool}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="tor-proxy-pool_${TIMESTAMP}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Starting backup...${NC}"

# Create backup directory
mkdir -p "$BACKUP_DIR"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"
mkdir -p "$BACKUP_PATH"

# Backup database
echo -e "${YELLOW}Backing up database...${NC}"
pg_dump -U torproxy torproxy > "${BACKUP_PATH}/database.sql"

# Backup configuration
echo -e "${YELLOW}Backing up configuration...${NC}"
cp /opt/tor-proxy-pool/.env "${BACKUP_PATH}/config.env" 2>/dev/null || true

# Backup Tor data (optional, can be large)
if [ "$2" == "--full" ]; then
    echo -e "${YELLOW}Backing up Tor data...${NC}"
    tar -czf "${BACKUP_PATH}/tor-data.tar.gz" /var/lib/tor-pool 2>/dev/null || true
fi

# Create archive
echo -e "${YELLOW}Creating archive...${NC}"
cd "$BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
rm -rf "$BACKUP_NAME"

echo -e "${GREEN}Backup completed: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz${NC}"

# Cleanup old backups (keep last 7)
ls -t "${BACKUP_DIR}"/*.tar.gz | tail -n +8 | xargs -r rm

echo -e "${GREEN}Old backups cleaned up.${NC}"
