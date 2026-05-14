#!/bin/sh
# scan.sh — runs nmap, then renders HTML report + diff via render.py

set -e

SCAN_DIR=/data/scans
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CURRENT_XML="$SCAN_DIR/scan_${TIMESTAMP}.xml"
LATEST_SYMLINK="$SCAN_DIR/scan_latest.xml"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] scan: $*"; }

log "--- Scan starting ---"
log "Targets: ${NMAP_TARGETS}"
log "Flags:   ${NMAP_FLAGS:--sn}"

mkdir -p "$SCAN_DIR"

# Run nmap
# shellcheck disable=SC2086
nmap ${NMAP_FLAGS:--sn} -oX "$CURRENT_XML" $NMAP_TARGETS
log "nmap complete → $CURRENT_XML"

# Determine previous scan for diff
PREVIOUS_XML=""
if [ -f "$LATEST_SYMLINK" ]; then
    PREVIOUS_XML="$LATEST_SYMLINK"
fi

# Render HTML report (+ diff if we have a previous scan)
if [ -n "$PREVIOUS_XML" ] && [ "$PREVIOUS_XML" != "$CURRENT_XML" ]; then
    log "Rendering scan + diff against $PREVIOUS_XML"
    python3 /opt/autonmap/render.py "$CURRENT_XML" "$PREVIOUS_XML"
else
    log "Rendering scan (no previous scan for diff)"
    python3 /opt/autonmap/render.py "$CURRENT_XML"
fi

# Update latest pointer (copy, not symlink — simpler in containers)
cp "$CURRENT_XML" "$LATEST_SYMLINK"

log "--- Scan complete ---"
