#!/usr/bin/env python3
"""
S Playwrightom dohvaća listu EPG linkova s iptv-epg.org (po zemljama), iz svakog
EPG XML-a izvlači channel id-ove, pa uspoređuje s kanalima s tvoje M3U liste.
Izlaz: CSV/JSON s kanalima koji imaju EPG link (channel_id, name, epg_url).

Korištenje:
  pip install playwright && playwright install chromium
  python3 find_epg_links.py /path/do/playliste.m3u [--output channels_with_epg.csv] [--limit-countries 20]
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.request import urlopen, Request

# M3U parsing - same logic as iptv_epg_server
def extract_stream_id_from_url(url: str):
    url = (url or "").strip()
    if not url or url.startswith("#"):
        return None
    parts = url.rstrip("/").split("/")
    if parts and parts[-1].strip():
        last = parts[-1].split(".")[0]
        if last.isdigit():
            return last
    return None

def parse_extinf(line: str) -> dict:
    m = re.search(r'tvg-name="([^"]*)"', line)
    tvg_name = (m.group(1).strip() if m else "")
    m_id = re.search(r'tvg-id="([^"]*)"', line)
    tvg_id = (m_id.group(1).strip() if m_id else "")
    m_grp = re.search(r'group-title="([^"]*)"', line)
    group_title = (m_grp.group(1).strip() if m_grp else "")
    if "," in line:
        title = line.split(",", 1)[-1].strip()
        if not tvg_name:
            tvg_name = title
    return {"tvg_name": tvg_name or "Unknown", "tvg_id": tvg_id, "group_title": group_title}


def parse_m3u_channels(m3u_path: str) -> List[Tuple[str, str]]:
    """Vraća listu (channel_id, display_name) za live kanale (s stream_id u URL-u)."""
    return [(cid, name) for cid, name, _ in parse_m3u_channels_with_groups(m3u_path)]


def parse_m3u_channels_with_groups(m3u_path: str) -> List[Tuple[str, str, str]]:
    """Vraća listu (channel_id, display_name, group_title) za live kanale (s stream_id u URL-u)."""
    path = Path(m3u_path)
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    channels = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#EXTINF"):
            info = parse_extinf(line)
            url = ""
            if i + 1 < len(lines) and not lines[i + 1].startswith("#"):
                url = lines[i + 1].strip()
                i += 1
            stream_id = extract_stream_id_from_url(url) if url else None
            if stream_id:
                channel_id = info["tvg_id"].strip() if info.get("tvg_id") else stream_id
                channels.append((channel_id, info["tvg_name"], info.get("group_title", "")))
            i += 1
            continue
        i += 1
    return channels


def get_epg_urls_with_playwright(limit_countries: Optional[int] = None) -> List[Tuple[str, str]]:
    """Dohvaća (country_code, epg_url) s iptv-epg.org/guides. Koristi Playwright. Ako nije instaliran, vraća []."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return []

    out = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://iptv-epg.org/guides", wait_until="networkidle", timeout=30000)
        # Linkovi su u tablici: https://iptv-epg.org/files/epg-XX.xml
        links = page.query_selector_all('a[href*="epg-"].xml')
        seen = set()
        for a in links:
            href = a.get_attribute("href")
            if not href or href in seen:
                continue
            seen.add(href)
            if not href.startswith("http"):
                href = "https://iptv-epg.org" + href if href.startswith("/") else "https://iptv-epg.org/" + href
            m = re.search(r"epg-([a-z]{2})\.xml", href)
            if m:
                out.append((m.group(1).upper(), href))
                if limit_countries and len(out) >= limit_countries:
                    break
        browser.close()
    return out


# EXYU/Balkan: zemlje s iptv-epg.org za maksimalnu pokrivenost ex-Yu kanala (HR, BA, RS, SI, ME, MK, AL)
EXYU_COUNTRY_CODES = {"AL", "BA", "HR", "ME", "MK", "RS", "SI"}


def get_epg_urls_fallback() -> List[Tuple[str, str]]:
    """Bez Playwrighta: fiksna lista EPG URL-ova s iptv-epg.org (po zemljama)."""
    countries = [
        "al", "ar", "am", "au", "at", "by", "be", "bo", "ba", "br", "bg", "ca", "cl", "co", "cr",
        "cz", "dk", "do", "ec", "eg", "sv", "fi", "fr", "ge", "de", "gh", "gr", "gt", "hn", "hk", "hr",
        "hu", "is", "in", "id", "il", "it", "jp", "lv", "lb", "lt", "lu", "mk", "my", "mt", "mx", "me",
        "nl", "nz", "ni", "ng", "no", "pa", "py", "pe", "ph", "pl", "pt", "ro", "ru", "sa", "rs", "sg",
        "si", "za", "kr", "es", "se", "ch", "tw", "th", "tr", "ug", "ua", "ae", "gb", "us", "uy", "ve", "vn", "zw",
    ]
    return [(c.upper(), f"https://iptv-epg.org/files/epg-{c}.xml") for c in countries]


def get_epg_urls_exyu() -> List[Tuple[str, str]]:
    """Samo EXYU/Balkan zemlje (AL, BA, HR, ME, MK, RS, SI) – za način s maksimalnom pokrivenošću ex-Yu po imenu."""
    all_list = get_epg_urls_fallback()
    return [(cc, url) for cc, url in all_list if cc in EXYU_COUNTRY_CODES]


def get_epg_urls_uk() -> List[Tuple[str, str]]:
    """Samo UK (GB) – za način s maksimalnom pokrivenošću UK kanala po imenu."""
    all_list = get_epg_urls_fallback()
    return [(cc, url) for cc, url in all_list if cc == "GB"]


def get_epg_urls_usa() -> List[Tuple[str, str]]:
    """Samo USA (US) – za način s maksimalnom pokrivenošću US kanala po imenu."""
    all_list = get_epg_urls_fallback()
    return [(cc, url) for cc, url in all_list if cc == "US"]


def get_epg_urls_de() -> List[Tuple[str, str]]:
    """Samo Njemačka (DE) – za način s maksimalnom pokrivenošću DE kanala po imenu."""
    all_list = get_epg_urls_fallback()
    return [(cc, url) for cc, url in all_list if cc == "DE"]


def fetch_channel_ids_from_epg(epg_url: str, max_bytes: int = 2 * 1024 * 1024):
    """Dohvaći do max_bytes EPG XML-a i izvuci sve channel id-ove. Slijedi redirect (meta refresh)."""
    channel_ids = set()
    url = epg_url
    try:
        for _ in range(3):  # max 3 redirects
            req = Request(url, headers={"User-Agent": "TiviMate-EPG-Matcher/1.0"})
            with urlopen(req, timeout=30) as r:
                data = b""
                while len(data) < max_bytes:
                    chunk = r.read(64 * 1024)
                    if not chunk:
                        break
                    data += chunk
                text = data.decode("utf-8", errors="replace")
            if text.strip().startswith("<?xml") or text.strip().startswith("<tv"):
                break
            # Meta refresh redirect
            m = re.search(r'url=["\']([^"\']+)["\']', text)
            if m:
                url = m.group(1).strip()
                continue
            break
    except Exception:
        return channel_ids
    for m in re.finditer(r'<channel\s+id=["\']([^"\']+)["\']', text):
        channel_ids.add(m.group(1))
    return channel_ids


def fetch_channel_ids_and_names_from_epg(
    epg_url: str, max_bytes: int = 2 * 1024 * 1024
) -> List[Tuple[str, str]]:
    """Dohvati channel id + display-name iz EPG XML-a (za name-based matching). Vraća [(id, display_name), ...]."""
    result: List[Tuple[str, str]] = []
    url = epg_url
    try:
        for _ in range(3):
            req = Request(url, headers={"User-Agent": "TiviMate-EPG-Matcher/1.0"})
            with urlopen(req, timeout=30) as r:
                data = b""
                while len(data) < max_bytes:
                    chunk = r.read(64 * 1024)
                    if not chunk:
                        break
                    data += chunk
                text = data.decode("utf-8", errors="replace")
            if text.strip().startswith("<?xml") or text.strip().startswith("<tv"):
                break
            m = re.search(r'url=["\']([^"\']+)["\']', text)
            if m:
                url = m.group(1).strip()
                continue
            break
    except Exception:
        return result
    # Po bloku: <channel id="..."> ... </channel> i unutar njega prvi <display-name>
    for blok in re.finditer(
        r'<channel\s+id=["\']([^"\']+)["\'][^>]*>(.*?)</channel>',
        text,
        re.DOTALL,
    ):
        cid = blok.group(1)
        inner = blok.group(2)
        name_m = re.search(r"<display-name[^>]*>([^<]*)</display-name>", inner)
        name = name_m.group(1).strip() if name_m else ""
        result.append((cid, name))
    return result


def main():
    ap = argparse.ArgumentParser(description="Pronađi EPG linkove za kanale s M3U liste")
    ap.add_argument("m3u", help="Putanja do M3U playliste")
    ap.add_argument("--output", "-o", default="channels_with_epg.csv", help="Izlazna datoteka (CSV ili .json)")
    ap.add_argument("--use-playwright", action="store_true", help="Koristi Playwright za dohvat liste EPG URL-ova (inače fiksna lista)")
    ap.add_argument("--limit-countries", type=int, default=None, help="Max broj zemalja (EPG fajlova) za skeniranje")
    ap.add_argument("--limit-channels", type=int, default=None, help="Max broj kanala s M3U za provjeru (za test)")
    args = ap.parse_args()

    m3u_path = Path(args.m3u)
    if not m3u_path.exists():
        print(f"Datoteka ne postoji: {m3u_path}", file=sys.stderr)
        sys.exit(1)

    print("Učitavam kanale s M3U...")
    channels = parse_m3u_channels(str(m3u_path))
    if args.limit_channels:
        channels = channels[: args.limit_channels]
    print(f"  Ukupno kanala (live): {len(channels)}")

    if args.use_playwright:
        print("Dohvaćam listu EPG URL-ova s iptv-epg.org (Playwright)...")
        epg_list = get_epg_urls_with_playwright(limit_countries=args.limit_countries)
    else:
        print("Koristim fiksnu listu EPG URL-ova (iptv-epg.org po zemljama)...")
        epg_list = get_epg_urls_fallback()
        if args.limit_countries:
            epg_list = epg_list[: args.limit_countries]
    print(f"  EPG izvora (zemalja): {len(epg_list)}")

    # channel_id -> epg_url (prvi koji sadrži taj id)
    channel_id_to_epg: dict[str, str] = {}
    # epg_url -> set of channel ids (cache)
    epg_channel_sets: dict[str, set[str]] = {}

    for i, (country, epg_url) in enumerate(epg_list):
        print(f"  Skeniram {country}: {epg_url[:50]}...")
        ids = fetch_channel_ids_from_epg(epg_url)
        epg_channel_sets[epg_url] = ids
        for cid in ids:
            key = cid.lower()
            if key not in channel_id_to_epg:
                channel_id_to_epg[key] = epg_url

    # Presjek: naši kanali koji imaju EPG (case-insensitive match)
    matches = []
    for channel_id, name in channels:
        epg_url = channel_id_to_epg.get(channel_id.lower())
        if epg_url:
            matches.append((channel_id, name, epg_url))

    print(f"Kanala s pronađenim EPG linkom: {len(matches)}")

    out_path = Path(args.output)
    if out_path.suffix.lower() == ".json":
        data = [{"channel_id": cid, "name": name, "epg_url": url} for cid, name, url in matches]
        out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        with open(out_path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["channel_id", "name", "epg_url"])
            w.writerows(matches)
    print(f"Zapisano: {out_path}")


if __name__ == "__main__":
    main()
