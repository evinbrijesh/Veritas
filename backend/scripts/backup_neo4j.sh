#!/bin/bash
# Nightly Neo4j backup — mandatory per CLAUDE.md, not optional tooling.
#
# Community edition has no online backup, so `neo4j-admin database dump`
# requires a stopped database. Pattern: stop the container briefly, dump the
# data dir with a throwaway container, restart. Expect ~1 min downtime.
# The trap guarantees neo4j comes back even if the dump fails.
#
# Schedule with cron, e.g. every night at 2am:
#   0 2 * * * /path/to/veritas/backend/scripts/backup_neo4j.sh
set -euo pipefail

# Repo root derived from script location — safe to run from any CWD (cron).
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKUP_DIR="${REPO_ROOT}/data/backups"
NEO4J_IMAGE="neo4j:5-community"
CONTAINER="veritas-neo4j"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
DUMP_NAME="neo4j_${TIMESTAMP}.dump"

mkdir -p "${BACKUP_DIR}"

echo "==> Stopping ${CONTAINER} for a consistent offline dump..."
# Graceful shutdown — neo4j can need more than the default 10s to flush.
docker stop --time=90 "${CONTAINER}" >/dev/null

# No matter what happens next, bring the graph back up.
restart_neo4j() {
  docker start "${CONTAINER}" >/dev/null
  echo "==> ${CONTAINER} restarted"
}
trap restart_neo4j EXIT

echo "==> Dumping Neo4j to ${BACKUP_DIR}/${DUMP_NAME}"
# Throwaway container with the same data mounts as the running service.
docker run --rm \
  -v "${REPO_ROOT}/data/neo4j/data:/data" \
  -v "${REPO_ROOT}/data/neo4j/logs:/logs" \
  -v "${REPO_ROOT}/data/neo4j/import:/var/lib/neo4j/import" \
  -v "${BACKUP_DIR}:/backups" \
  "${NEO4J_IMAGE}" \
  sh -c "neo4j-admin database dump neo4j --to-path=/backups && mv /backups/neo4j.dump /backups/${DUMP_NAME}"

echo "==> Backup complete"
ls -lh "${BACKUP_DIR}/${DUMP_NAME}"
