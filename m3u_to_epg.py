#!/usr/bin/env python3
"""
Parsira M3U playlistu i generira:
1. XMLTV EPG datoteku (za TiviMate) s jednim <channel> po kanalu
2. Ažurirani M3U s tvg-id na svakom kanalu (spajanje s EPG-om)

Korištenje:
  python3 m3u_to_epg.py /path/to/playlist.m3u

Izlaz (u isti folder kao skripta):
  - epg.xml (XMLTV za TiviMate)
  - playlist_with_epg.m3u (M3U s tvg-id)
"""

import re
import sys
import xml.sax.saxutils as saxutils
from pathlib import Path


def sanitize_channel_id(name: str, seen: set) -> str:
    """Jedinstveni, XML-safe channel id od tvg-name."""
    # Ukloni ili zamijeni znakove neprikladne za XML id
    safe = re.sub(r'[^\w\s\-.]', '', name)
    safe = re.sub(r'\s+', '_', safe.strip()) or "channel"
    base = safe[:80]  # skrati
    id_ = base
    n = 0
    while id_ in seen:
        n += 1
        id_ = f"{base}_{n}"
    seen.add(id_)
    return id_


def parse_extinf(line: str) -> dict:
    """Iz #EXTINF:-1 tvg-id="" tvg-name="X" ... izvuci tvg-name (ili naslov)."""
    out = {}
    # tvg-name="..."
    m = re.search(r'tvg-name="([^"]*)"', line)
    out["tvg_name"] = (m.group(1).strip() if m else "")
    # Naslov je zadnji dio nakon zadnjeg zareza
    if "," in line:
        title = line.split(",", 1)[-1].strip()
        if not out["tvg_name"]:
            out["tvg_name"] = title
    if not out["tvg_name"]:
        out["tvg_name"] = "Unknown"
    return out


def escape_xml(text: str) -> str:
    return saxutils.escape(text)


def process_m3u(m3u_path: str, out_dir: Path):
    out_dir = Path(out_dir)
    epg_path = out_dir / "epg.xml"
    m3u_out_path = out_dir / "playlist_with_epg.m3u"

    seen_ids = set()
    channels = []  # (channel_id, display_name, extinf_line, url)

    with open(m3u_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#EXTM3U"):
            i += 1
            continue
        if line.startswith("#EXTINF"):
            info = parse_extinf(line)
            channel_id = sanitize_channel_id(info["tvg_name"], seen_ids)
            url = ""
            if i + 1 < len(lines) and not lines[i + 1].startswith("#"):
                url = lines[i + 1].rstrip()
                i += 1
            channels.append((channel_id, info["tvg_name"], line.rstrip(), url))
            i += 1
            continue
        i += 1

    # Upis XMLTV
    with open(epg_path, "w", encoding="utf-8") as xml_out:
        xml_out.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        xml_out.write('<tv generator-info-name="m3u_to_epg">\n')
        for cid, name in ((c[0], c[1]) for c in channels):
            xml_out.write(f'  <channel id="{escape_xml(cid)}">\n')
            xml_out.write(f'    <display-name>{escape_xml(name)}</display-name>\n')
            xml_out.write('  </channel>\n')
        xml_out.write('</tv>\n')

    # Upis M3U s tvg-id i URL-ovima
    with open(m3u_out_path, "w", encoding="utf-8") as m3u_out:
        m3u_out.write("#EXTM3U\n")
        for channel_id, _display_name, extinf, url in channels:
            if 'tvg-id=""' in extinf:
                new_extinf = extinf.replace('tvg-id=""', f'tvg-id="{escape_xml(channel_id)}"', 1)
            elif re.search(r'tvg-id="[^"]*"', extinf):
                new_extinf = re.sub(r'tvg-id="[^"]*"', f'tvg-id="{escape_xml(channel_id)}"', extinf, count=1)
            else:
                new_extinf = extinf.replace("#EXTINF:-1 ", f'#EXTINF:-1 tvg-id="{escape_xml(channel_id)}" ', 1)
            m3u_out.write(new_extinf + "\n")
            if url:
                m3u_out.write(url + "\n")

    return len(channels)


def main():
    if len(sys.argv) < 2:
        print("Korištenje: python3 m3u_to_epg.py <putanja_do_playliste.m3u> [izlazni_folder]")
        print("  Izlazni folder po defaultu: isti kao skripta (epg-iptv)")
        sys.exit(1)
    m3u_path = Path(sys.argv[1]).resolve()
    if not m3u_path.exists():
        print(f"Datoteka ne postoji: {m3u_path}")
        sys.exit(1)
    out_dir = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path(__file__).resolve().parent
    out_dir.mkdir(parents=True, exist_ok=True)
    n = process_m3u(str(m3u_path), out_dir)
    print(f"Gotovo. Obradeno kanala: {n}")
    print(f"  EPG (XML):     {out_dir / 'epg.xml'}")
    print(f"  Playlist M3U:  {out_dir / 'playlist_with_epg.m3u'}")


if __name__ == "__main__":
    main()