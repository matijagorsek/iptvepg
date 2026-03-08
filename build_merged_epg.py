#!/usr/bin/env python3
"""
Generira JEDAN EPG file (XMLTV) za učitavanje u TiviMate koji:
- sadrži SVE tvoje kanale (iz M3U) kao <channel> – svaki kanal ima ulaz u EPG-u;
- za kanale koji se poklapaju s iptv-epg.org uključuje i stvarne programe (TV vodič).

Nisu svi kanali imaju programe – samo oni koji postoje na iptv-epg.org (po zemljama).
Ostali kanali i dalje imaju <channel> u fileu (TiviMate ih prikaže), ali bez rasporeda.

Korištenje:
  python3 build_merged_epg.py /path/do/playliste.m3u -o epg_merged.xml [--limit-countries 40]
  U TiviMateu stavi EPG URL na ovaj file (npr. raw GitHub link na epg_merged.xml).
"""

import argparse
import io
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.request import Request, urlopen

# Import iz find_epg_links
from find_epg_links import (
    fetch_channel_ids_from_epg,
    get_epg_urls_fallback,
    parse_m3u_channels,
)


def escape_xml(text: str) -> str:
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def fetch_epg_content(epg_url: str, max_bytes: int = 25 * 1024 * 1024) -> Optional[bytes]:
    """Dohvati do max_bytes EPG XML-a; prati redirect (meta refresh)."""
    url = epg_url
    for _ in range(3):
        try:
            req = Request(url, headers={"User-Agent": "TiviMate-EPG-Merge/1.0"})
            with urlopen(req, timeout=60) as r:
                data = b""
                while len(data) < max_bytes:
                    chunk = r.read(128 * 1024)
                    if not chunk:
                        break
                    data += chunk
                text = data.decode("utf-8", errors="replace")
            if text.strip().startswith("<?xml") or text.strip().startswith("<tv"):
                return data
            m = re.search(r'url=["\']([^"\']+)["\']', text)
            if m:
                url = m.group(1).strip()
                continue
            break
        except Exception:
            return None
    return None


def build_source_to_our_id(
    source_channel_ids: Set[str], our_channel_ids_for_this_epg: List[str]
) -> Dict[str, str]:
    """Za EPG izvor: mapiranje source channel id -> naš channel_id (za ispis <programme>)."""
    mapping = {}
    our_lower = {c.lower(): c for c in our_channel_ids_for_this_epg}
    for sid in source_channel_ids:
        oid = our_lower.get(sid.lower())
        if oid:
            mapping[sid] = oid
    return mapping


def extract_programmes_from_xml(
    content: bytes, source_to_our: Dict[str, str], out_file
) -> int:
    """Stream-parse XML, za svaki <programme> čiji channel je u source_to_our upiši ga u out_file s channel=our_id. Vraća broj upisanih."""
    count = 0
    try:
        for event, elem in ET.iterparse(io.BytesIO(content), events=("end",)):
            if elem.tag == "programme":
                ch = elem.get("channel")
                our_id = source_to_our.get(ch) if ch else None
                if our_id is not None:
                    elem.set("channel", our_id)
                    out_file.write("  ")
                    out_file.write(ET.tostring(elem, encoding="unicode", method="xml"))
                    out_file.write("\n")
                    count += 1
                elem.clear()
    except ET.ParseError:
        pass
    return count


def main():
    ap = argparse.ArgumentParser(
        description="Napravi jedan EPG file za TiviMate sa svim kanalima i programima gdje ih ima"
    )
    ap.add_argument("m3u", help="Putanja do M3U playliste")
    ap.add_argument("-o", "--output", default="epg_merged.xml", help="Izlazni EPG file")
    ap.add_argument(
        "--limit-countries",
        type=int,
        default=None,
        help="Max broj zemalja za preuzimanje programa (default: sve)",
    )
    args = ap.parse_args()

    m3u_path = Path(args.m3u)
    if not m3u_path.exists():
        print(f"Datoteka ne postoji: {m3u_path}", file=sys.stderr)
        sys.exit(1)

    print("Učitavam kanale s M3U...")
    channels = parse_m3u_channels(str(m3u_path))
    print(f"  Ukupno kanala: {len(channels)}")

    epg_list = get_epg_urls_fallback()
    if args.limit_countries:
        epg_list = epg_list[: args.limit_countries]
    print(f"EPG izvora (zemalja): {len(epg_list)}")

    # channel_id (naš) -> epg_url
    channel_id_to_epg: Dict[str, str] = {}
    # epg_url -> set of source channel ids (iz tog EPG-a)
    epg_source_ids: Dict[str, Set[str]] = {}
    for country, epg_url in epg_list:
        ids = fetch_channel_ids_from_epg(epg_url)
        epg_source_ids[epg_url] = ids
        for cid in ids:
            if cid.lower() not in channel_id_to_epg:
                channel_id_to_epg[cid.lower()] = epg_url

    # Naši kanali koji imaju EPG izvor
    our_channels_with_epg = [
        (cid, name) for cid, name in channels if channel_id_to_epg.get(cid.lower())
    ]
    print(f"Kanala s dostupnim programom (iptv-epg.org): {len(our_channels_with_epg)}")

    out_path = Path(args.output)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<tv generator-info-name="epg-iptv-merged">\n')
        for cid, name in channels:
            f.write(f'  <channel id="{escape_xml(cid)}">\n')
            f.write(f'    <display-name>{escape_xml(name)}</display-name>\n')
            f.write("  </channel>\n")

        total_prog = 0
        for country, epg_url in epg_list:
            our_ids = [c for c, _ in our_channels_with_epg if channel_id_to_epg.get(c.lower()) == epg_url]
            if not our_ids:
                continue
            source_ids = epg_source_ids.get(epg_url) or set()
            source_to_our = build_source_to_our_id(source_ids, our_ids)
            if not source_to_our:
                continue
            print(f"  Preuzimam programe: {country} ...")
            content = fetch_epg_content(epg_url)
            if not content:
                continue
            n = extract_programmes_from_xml(content, source_to_our, f)
            total_prog += n
            print(f"    -> {n} programa")

        f.write("</tv>\n")

    print(f"Zapisano: {out_path}")
    print(f"Ukupno programa upisano: {total_prog}")
    print("U TiviMateu dodaj ovaj file kao EPG URL (npr. raw GitHub link).")


if __name__ == "__main__":
    main()
