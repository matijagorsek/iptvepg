#!/usr/bin/env python3
"""
Skripta za GitHub Actions: čita IPTV_* iz okoline, dohvaća M3U s providera,
generira playlist_with_epg.m3u i epg.xml te ih sprema u zadani folder (npr. output/).
Pokreni iz roota projekta: python3 scripts/generate_epg_github.py output
"""

import os
import sys
from pathlib import Path

# Root projekta u path
_SCRIPT_DIR = Path(__file__).resolve().parent
_ROOT = _SCRIPT_DIR.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from epg_iptv.iptv_epg_server import (
    parse_m3u_and_inject_tvg_id,
    build_m3u_with_tvg_id,
    build_epg_xml,
)


def get_config():
    base = os.environ.get("IPTV_BASE_URL", "").rstrip("/")
    user = os.environ.get("IPTV_USERNAME", "")
    password = os.environ.get("IPTV_PASSWORD", "")
    if not base or not user or not password:
        raise ValueError(
            "Postavi IPTV_BASE_URL, IPTV_USERNAME i IPTV_PASSWORD (env ili GitHub Secrets)"
        )
    return base, user, password


def fetch_m3u(base: str, user: str, password: str) -> str:
    import http.client
    import urllib.request
    url = f"{base}/get.php?username={user}&password={password}&type=m3u_plus"
    req = urllib.request.Request(url, headers={"User-Agent": "TiviMate-EPG-GitHub/1.0"})
    chunks = []
    chunk_size = 1024 * 1024  # 1 MB
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                while True:
                    chunk = r.read(chunk_size)
                    if not chunk:
                        break
                    chunks.append(chunk)
            return b"".join(chunks).decode("utf-8", errors="replace")
        except (http.client.IncompleteRead, OSError) as e:
            if attempt < max_retries - 1:
                print(f"  Prekid veze ({e}), ponovni pokušaj {attempt + 2}/{max_retries}...")
            else:
                raise


def main():
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "output")
    out_dir.mkdir(parents=True, exist_ok=True)

    base, user, password = get_config()
    print("Dohvaćam playlistu s providera...")
    raw = fetch_m3u(base, user, password)
    channels = parse_m3u_and_inject_tvg_id(raw)
    print(f"Obradeno kanala: {len(channels)}")

    playlist_path = out_dir / "playlist_with_epg.m3u"
    epg_path = out_dir / "epg.xml"
    playlist_path.write_text(build_m3u_with_tvg_id(channels), encoding="utf-8")
    epg_path.write_text(build_epg_xml(channels), encoding="utf-8")
    print(f"Zapisano: {playlist_path}, {epg_path}")


if __name__ == "__main__":
    main()
