#!/usr/bin/env bash
# Nightly Neo4j backup — cron this on the host, e.g.:
#   0 2 * * * /path/to/veritas/backend/scripts/backup_neo4j.sh
#
# Chain-of-custody requires evidence data to be recoverable; this dumps
# the graph database to a timestamped file outside the live data dir.

set -euo pipefail

BACKUP_DIR="./data/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/neo4j_backup_${TIMESTAMP}.dump"

mkdir -p "${BACKUP_DIR}"

docker exec veritas-neo4j neo4j-admin database dump neo4j --to-path=/data/backups_tmp

docker cp veritas-neo4j:/data/backups_tmp "${BACKUP_FILE}"

echo "Backup written to ${BACKUP_FILE}"

# Optional: prune backups older than 30 days
find "${BACKUP_DIR}" -name "neo4j_backup_*.dump" -mtime +30 -delete
