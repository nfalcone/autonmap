# AutoNmap

Scheduled nmap scanning with a human-readable web dashboard. Runs in Docker on Alpine Linux.

## What it does

- Runs `nmap` on your configured targets on a cron schedule
- Saves each scan as XML (raw) + HTML (rendered, human-readable)
- Diffs each scan against the previous one: new hosts, disappeared hosts, port changes
- Serves everything via nginx on port 80 — browse to `http://your-server:8080`

## Quick start

1. Clone this repo
2. Edit `docker-compose.yml` — set `NMAP_TARGETS` to your network(s)
3. Replace `YOUR_GITHUB_USERNAME` in the image name with your actual GitHub username

```bash
docker compose pull
docker compose up -d
```

Then open `http://your-server:8080` — the first scan runs immediately on startup.

## Configuration (docker-compose.yml environment)

| Variable | Default | Description |
|---|---|---|
| `NMAP_TARGETS` | *(required)* | Space-separated targets: CIDRs, IPs, ranges |
| `NMAP_FLAGS` | `-sn` | nmap flags. `-sn` = ping sweep only |
| `SCAN_CRON` | `0 * * * *` | Cron schedule (default: top of every hour) |
| `SCAN_ON_START` | `true` | Run a scan immediately when container starts |
| `TZ` | `UTC` | Timezone for scan timestamps |

### Common flag combinations

```
# Ping sweep only (fastest, no port scan)
NMAP_FLAGS=-sn

# Ping sweep + service detection on common ports
NMAP_FLAGS=-sV --open -T4

# Full service + OS detection (requires NET_RAW cap)
NMAP_FLAGS=-sV -O --open -T4

# Specific ports
NMAP_FLAGS=-p 22,80,443,3389,8080 --open
```

### Multiple targets

```yaml
- NMAP_TARGETS=10.10.0.0/24 10.20.0.0/24 10.30.50.0/24
```

## Output structure

```
/data/scans/
├── index.html                    ← auto-regenerated after every scan
├── scan_20260513_120000.xml      ← raw nmap output
├── scan_20260513_120000.html     ← rendered scan report
├── diff_20260513_120000.html     ← diff vs previous scan
├── scan_20260513_130000.xml
├── scan_20260513_130000.html
├── diff_20260513_130000.html
└── nmap.xsl                      ← lets raw XML render in Firefox
```

## Updating

Push a change to `main` → GitHub Actions builds a new image → pull it on your server:

```bash
docker compose pull && docker compose up -d
```

Or set up Watchtower to auto-pull:

```yaml
services:
  watchtower:
    image: containrrr/watchtower
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    command: --interval 300 autonmap   # check every 5 minutes
```

## Viewing logs

```bash
# Container logs (cron + entrypoint)
docker compose logs -f

# Scan log inside container
docker compose exec autonmap tail -f /var/log/autonmap/scan.log
```

## Notes

- Scan history is persisted in the `autonmap_data` Docker volume — survives container restarts and image updates
- `NET_RAW` / `NET_ADMIN` capabilities are needed for OS detection (`-O`) and SYN scans (`-sS`). For ping sweeps only (`-sn`) you can remove those from docker-compose.yml
- The raw `.xml` files will render nicely in Firefox (uses `nmap.xsl`) but not Chrome (Chrome blocks local XSL for security)
