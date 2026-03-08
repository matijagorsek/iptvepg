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
