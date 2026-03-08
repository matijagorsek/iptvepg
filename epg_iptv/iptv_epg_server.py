#!/usr/bin/env python3
"""
Mali server koji dohvaća playlistu s tvog IPTV providera (get.php), dodaje tvg-id
svakom kanalu i servira EPG XML. U TiviMateu jednom postaviš dva URL-a i više
ne moraš ništa uploadati – sve se odrađuje u aplikaciji (dohvat s ovog servera).

Korištenje:
  1. Postavi .env u rootu projekta: IPTV_BASE_URL, IPTV_USERNAME, IPTV_PASSWORD
  2. Pokreni: python3 scripts/iptv_epg_server.py  (ili python3 -m epg_iptv.iptv_epg_server)
  3. U TiviMateu: Playlist URL = http://tvoj-server:8765/playlist.m3u
                  EPG URL      = http://tvoj-server:8765/epg.xml
"""

import os
import re
import time
import urllib.request
import xml.sax.saxutils as saxutils
from io import StringIO
from pathlib import Path

# Optional: Flask za jednostavan HTTP server
try:
    from flask import Flask, Response
except ImportError:
    Flask = None
    Response = None

# Cache: (raw_m3u, channels_list) ili None
_cache = None
_cache_time = 0
CACHE_SECONDS = 300  # 5 minuta


def load_env():
    # .env u rootu projekta (jedan nivo iznad epg_iptv/)
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def get_config():
    load_env()
    base = os.environ.get("IPTV_BASE_URL", "").rstrip("/")
    user = os.environ.get("IPTV_USERNAME", "")
    password = os.environ.get("IPTV_PASSWORD", "")
    if not base or not user or not password:
        raise ValueError(
            "Postavi IPTV_BASE_URL, IPTV_USERNAME i IPTV_PASSWORD u .env "
            "(npr. IPTV_BASE_URL=http://line.ottcst.com:80)"
        )
    return base, user, password


def fetch_m3u(base: str, user: str, password: str) -> str:
    url = f"{base}/get.php?username={user}&password={password}&type=m3u_plus"
    req = urllib.request.Request(url, headers={"User-Agent": "TiviMate-EPG-Proxy/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")


def extract_stream_id_from_url(url: str):
    """Iz URL-a tipa http://host:port/username/password/STREAM_ID izvuci STREAM_ID."""
    url = url.strip()
    if not url or url.startswith("#"):
        return None
    parts = url.rstrip("/").split("/")
    if len(parts) >= 1 and parts[-1].strip():
        last = parts[-1].split(".")[0]
        if last.isdigit():
            return last
    return None


def parse_extinf(line: str) -> dict:
    m = re.search(r'tvg-name="([^"]*)"', line)
    tvg_name = (m.group(1).strip() if m else "")
    m_id = re.search(r'tvg-id="([^"]*)"', line)
    tvg_id = (m_id.group(1).strip() if m_id else "")
    if "," in line:
        title = line.split(",", 1)[-1].strip()
        if not tvg_name:
            tvg_name = title
    return {"tvg_name": tvg_name or "Unknown", "tvg_id": tvg_id}


def escape_xml(text: str) -> str:
    return saxutils.escape(text)


def parse_m3u_and_inject_tvg_id(text: str):
    """
    Parsira M3U, za svaki kanal izvuče stream_id iz URL-a i eventualni tvg-id.
    Vraća listu (channel_id, display_name, extinf_line, url).
    channel_id = postojeći tvg-id ako provider šalje (npr. hrt1.hr), inače stream_id.
    """
    lines = text.splitlines()
    channels = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#EXTM3U"):
            i += 1
            continue
        if line.startswith("#EXTINF"):
            info = parse_extinf(line)
            url = ""
            if i + 1 < len(lines) and not lines[i + 1].startswith("#"):
                url = lines[i + 1].strip()
                i += 1
            stream_id = extract_stream_id_from_url(url) if url else None
            if stream_id:
                # Ako provider već šalje tvg-id (npr. hrt1.hr), zadrži ga za EPG/spajanje
                channel_id = info["tvg_id"] if (info.get("tvg_id") and info["tvg_id"].strip()) else stream_id
                channels.append((channel_id, info["tvg_name"], line, url))
            i += 1
            continue
        i += 1
    return channels


def build_m3u_with_tvg_id(channels: list) -> str:
    out = StringIO()
    out.write("#EXTM3U\n")
    for channel_id, _name, extinf, url in channels:
        if 'tvg-id=""' in extinf:
            new_extinf = extinf.replace('tvg-id=""', f'tvg-id="{escape_xml(channel_id)}"', 1)
        elif re.search(r'tvg-id="[^"]*"', extinf):
            # Provider već ima tvg-id – zadrži ga (ne prepisuj)
            new_extinf = re.sub(r'tvg-id="[^"]*"', f'tvg-id="{escape_xml(channel_id)}"', extinf, count=1)
        else:
            new_extinf = extinf.replace("#EXTINF:-1 ", f'#EXTINF:-1 tvg-id="{escape_xml(channel_id)}" ', 1)
        out.write(new_extinf + "\n")
        if url:
            out.write(url + "\n")
    return out.getvalue()


def build_epg_xml(channels: list) -> str:
    out = StringIO()
    out.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    out.write('<tv generator-info-name="iptv-epg-server">\n')
    for channel_id, name in ((c[0], c[1]) for c in channels):
        out.write(f'  <channel id="{escape_xml(channel_id)}">\n')
        out.write(f'    <display-name>{escape_xml(name)}</display-name>\n')
        out.write('  </channel>\n')
    out.write('</tv>\n')
    return out.getvalue()


def get_cached_or_fetch():
    global _cache, _cache_time
    now = time.time()
    if _cache is not None and (now - _cache_time) < CACHE_SECONDS:
        return _cache
    base, user, password = get_config()
    raw = fetch_m3u(base, user, password)
    channels = parse_m3u_and_inject_tvg_id(raw)
    _cache = (raw, channels)
    _cache_time = now
    return _cache


def serve_playlist():
    _raw, channels = get_cached_or_fetch()
    return build_m3u_with_tvg_id(channels)


def serve_epg():
    _raw, channels = get_cached_or_fetch()
    return build_epg_xml(channels)


def run_server():
    if Flask is None:
        print("Instaliraj Flask: pip install flask")
        return
    app = Flask(__name__)

    @app.route("/playlist.m3u")
    def playlist():
        try:
            body = serve_playlist()
            return Response(body, mimetype="audio/x-mpegurl", charset="utf-8")
        except Exception as e:
            return Response(f"Greška: {e}", status=502)

    @app.route("/epg.xml")
    def epg():
        try:
            body = serve_epg()
            return Response(body, mimetype="application/xml", charset="utf-8")
        except Exception as e:
            return Response(f"Greška: {e}", status=502)

    port = int(os.environ.get("PORT", "8765"))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"Server: http://{host}:{port}")
    print("  Playlist: http://<tvoj-ip>:{port}/playlist.m3u".format(port=port))
    print("  EPG:      http://<tvoj-ip>:{port}/epg.xml".format(port=port))
    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == "__main__":
    run_server()
