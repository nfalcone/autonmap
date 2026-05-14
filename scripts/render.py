#!/usr/bin/env python3
"""
render.py — AutoNmap HTML renderer

Usage:
  render.py <current.xml> [<previous.xml>]   Render scan (+ diff if previous given)
  render.py --index-only                      Regenerate index.html only
"""

import sys
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from ipaddress import ip_address

SCAN_DIR = Path('/data/scans')

# ---------------------------------------------------------------------------
# Shared page chrome
# ---------------------------------------------------------------------------

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: #0d1117;
    color: #c9d1d9;
    font-size: 14px;
    line-height: 1.5;
}
a { color: #58a6ff; text-decoration: none; }
a:hover { text-decoration: underline; }

header {
    background: #161b22;
    border-bottom: 1px solid #30363d;
    padding: 0.9rem 1.5rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}
header h1 { font-size: 1.1rem; font-weight: 600; color: #f0f6fc; }
header .subtitle { font-size: 0.78rem; color: #6e7681; margin-top: 0.15rem; }
header .logo { font-size: 1.4rem; }

.container { padding: 1.25rem 1.5rem; max-width: 1400px; margin: 0 auto; }

.back {
    display: inline-flex; align-items: center; gap: 0.3rem;
    font-size: 0.8rem; color: #6e7681; margin-bottom: 1.1rem;
}
.back:hover { color: #c9d1d9; }

/* Stats row */
.stats { display: flex; flex-wrap: wrap; gap: 0.75rem; margin-bottom: 1.25rem; }
.stat-card {
    background: #161b22; border: 1px solid #30363d;
    border-radius: 6px; padding: 0.6rem 1rem; min-width: 130px;
}
.stat-card .label { font-size: 0.68rem; color: #6e7681; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.2rem; }
.stat-card .value { font-size: 1.4rem; font-weight: 700; color: #f0f6fc; }
.stat-card .value.sm { font-size: 0.9rem; }

/* Tables */
.table-wrap { overflow-x: auto; border: 1px solid #30363d; border-radius: 6px; }
table { width: 100%; border-collapse: collapse; }
thead th {
    background: #161b22; color: #8b949e;
    font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em;
    padding: 0.6rem 0.9rem; text-align: left;
    border-bottom: 1px solid #30363d;
    white-space: nowrap;
}
tbody td { padding: 0.5rem 0.9rem; border-bottom: 1px solid #21262d; vertical-align: top; }
tbody tr:last-child td { border-bottom: none; }
tbody tr:hover td { background: #1c2128; }

/* Port badges */
.ports { display: flex; flex-wrap: wrap; gap: 3px; }
.badge {
    display: inline-block; padding: 1px 6px; border-radius: 4px;
    font-size: 0.72rem; font-family: 'Cascadia Code', 'Consolas', monospace;
    white-space: nowrap;
}
.badge-tcp { background: #0d2444; color: #79c0ff; border: 1px solid #1f4b7a; }
.badge-udp { background: #2d1b3d; color: #d2a8ff; border: 1px solid #5a3278; }
.none { color: #484f58; }

/* Diff row styles */
.row-new td:first-child { border-left: 3px solid #3fb950; }
.row-new { background: #0a1f0a; }
.row-gone td:first-child { border-left: 3px solid #f85149; }
.row-gone { background: #1f0a0a; }
.row-changed td:first-child { border-left: 3px solid #e3b341; }
.row-changed { background: #1a1500; }

/* Tags */
.tag {
    display: inline-flex; align-items: center;
    padding: 1px 7px; border-radius: 9999px;
    font-size: 0.68rem; font-weight: 600; letter-spacing: 0.03em;
    white-space: nowrap;
}
.tag-new     { background: #0d3318; color: #3fb950; border: 1px solid #1f5c2e; }
.tag-gone    { background: #3d0c0c; color: #f85149; border: 1px solid #7a2020; }
.tag-changed { background: #3a2800; color: #e3b341; border: 1px solid #7a5a00; }
.tag-nochange{ background: #161b22; color: #6e7681; border: 1px solid #30363d; }

/* Section headers */
.section-header {
    font-size: 0.85rem; font-weight: 600; margin: 1.5rem 0 0.6rem;
    display: flex; align-items: center; gap: 0.5rem;
}

/* Summary banner */
.diff-summary {
    background: #161b22; border: 1px solid #30363d;
    border-radius: 6px; padding: 0.9rem 1.1rem;
    margin-bottom: 1.25rem; font-size: 0.85rem; color: #8b949e;
}
.diff-summary .tags { margin-top: 0.5rem; display: flex; gap: 0.5rem; flex-wrap: wrap; }

/* Index history table */
.scan-link { font-family: monospace; font-size: 0.8rem; }

/* Empty state */
.empty { text-align: center; padding: 3rem 1rem; color: #484f58; }
.empty .icon { font-size: 2rem; margin-bottom: 0.5rem; }

code { font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 0.85em; }

/* Argline */
.argline {
    font-family: monospace; font-size: 0.72rem; color: #484f58;
    margin-top: 0.4rem; word-break: break-all;
}
"""

def html_page(title: str, subtitle: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — AutoNmap</title>
  <style>{CSS}</style>
</head>
<body>
<header>
  <span class="logo">🔍</span>
  <div>
    <h1>{title}</h1>
    <div class="subtitle">{subtitle}</div>
  </div>
</header>
<div class="container">
{body}
</div>
</body>
</html>"""

# ---------------------------------------------------------------------------
# nmap XML parser
# ---------------------------------------------------------------------------

def parse_xml(xml_path: Path) -> tuple[dict, list[dict]]:
    """Parse an nmap XML file. Returns (meta, hosts)."""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    meta = {
        'args': root.get('args', ''),
        'startstr': root.get('startstr', 'Unknown'),
        'version': root.get('version', ''),
    }
    runstats = root.find('runstats/finished')
    if runstats is not None:
        meta['elapsed']  = runstats.get('elapsed', '?')
        meta['summary']  = runstats.get('summary', '')

    hosts = []
    for host in root.findall('host'):
        status = host.find('status')
        if status is None or status.get('state') != 'up':
            continue

        ip = mac = mac_vendor = hostname = os_name = ''

        for addr in host.findall('address'):
            t = addr.get('addrtype', '')
            if t == 'ipv4':
                ip = addr.get('addr', '')
            elif t == 'mac':
                mac = addr.get('addr', '')
                mac_vendor = addr.get('vendor', '')

        hostnames_el = host.find('hostnames')
        if hostnames_el is not None:
            # prefer PTR, then any
            hn = hostnames_el.find('hostname[@type="PTR"]')
            if hn is None:
                hn = hostnames_el.find('hostname')
            if hn is not None:
                hostname = hn.get('name', '')

        ports = []
        ports_el = host.find('ports')
        if ports_el is not None:
            for port in ports_el.findall('port'):
                st = port.find('state')
                if st is None or st.get('state') != 'open':
                    continue
                svc = port.find('service')
                svc_name    = svc.get('name', '')    if svc is not None else ''
                svc_product = svc.get('product', '') if svc is not None else ''
                svc_ver     = svc.get('version', '') if svc is not None else ''
                label = svc_name
                if svc_product:
                    label = svc_product
                    if svc_ver:
                        label += f' {svc_ver}'
                ports.append({
                    'portid':  port.get('portid', ''),
                    'proto':   port.get('protocol', 'tcp'),
                    'service': label,
                })

        os_el = host.find('os')
        if os_el is not None:
            osm = os_el.find('osmatch')
            if osm is not None:
                os_name = osm.get('name', '')

        hosts.append({
            'ip':         ip,
            'hostname':   hostname,
            'mac':        mac,
            'mac_vendor': mac_vendor,
            'ports':      ports,
            'os':         os_name,
            # frozenset for fast diffing
            '_ports_key': frozenset((p['portid'], p['proto']) for p in ports),
        })

    # Sort by IP numerically
    def ip_sort_key(h):
        try:
            return ip_address(h['ip'])
        except Exception:
            return ip_address('0.0.0.0')

    hosts.sort(key=ip_sort_key)
    return meta, hosts

# ---------------------------------------------------------------------------
# HTML fragments
# ---------------------------------------------------------------------------

def port_badges_html(ports: list[dict]) -> str:
    if not ports:
        return '<span class="none">—</span>'
    sorted_ports = sorted(ports, key=lambda p: int(p['portid']) if p['portid'].isdigit() else 0)
    parts = []
    for p in sorted_ports:
        cls = 'badge-udp' if p['proto'] == 'udp' else 'badge-tcp'
        tip = p['service'] if p['service'] else p['proto']
        label = f"{p['portid']}"
        if p['service']:
            label += f"&nbsp;<span style='opacity:.7'>{p['service']}</span>"
        else:
            label += f"/{p['proto']}"
        parts.append(f'<span class="badge {cls}" title="{tip}">{label}</span>')
    return f'<div class="ports">{"".join(parts)}</div>'

def host_table_html(hosts: list[dict], row_class: str = '', tag_html: str = '') -> str:
    if not hosts:
        return ''
    rows = []
    for h in hosts:
        tag_cell = f'<td>{tag_html}</td>' if tag_html else ''
        rows.append(f"""<tr class="{row_class}">
  {tag_cell}
  <td><code>{h['ip']}</code></td>
  <td>{h['hostname'] or '<span class="none">—</span>'}</td>
  <td>
    {'<code style="font-size:0.72rem">'+h['mac']+'</code>' if h['mac'] else '<span class="none">—</span>'}
    {'<span style="color:#6e7681;font-size:0.72rem"> '+h['mac_vendor']+'</span>' if h['mac_vendor'] else ''}
  </td>
  <td>{port_badges_html(h['ports'])}</td>
  <td style="color:#6e7681;font-size:0.75rem">{h['os'] or '<span class="none">—</span>'}</td>
</tr>""")
    return '\n'.join(rows)

def table_wrap(thead: str, tbody: str) -> str:
    return f'<div class="table-wrap"><table><thead>{thead}</thead><tbody>{tbody}</tbody></table></div>'

# ---------------------------------------------------------------------------
# Scan renderer
# ---------------------------------------------------------------------------

def render_scan(xml_path: Path, out_path: Path):
    meta, hosts = parse_xml(xml_path)
    elapsed = meta.get('elapsed', '?')

    stats_html = f"""<div class="stats">
  <div class="stat-card">
    <div class="label">Hosts Up</div>
    <div class="value">{len(hosts)}</div>
  </div>
  <div class="stat-card">
    <div class="label">Scan Time</div>
    <div class="value sm">{meta['startstr']}</div>
  </div>
  <div class="stat-card">
    <div class="label">Elapsed</div>
    <div class="value">{elapsed}s</div>
  </div>
</div>
<div class="argline">{meta['args']}</div>
<br>"""

    if not hosts:
        table_html = '<div class="empty"><div class="icon">📭</div>No hosts found in this scan.</div>'
    else:
        thead = '<tr><th>IP Address</th><th>Hostname</th><th>MAC / Vendor</th><th>Open Ports</th><th>OS</th></tr>'
        tbody = host_table_html(hosts)
        table_html = table_wrap(thead, tbody)

    body = f'<a class="back" href="index.html">← Scan history</a>\n{stats_html}\n{table_html}'
    out_path.write_text(html_page(f'Scan — {meta["startstr"]}', meta['args'], body))

# ---------------------------------------------------------------------------
# Diff renderer
# ---------------------------------------------------------------------------

def diff_hosts(prev: list[dict], curr: list[dict]) -> tuple[list, list, list]:
    """Returns (added, removed, changed). changed items include port delta."""
    prev_map = {h['ip']: h for h in prev}
    curr_map = {h['ip']: h for h in curr}

    added   = [h for ip, h in curr_map.items() if ip not in prev_map]
    removed = [h for ip, h in prev_map.items() if ip not in curr_map]
    changed = []
    for ip in set(prev_map) & set(curr_map):
        p, c = prev_map[ip], curr_map[ip]
        if p['_ports_key'] != c['_ports_key']:
            prev_port_set = {(x['portid'], x['proto']): x for x in p['ports']}
            curr_port_set = {(x['portid'], x['proto']): x for x in c['ports']}
            opened = [x for k, x in curr_port_set.items() if k not in prev_port_set]
            closed = [x for k, x in prev_port_set.items() if k not in curr_port_set]
            changed.append({'host': c, 'opened': opened, 'closed': closed})

    try:
        added.sort(key=lambda h: ip_address(h['ip']))
        removed.sort(key=lambda h: ip_address(h['ip']))
        changed.sort(key=lambda c: ip_address(c['host']['ip']))
    except Exception:
        pass

    return added, removed, changed

def render_diff(prev_xml: Path, curr_xml: Path, out_path: Path) -> tuple[int, int, int]:
    prev_meta, prev_hosts = parse_xml(prev_xml)
    curr_meta, curr_hosts = parse_xml(curr_xml)
    added, removed, changed = diff_hosts(prev_hosts, curr_hosts)

    sections = []

    # Summary banner
    tag_parts = []
    if added:   tag_parts.append(f'<span class="tag tag-new">+{len(added)} new</span>')
    if removed: tag_parts.append(f'<span class="tag tag-gone">−{len(removed)} gone</span>')
    if changed: tag_parts.append(f'<span class="tag tag-changed">~{len(changed)} changed</span>')
    if not tag_parts:
        tag_parts = ['<span class="tag tag-nochange">No changes detected</span>']

    sections.append(f"""<div class="diff-summary">
  Comparing <code>{prev_xml.name}</code> → <code>{curr_xml.name}</code>
  <div class="tags">{"".join(tag_parts)}</div>
</div>""")

    # --- Added hosts ---
    if added:
        thead = '<tr><th></th><th>IP Address</th><th>Hostname</th><th>MAC / Vendor</th><th>Open Ports</th><th>OS</th></tr>'
        tbody = host_table_html(added, row_class='row-new', tag_html='<span class="tag tag-new">NEW</span>')
        sections.append(f'<div class="section-header"><span style="color:#3fb950">◆</span> New Hosts ({len(added)})</div>'
                        + table_wrap(thead, tbody))

    # --- Removed hosts ---
    if removed:
        thead = '<tr><th></th><th>IP Address</th><th>Hostname</th><th>MAC / Vendor</th><th>Last Known Ports</th><th>OS</th></tr>'
        tbody = host_table_html(removed, row_class='row-gone', tag_html='<span class="tag tag-gone">GONE</span>')
        sections.append(f'<div class="section-header"><span style="color:#f85149">◆</span> Disappeared Hosts ({len(removed)})</div>'
                        + table_wrap(thead, tbody))

    # --- Changed hosts ---
    if changed:
        rows = []
        for c in changed:
            h = c['host']
            delta_parts = []
            if c['opened']:
                delta_parts.append(
                    f'<div style="margin-bottom:4px"><span style="color:#3fb950;font-size:0.7rem;font-weight:600">OPENED&nbsp;</span>'
                    f'{port_badges_html(c["opened"])}</div>'
                )
            if c['closed']:
                delta_parts.append(
                    f'<div><span style="color:#f85149;font-size:0.7rem;font-weight:600">CLOSED&nbsp;</span>'
                    f'{port_badges_html(c["closed"])}</div>'
                )
            rows.append(f"""<tr class="row-changed">
  <td><span class="tag tag-changed">CHANGED</span></td>
  <td><code>{h['ip']}</code></td>
  <td>{h['hostname'] or '<span class="none">—</span>'}</td>
  <td>{''.join(delta_parts)}</td>
</tr>""")
        thead = '<tr><th></th><th>IP Address</th><th>Hostname</th><th>Port Changes</th></tr>'
        sections.append(
            f'<div class="section-header"><span style="color:#e3b341">◆</span> Changed Hosts ({len(changed)})</div>'
            + table_wrap(thead, '\n'.join(rows))
        )

    # --- No changes ---
    if not added and not removed and not changed:
        sections.append("""<div style="background:#161b22;border:1px solid #30363d;border-radius:6px;
            padding:2rem;text-align:center;color:#6e7681;margin-top:1rem">
  ✅ No changes detected between scans.
</div>""")

    body = '<a class="back" href="index.html">← Scan history</a>\n' + '\n'.join(sections)
    subtitle = f'{curr_meta["startstr"]} vs previous'
    out_path.write_text(html_page('Scan Diff', subtitle, body))

    return len(added), len(removed), len(changed)

# ---------------------------------------------------------------------------
# Index generator
# ---------------------------------------------------------------------------

def ts_from_stem(stem: str) -> datetime:
    """scan_20260513_120000 → datetime"""
    parts = stem.split('_', 1)  # ['scan', '20260513_120000']
    if len(parts) == 2:
        try:
            return datetime.strptime(parts[1], '%Y%m%d_%H%M%S')
        except ValueError:
            pass
    return datetime.min

def gen_index():
    scan_files = sorted(
        SCAN_DIR.glob('scan_[0-9]*.xml'),
        key=lambda p: p.stem,
        reverse=True
    )
    # exclude scan_latest.xml
    scan_files = [f for f in scan_files if f.stem != 'scan_latest']

    if not scan_files:
        body = '''<div class="empty">
  <div class="icon">📡</div>
  <div>No scans yet. The first scan will run on schedule (or immediately if SCAN_ON_START=true).</div>
</div>'''
        (SCAN_DIR / 'index.html').write_text(html_page('AutoNmap Dashboard', 'Network Scan History', body))
        return

    # Latest scan stats for the header
    try:
        latest_meta, latest_hosts = parse_xml(scan_files[0])
        latest_time = latest_meta['startstr']
        latest_count = len(latest_hosts)
    except Exception:
        latest_time = '—'
        latest_count = '?'

    stats_html = f"""<div class="stats">
  <div class="stat-card">
    <div class="label">Latest Scan</div>
    <div class="value sm">{latest_time}</div>
  </div>
  <div class="stat-card">
    <div class="label">Hosts Up (Latest)</div>
    <div class="value">{latest_count}</div>
  </div>
  <div class="stat-card">
    <div class="label">Total Scans</div>
    <div class="value">{len(scan_files)}</div>
  </div>
</div>"""

    rows = []
    for xml_path in scan_files:
        stem = xml_path.stem   # scan_20260513_120000
        ts_part = stem[5:]     # 20260513_120000

        try:
            dt = datetime.strptime(ts_part, '%Y%m%d_%H%M%S')
            dt_display = dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            dt_display = ts_part

        html_file = xml_path.with_suffix('.html')
        diff_file = SCAN_DIR / f'diff_{ts_part}.html'

        # Host count
        try:
            _, hosts = parse_xml(xml_path)
            host_count = str(len(hosts))
        except Exception:
            host_count = '?'

        scan_link = f'<a href="{html_file.name}">{dt_display}</a>'

        if diff_file.exists():
            diff_link = f'<a href="{diff_file.name}">View diff</a>'
        else:
            diff_link = '<span class="none">—</span>'

        rows.append(f"""<tr>
  <td class="scan-link">{scan_link}</td>
  <td style="font-variant-numeric:tabular-nums">{host_count}</td>
  <td>{diff_link}</td>
  <td style="color:#484f58"><a href="{xml_path.name}" style="color:#484f58">{xml_path.name}</a></td>
</tr>""")

    thead = '<tr><th>Scan Time</th><th>Hosts Up</th><th>Changes</th><th>Raw XML</th></tr>'
    table_html = table_wrap(thead, '\n'.join(rows))

    body = stats_html + '\n' + table_html
    (SCAN_DIR / 'index.html').write_text(
        html_page('AutoNmap Dashboard', 'Network Scan History', body)
    )

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    args = sys.argv[1:]

    if not args or args[0] == '--index-only':
        gen_index()
        print("index.html regenerated")
        sys.exit(0)

    curr_xml = Path(args[0])
    prev_xml = Path(args[1]) if len(args) > 1 else None

    if not curr_xml.exists():
        print(f"ERROR: {curr_xml} does not exist", file=sys.stderr)
        sys.exit(1)

    # Render scan
    scan_html = curr_xml.with_suffix('.html')
    render_scan(curr_xml, scan_html)
    print(f"Scan rendered: {scan_html.name}")

    # Render diff
    if prev_xml and prev_xml.exists() and prev_xml != curr_xml:
        ts_part = curr_xml.stem[5:]   # strip 'scan_'
        diff_html = SCAN_DIR / f'diff_{ts_part}.html'
        added, removed, changed = render_diff(prev_xml, curr_xml, diff_html)
        print(f"Diff rendered: {diff_html.name}  (+{added} new, -{removed} gone, ~{changed} changed)")
    else:
        if prev_xml:
            print(f"Skipping diff: {prev_xml} not found")

    # Always regenerate index
    gen_index()
    print("index.html regenerated")
