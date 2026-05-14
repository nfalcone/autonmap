#!/bin/sh
set -e

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] entrypoint: $*"; }

# --- Validate required env ---
if [ -z "$NMAP_TARGETS" ]; then
    log "ERROR: NMAP_TARGETS is not set. Set it in your .env or docker-compose.yml"
    log "Example: NMAP_TARGETS=192.168.1.0/24 10.10.0.0/16"
    exit 1
fi

# --- Defaults ---
SCAN_CRON="${SCAN_CRON:-0 * * * *}"
NMAP_FLAGS="${NMAP_FLAGS:--sn}"

log "Targets:   $NMAP_TARGETS"
log "Flags:     $NMAP_FLAGS"
log "Schedule:  $SCAN_CRON"
log "Timezone:  ${TZ:-UTC}"

# --- Write crontab ---
mkdir -p /var/spool/cron/crontabs
echo "$SCAN_CRON /opt/autonmap/scan.sh >> /var/log/autonmap/scan.log 2>&1" \
    > /var/spool/cron/crontabs/root
chmod 600 /var/spool/cron/crontabs/root
log "Crontab written"

# --- Ensure data dirs exist ---
mkdir -p /data/scans /var/log/autonmap

# --- Copy nmap.xsl so raw XML renders nicely in Firefox ---
if [ -f /usr/share/nmap/nmap.xsl ]; then
    cp /usr/share/nmap/nmap.xsl /data/scans/nmap.xsl
    log "Copied nmap.xsl to scan dir"
fi

# --- Generate blank index if first run ---
if [ ! -f /data/scans/index.html ]; then
    log "Generating initial index..."
    python3 /opt/autonmap/render.py --index-only
fi

# --- Run an initial scan immediately on first start (optional) ---
if [ "${SCAN_ON_START:-true}" = "true" ]; then
    log "Running initial scan on startup..."
    /opt/autonmap/scan.sh >> /var/log/autonmap/scan.log 2>&1 &
fi

# --- Start nginx in background ---
nginx
log "nginx started"

# --- Start crond in foreground (keeps container alive) ---
log "Starting crond..."
exec crond -f -l 6
