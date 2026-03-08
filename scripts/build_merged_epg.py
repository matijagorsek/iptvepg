#!/usr/bin/env python3
"""
Generira JEDAN EPG file (XMLTV) za učitavanje u TiviMate koji:
- sadrži SVE tvoje kanale (iz M3U) kao <channel> – svaki kanal ima ulaz u EPG-u;
- za kanale koji se poklapaju s iptv-epg.org uključuje i stvarne programe (TV vodič).

Korištenje (iz roota projekta):
  python3 scripts/build_merged_epg.py /path/do/playliste.m3u -o epg_merged.xml [--limit-countries 40]
"""

import argparse
import io
import re
import sys
from pathlib import Path

# Dodaj root projekta u path da se nađe epg_iptv
_SCRIPT_DIR = Path(__file__).resolve().parent
_ROOT = _SCRIPT_DIR.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set, Tuple
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from epg_iptv.find_epg_links import (
    fetch_channel_ids_from_epg,
    fetch_channel_ids_and_names_from_epg,
    get_epg_urls_fallback,
    get_epg_urls_de,
    get_epg_urls_exyu,
    get_epg_urls_uk,
    get_epg_urls_usa,
    get_epg_urls_with_playwright,
    parse_m3u_channels,
    parse_m3u_channels_with_groups,
)
from epg_iptv.epg_sources_exact import get_tvprofil_exact_sources, TVPROFIL_ALIASES
from epg_iptv.channel_aliases import all_lookup_variants, name_match_variants_for_region


def normalize_channel_name(name: str) -> str:
    """Normalizira ime za usporedbu: uklanja prefikse |XX|, HD/FHD/4K, specijalne znakove, lower."""
    if not name:
        return ""
    s = name.strip().lower()
    s = re.sub(r"^\|[^|]+\|\s*", "", s)
    s = re.sub(r"\s*\|[^|]+\|$", "", s)
    s = re.sub(r"\b(hd|fhd|uhd|4k|raw|ᴿᴬᵂ|ᴴᴰ|ᵁᴴᴰ|⁴ᴷ)\b", "", s, flags=re.IGNORECASE)
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


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
    source_channel_ids: Set[str],
    our_channel_ids_for_this_epg: List[str],
    source_channels_with_names: List[Tuple[str, str]],
    our_channels_all: List[Tuple[str, str]],
    exclude_our_ids: Optional[Set[str]] = None,
    use_name_aliases_region: Optional[str] = None,
) -> Dict[str, str]:
    exclude_our_ids = exclude_our_ids or set()
    mapping: Dict[str, str] = {}
    our_lower: Dict[str, str] = {}
    for c in our_channel_ids_for_this_epg:
        for variant in all_lookup_variants(c):
            our_lower[variant] = c
    for sid in source_channel_ids:
        oid = our_lower.get(sid.lower())
        if oid and oid not in exclude_our_ids:
            mapping[sid] = oid
    assigned_epg = set(mapping.keys())
    assigned_our = set(mapping.values())
    epg_norm_to_id = [(normalize_channel_name(name), epg_id) for epg_id, name in source_channels_with_names if name]
    for our_id, our_name in our_channels_all:
        if our_id in assigned_our or our_id in exclude_our_ids:
            continue
        norm_our = normalize_channel_name(our_name)
        if not norm_our or len(norm_our) < 2:
            continue
        our_accept: List[str] = [norm_our]
        if use_name_aliases_region:
            our_accept = name_match_variants_for_region(norm_our, use_name_aliases_region)
        for norm_epg, epg_id in epg_norm_to_id:
            if epg_id in assigned_epg:
                continue
            match = norm_epg in our_accept or norm_our == norm_epg
            if not match and len(norm_epg) >= 3:
                match = norm_our in norm_epg or norm_epg in norm_our
            if not match and use_name_aliases_region:
                for a in our_accept:
                    if a and len(a) >= 2 and (a == norm_epg or (len(norm_epg) >= 3 and (a in norm_epg or norm_epg in a))):
                        match = True
                        break
            if match:
                mapping[epg_id] = our_id
                assigned_epg.add(epg_id)
                assigned_our.add(our_id)
                break
    return mapping


def _parse_programme_start(start_attr: Optional[str]):
    if not start_attr or len(start_attr) < 14:
        return None
    try:
        s = start_attr.strip()[:14]
        return datetime(
            int(s[:4]), int(s[4:6]), int(s[6:8]),
            int(s[8:10]), int(s[10:12]), int(s[12:14]),
            tzinfo=timezone.utc,
        )
    except (ValueError, TypeError):
        return None


def extract_programmes_from_xml(
    content: bytes,
    source_to_our: Dict[str, str],
    out_file,
    max_days_ahead: int = 7,
) -> Tuple[int, Set[str]]:
    count = 0
    our_ids_with_programme: Set[str] = set()
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(days=max_days_ahead)
    try:
        for event, elem in ET.iterparse(io.BytesIO(content), events=("end",)):
            if elem.tag == "programme":
                ch = elem.get("channel")
                our_id = source_to_our.get(ch) if ch else None
                if our_id is not None:
                    start_dt = _parse_programme_start(elem.get("start"))
                    if start_dt is not None and (start_dt > cutoff or start_dt < now - timedelta(hours=12)):
                        elem.clear()
                        continue
                    elem.set("channel", our_id)
                    out_file.write("  ")
                    out_file.write(ET.tostring(elem, encoding="unicode", method="xml"))
                    out_file.write("\n")
                    count += 1
                    our_ids_with_programme.add(our_id)
                elem.clear()
    except ET.ParseError:
        pass
    return count, our_ids_with_programme


def main():
    ap = argparse.ArgumentParser(
        description="Napravi jedan EPG file za TiviMate sa svim kanalima i programima gdje ih ima"
    )
    ap.add_argument("m3u", help="Putanja do M3U playliste")
    ap.add_argument("-o", "--output", default="epg_merged.xml", help="Izlazni EPG file")
    ap.add_argument("--limit-countries", type=int, default=None, help="Max broj zemalja")
    ap.add_argument("--use-playwright", action="store_true", help="Dohvati EPG URL-ove preko Playwrighta")
    ap.add_argument("--max-days", type=int, default=7, help="Samo programme unutar N dana")
    ap.add_argument("--exclude-group-pattern", type=str, default=None, help="Regex za group-title (isključi kanale)")
    ap.add_argument("--skip-vod", action="store_true", help="Preskoči VOD/videoteka grupe")
    ap.add_argument(
        "--focus-exyu",
        action="store_true",
        help="Samo EXYU zemlje (AL,BA,HR,ME,MK,RS,SI) + name matching za ex-Yu kanale",
    )
    ap.add_argument(
        "--focus-uk",
        action="store_true",
        help="Samo UK (GB) + name matching za britanske kanale",
    )
    ap.add_argument(
        "--focus-usa",
        action="store_true",
        help="Samo USA (US) + name matching za američke kanale",
    )
    ap.add_argument(
        "--focus-de",
        action="store_true",
        help="Samo Njemačka (DE) + name matching za njemačke kanale",
    )
    ap.add_argument(
        "--only-countries",
        type=str,
        default=None,
        help="Samo ove zemlje (ISO kodovi odvojeni zarezom, npr. HR,BA,RS,SI,ME,MK,AL)",
    )
    args = ap.parse_args()

    m3u_path = Path(args.m3u)
    if not m3u_path.exists():
        print(f"Datoteka ne postoji: {m3u_path}", file=sys.stderr)
        sys.exit(1)

    exclude_pattern = args.exclude_group_pattern
    if args.skip_vod:
        exclude_pattern = (
            r"MOVIES|NETFLIX|SERIES|CINEMA|VIDEOTEKA|VOD|RAMADAN|PLUTO|DISNEY|APPLE|AMAZON|HBO|HULU|SKY STORE|MARVEL"
        )

    print("Učitavam kanale s M3U...")
    if exclude_pattern:
        raw = parse_m3u_channels_with_groups(str(m3u_path))
        comp = re.compile(exclude_pattern, re.IGNORECASE)
        channels = [(cid, name) for cid, name, grp in raw if not comp.search(grp)]
        excluded = len(raw) - len(channels)
        print(f"  Isključeno (group odgovara '{exclude_pattern}'): {excluded}")
    else:
        channels = parse_m3u_channels(str(m3u_path))
    print(f"  Kanala za EPG: {len(channels)}")

    focus_region: Optional[str] = None
    if args.focus_exyu:
        epg_list = get_epg_urls_exyu()
        focus_region = "exyu"
        print("Način: EXYU (samo AL,BA,HR,ME,MK,RS,SI) + name aliasi za ex-Yu.")
    elif args.focus_uk:
        epg_list = get_epg_urls_uk()
        focus_region = "uk"
        print("Način: UK (GB) + name aliasi za britanske kanale.")
    elif args.focus_usa:
        epg_list = get_epg_urls_usa()
        focus_region = "usa"
        print("Način: USA (US) + name aliasi za američke kanale.")
    elif args.focus_de:
        epg_list = get_epg_urls_de()
        focus_region = "de"
        print("Način: DE (Njemačka) + name aliasi za njemačke kanale.")
    elif args.only_countries:
        want = {c.strip().upper() for c in args.only_countries.split(",") if c.strip()}
        all_list = get_epg_urls_fallback()
        epg_list = [(cc, url) for cc, url in all_list if cc in want]
        if not epg_list:
            print(f"Nema EPG izvora za zemlje: {want}", file=sys.stderr)
            sys.exit(1)
        print(f"Samo zemlje: {', '.join(sorted(want))}")
    elif args.use_playwright:
        epg_list = get_epg_urls_with_playwright(limit_countries=args.limit_countries)
        if not epg_list:
            print("  Playwright nije vratio linkove, koristim fiksnu listu.", file=sys.stderr)
            epg_list = get_epg_urls_fallback()
            if args.limit_countries:
                epg_list = epg_list[: args.limit_countries]
    else:
        epg_list = get_epg_urls_fallback()
        if args.limit_countries:
            epg_list = epg_list[: args.limit_countries]
    print(f"EPG izvora (zemalja): {len(epg_list)}")

    epg_source_ids: Dict[str, Set[str]] = {}
    epg_channels_with_names: Dict[str, List[Tuple[str, str]]] = {}
    for country, epg_url in epg_list:
        ids = fetch_channel_ids_from_epg(epg_url)
        epg_source_ids[epg_url] = ids
        id_names = fetch_channel_ids_and_names_from_epg(epg_url)
        epg_channels_with_names[epg_url] = id_names

    channel_id_to_epg: Dict[str, str] = {}
    for epg_url, ids in epg_source_ids.items():
        for cid in ids:
            if cid.lower() not in channel_id_to_epg:
                channel_id_to_epg[cid.lower()] = epg_url
    our_ids_with_id_match = {c.lower() for c, _ in channels if channel_id_to_epg.get(c.lower())}
    print(f"Kanala s točnim ID matchom (tvg-id u EPG izvoru): {len(our_ids_with_id_match)}")
    if len(channels) > 500 and len(our_ids_with_id_match) < 200:
        print("  (Malo ID matchova – ako M3U nema tvg-id, koristi se stream ID; za veću pokrivenost trebaju tvg-id u playlisti ili name matching.)")

    out_path = Path(args.output)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<tv generator-info-name="epg-iptv-merged">\n')
        for cid, name in channels:
            f.write(f'  <channel id="{escape_xml(cid)}">\n')
            f.write(f'    <display-name>{escape_xml(name)}</display-name>\n')
            f.write("  </channel>\n")

        total_prog = 0
        channels_linked: Set[str] = set()

        exact_sources = get_tvprofil_exact_sources()
        exact_matched = [c for c, _ in channels if c.lower() in exact_sources]
        if exact_matched:
            print(f"Točni EPG (tvprofil.net): {len(exact_matched)} kanala ...")
        for our_id, _ in channels:
            if our_id.lower() not in exact_sources:
                continue
            url = exact_sources[our_id.lower()]
            content = fetch_epg_content(url, max_bytes=2 * 1024 * 1024)
            if not content:
                continue
            canonical = TVPROFIL_ALIASES.get(our_id.lower(), our_id.lower())
            source_to_our = {canonical.lower(): our_id}
            n, ids_written = extract_programmes_from_xml(
                content, source_to_our, f, max_days_ahead=args.max_days
            )
            total_prog += n
            channels_linked.update(ids_written)
        if exact_matched:
            print(f"  -> {len(channels_linked)} kanala s točnim EPG-om")

        for country, epg_url in epg_list:
            source_ids = epg_source_ids.get(epg_url) or set()
            our_ids_for_this_epg = [c for c, _ in channels if channel_id_to_epg.get(c.lower()) == epg_url]
            source_channels_with_names = epg_channels_with_names.get(epg_url) or []
            source_to_our = build_source_to_our_id(
                source_ids,
                our_ids_for_this_epg,
                source_channels_with_names,
                channels,
                exclude_our_ids=channels_linked,
                use_name_aliases_region=focus_region,
            )
            if not source_to_our:
                continue
            print(f"  Preuzimam programe: {country} ({len(source_to_our)} kanala) ...")
            content = fetch_epg_content(epg_url)
            if not content:
                continue
            n, ids_written = extract_programmes_from_xml(
                content, source_to_our, f, max_days_ahead=args.max_days
            )
            total_prog += n
            channels_linked.update(ids_written)
            print(f"    -> {n} programa")

        f.write("</tv>\n")

    total_channels = len(channels)
    pct = (100.0 * len(channels_linked) / total_channels) if total_channels else 0
    print(f"Zapisano: {out_path}")
    print(f"Ukupno programa upisano: {total_prog}")
    print(f"Kanala s EPG programom: {len(channels_linked)} / {total_channels} ({pct:.1f}%)")
    if total_channels > 0 and pct < 10:
        print("  Za više kanala s programom: playlist treba imati tvg-id (npr. rtl.hr, bbc.uk) ili EPG server s istim ID-ovima; inače se spaja samo po imenu kanala.")
    print("U TiviMateu dodaj ovaj file kao EPG URL (npr. raw GitHub link).")


if __name__ == "__main__":
    main()
