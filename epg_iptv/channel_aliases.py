#!/usr/bin/env python3
"""
Aliasi channel_id po zemljama: provider često koristi drugi sufiks nego EPG (npr. .uk umjesto .gb).
Koristi se pri usporedbi našeg tvg-id s EPG channel id-ovima (iptv-epg.org, tvprofil).
"""

from typing import Dict, List, Tuple

# (sufiks u playlisti, sufiks u EPG-u) – kad naš id završava s provider_suffix, smatramo ga jednakim EPG id-u s epg_suffix
# Samo stvarne zamjene (provider != EPG). EPG (iptv-epg.org) koristi ISO 3166-1 alpha-2.
SUFFIX_ALIASES: List[Tuple[str, str]] = [
    # UK – provideri često .uk, EPG ima .gb
    (".uk", ".gb"),
    (".eng", ".gb"),
    (".scot", ".gb"),
    (".wal", ".gb"),
    (".wales", ".gb"),
    (".ni", ".gb"),   # Northern Ireland
    # Srbija – tvprofil koristi .sr, provideri .rs; iptv-epg ima rs (ista dva slova)
    (".rs", ".sr"),
    # Turska
    (".tur", ".tr"),
    (".turkey", ".tr"),
    # Grčka (Hellas)
    (".ell", ".gr"),
    # Njemačka (bivša DDR)
    (".dd", ".de"),
    # Rusija (bivši SSSR)
    (".su", ".ru"),
    # Australija
    (".aus", ".au"),
]

# provider_suffix -> epg_suffix za brzi lookup
_SUFFIX_MAP: Dict[str, str] = {_prov: _epg for _prov, _epg in SUFFIX_ALIASES}


def canonical_id_for_lookup(channel_id: str) -> str:
    """Vraća channel_id u obliku koji odgovara EPG-u (npr. .uk -> .gb). Ako nema pravila, vraća lower()."""
    if not channel_id:
        return ""
    lower = channel_id.strip().lower()
    for prov_suf, epg_suf in _SUFFIX_MAP.items():
        if lower.endswith(prov_suf):
            return lower[: -len(prov_suf)] + epg_suf
    return lower


def all_lookup_variants(channel_id: str) -> List[str]:
    """Svi id-ovi pod kojima treba tražiti ovaj kanal pri matchanju (naš id + canonical za EPG).
    Koristi se za izgradnju our_lower: za svaki variant, our_lower[variant] = our_id."""
    if not channel_id:
        return []
    lower = channel_id.strip().lower()
    out = [lower]
    canon = canonical_id_for_lookup(channel_id)
    if canon != lower:
        out.append(canon)
    return out


# EXYU: normalizirano ime u playlisti -> dodatni EPG normalizirani nazivi koji se smiju spariti
# (npr. "bht hd" u playlisti ↔ "BHT 1" u EPG-u)
EXYU_NAME_MATCH_VARIANTS: Dict[str, List[str]] = {
    "bht hd": ["bht 1", "bht"],
    "bht": ["bht 1"],
    "pink hd": ["pink"],
    "pink": [],
    "rts 1": ["rts1"],
    "rts 2": ["rts2"],
    "rts 3": ["rts3"],
    "rts 1 fhd": ["rts1"],
    "rts 2 fhd": ["rts2"],
    "rts 3 fhd": ["rts3"],
    "rts svet": ["rts svet"],
    "prva": ["prva srpska tv", "prva"],
    "prva fhd": ["prva srpska tv", "prva"],
    "prva plus": ["prva plus"],
    "prva kick": ["prva kick"],
    "b92": [],
    "nova bh": ["nova bh"],
    "nova bh hd": ["nova bh"],
    "ftv": [],
    "hayat": ["hayat tv", "hayat"],
    "hayat hd": ["hayat tv", "hayat"],
    "hayat bih": ["hayat tv", "hayat"],
    "obn": [],
    "htv1": ["htv 1", "hrt 1"],
    "htv2": ["htv 2", "hrt 2"],
    "htv3": ["htv 3", "hrt 3"],
    "htv4": ["htv 4", "hrt 4"],
    "hrt 1": ["htv 1", "htv1"],
    "hrt 2": ["htv 2", "htv2"],
    "hrt 3": ["htv 3", "htv3"],
    "hrt 4": ["htv 4", "htv4"],
    "rtl": [],
    "rtl hd": ["rtl"],
    "nova": ["nova tv", "nova"],
    "nova hd": ["nova"],
    "slo1": ["slo 1", "tv slo 1"],
    "slo2": ["slo 2", "tv slo 2"],
    "slo3": ["slo 3", "tv slo 3"],
    "slo 1": ["slo1", "tv slo 1"],
    "slo 2": ["slo2", "tv slo 2"],
    "slo 3": ["slo3", "tv slo 3"],
    "n1 srbija": ["n1", "n1 rs"],
    "n1 bosna": ["n1", "n1 ba"],
    "rtrs": [],
    "rtrs plus": ["rtrs plus"],
    "federalna tv": ["federalna", "ftv"],
    "face tv": ["face tv", "facetv"],
    "al jazeera balkan": ["al jazeera balkans", "al jazeera"],
    "k1 tv": ["kcn1", "k1"],
    "happy tv": ["happytv", "happy tv"],
    "nova s": ["nova s", "novas"],
    "nova m": ["nova m"],
}


# UK (GB): playlist ime -> EPG nazivi za spajanje
UK_NAME_MATCH_VARIANTS: Dict[str, List[str]] = {
    "bbc one": [],
    "bbc one hd": ["bbc one"],
    "bbc two": [],
    "bbc two hd": ["bbc two"],
    "bbc three": [],
    "bbc four": [],
    "bbc news": [],
    "bbc news hd": ["bbc news"],
    "bbc scotland": [],
    "bbc parliament": [],
    "cbbc": [],
    "cbeebies": [],
    "itv": [],
    "itv hd": ["itv"],
    "itv1": ["itv"],
    "itv2": [],
    "itv3": [],
    "itv4": [],
    "channel 4": [],
    "channel 4 hd": ["channel 4"],
    "channel 5": [],
    "channel 5 hd": ["channel 5"],
    "sky news": [],
    "sky sports main event": ["sky sports", "sky sports main event"],
    "sky sports premier league": ["sky sports"],
    "sky sports football": ["sky sports"],
    "sky atlantic": [],
    "sky arts": [],
    "e4": [],
    "e4 hd": ["e4"],
    "film4": [],
    "film 4": ["film4"],
    "comedy central": [],
    "comedy central uk": ["comedy central"],
    "discovery": [],
    "discovery hd": ["discovery"],
    "national geographic": [],
    "national geographic uk": ["national geographic"],
    "dave": [],
    "w": [],
    "drama": [],
    "quest": [],
    "stv": [],
    "stv hd": ["stv"],
    "s4c": [],
}

# USA (US): playlist ime -> EPG nazivi za spajanje
USA_NAME_MATCH_VARIANTS: Dict[str, List[str]] = {
    "cnn": [],
    "cnn hd": ["cnn"],
    "cnn international": ["cnn"],
    "fox news": [],
    "fox news hd": ["fox news"],
    "msnbc": [],
    "msnbc hd": ["msnbc"],
    "abc": [],
    "abc news": ["abc"],
    "nbc": [],
    "nbc hd": ["nbc"],
    "cbs": [],
    "cbs hd": ["cbs"],
    "fox": [],
    "fox hd": ["fox"],
    "fox business": [],
    "hbo": [],
    "hbo hd": ["hbo"],
    "amc": [],
    "amc hd": ["amc"],
    "discovery channel": ["discovery"],
    "discovery hd": ["discovery"],
    "national geographic": [],
    "national geographic us": ["national geographic"],
    "espn": [],
    "espn hd": ["espn"],
    "espn 2": [],
    "espn2": ["espn 2"],
    "tnt": [],
    "tnt hd": ["tnt"],
    "usa network": ["usa"],
    "usa": [],
    "syfy": [],
    "bravo": [],
    "comedy central": [],
    "comedy central us": ["comedy central"],
    "fx": [],
    "fx hd": ["fx"],
    "history": [],
    "a&e": ["ae"],
    "food network": [],
    "hgtv": [],
    "tlc": [],
    "animal planet": [],
    "cartoon network": [],
    "nickelodeon": [],
    "nick": ["nickelodeon"],
    "mtv": [],
    "paramount network": ["paramount"],
    "c span": ["cspan"],
    "pbs": [],
    "pbs kids": ["pbs"],
    "the cw": ["cw"],
    "ion": [],
    "reelz": [],
}

# DE (Njemačka): playlist ime -> EPG nazivi za spajanje
DE_NAME_MATCH_VARIANTS: Dict[str, List[str]] = {
    "das erste": ["ard", "das erste"],
    "ard": ["das erste"],
    "ard hd": ["das erste", "ard"],
    "zdf": [],
    "zdf hd": ["zdf"],
    "rtl": [],
    "rtl hd": ["rtl"],
    "rtl ii": ["rtl 2"],
    "rtl 2": ["rtl ii"],
    "sat 1": ["sat1"],
    "sat1": ["sat 1"],
    "sat 1 hd": ["sat1"],
    "pro 7": ["prosieben", "pro 7"],
    "prosieben": ["pro 7"],
    "pro7": ["pro 7", "prosieben"],
    "pro 7 maxx": ["prosieben maxx"],
    "vox": [],
    "vox hd": ["vox"],
    "kabel 1": ["kabel eins"],
    "kabel eins": ["kabel 1"],
    "kabel 1 hd": ["kabel 1"],
    "rtl plus": ["rtl plus"],
    "ntv": [],
    "welt": [],
    "welt hd": ["welt"],
    "arte": [],
    "arte hd": ["arte"],
    "3sat": [],
    "phoenix": [],
    "one": ["one"],
    "tagesschau": [],
    "sport1": ["sport 1"],
    "sport 1": ["sport1"],
    "dmax": [],
    "sixx": [],
    "comedy central": [],
    "comedy central de": ["comedy central"],
    "discovery": [],
    "national geographic": [],
    "eurosport": [],
    "eurosport 1": ["eurosport"],
    "eurosport 2": ["eurosport 2"],
    "sky sport": ["sky sport"],
    "sky sport hd": ["sky sport"],
    "crime thriller": [],
    "anixe": [],
    "tele 5": ["tele5"],
    "bild": [],
}


def _name_match_variants_from_dict(normalized_name: str, variants_dict: Dict[str, List[str]]) -> List[str]:
    out = [normalized_name]
    if normalized_name in variants_dict:
        for v in variants_dict[normalized_name]:
            if v and v not in out:
                out.append(v)
    return out


def exyu_name_match_variants(normalized_display_name: str) -> List[str]:
    """Za EXYU: vraća [norm_our] + dodatne EPG nazive s kojima se smije spariti ovaj kanal (po imenu)."""
    if not normalized_display_name:
        return []
    n = normalized_display_name.strip().lower()
    return _name_match_variants_from_dict(n, EXYU_NAME_MATCH_VARIANTS)


def name_match_variants_for_region(normalized_display_name: str, region: str) -> List[str]:
    """Vraća [norm_our] + EPG nazive za spajanje za danu regiju (exyu, uk, usa, de)."""
    if not normalized_display_name or not region:
        return [normalized_display_name] if normalized_display_name else []
    n = normalized_display_name.strip().lower()
    region = region.lower()
    if region == "exyu":
        return _name_match_variants_from_dict(n, EXYU_NAME_MATCH_VARIANTS)
    if region == "uk":
        return _name_match_variants_from_dict(n, UK_NAME_MATCH_VARIANTS)
    if region == "usa":
        return _name_match_variants_from_dict(n, USA_NAME_MATCH_VARIANTS)
    if region == "de":
        return _name_match_variants_from_dict(n, DE_NAME_MATCH_VARIANTS)
    return [n]
