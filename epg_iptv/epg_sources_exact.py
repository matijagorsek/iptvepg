#!/usr/bin/env python3
"""
Točni EPG izvori: jedan URL po kanalu (1:1), bez krivog linkanja.
Izvor: http://tvprofil.net/xmltv/?channels= – besplatni weekly XML po kanalu.
"""

from typing import Dict

# channel_id (lower) -> weekly XML URL
# Ako tvoj M3U ima tvg-id ili stream_id koji se poklapa (case-insensitive), koristi se ovaj URL.
TVPROFIL_EXACT: Dict[str, str] = {
    "htv1.hr": "https://tvprofil.net/xmltv/data/htv1.hr/weekly_htv1.hr_tvprofil.net.xml",
    "htv2.hr": "https://tvprofil.net/xmltv/data/htv2.hr/weekly_htv2.hr_tvprofil.net.xml",
    "htv3.hr": "https://tvprofil.net/xmltv/data/htv3.hr/weekly_htv3.hr_tvprofil.net.xml",
    "htv4.hr": "https://tvprofil.net/xmltv/data/htv4.hr/weekly_htv4.hr_tvprofil.net.xml",
    "rtl.hr": "https://tvprofil.net/xmltv/data/rtl.hr/weekly_rtl.hr_tvprofil.net.xml",
    "rtl2.hr": "https://tvprofil.net/xmltv/data/rtl2.hr/weekly_rtl2.hr_tvprofil.net.xml",
    "nova.hr": "https://tvprofil.net/xmltv/data/nova.hr/weekly_nova.hr_tvprofil.net.xml",
    "vinkovacka-tv.hr": "https://tvprofil.net/xmltv/data/vinkovacka-tv.hr/weekly_vinkovacka-tv.hr_tvprofil.net.xml",
    "tv-zapad.hr": "https://tvprofil.net/xmltv/data/tv-zapad.hr/weekly_tv-zapad.hr_tvprofil.net.xml",
    "plava-televizija.hr": "https://tvprofil.net/xmltv/data/plava-televizija.hr/weekly_plava-televizija.hr_tvprofil.net.xml",
    "slo1.si": "https://tvprofil.net/xmltv/data/slo1.si/weekly_slo1.si_tvprofil.net.xml",
    "slo2.si": "https://tvprofil.net/xmltv/data/slo2.si/weekly_slo2.si_tvprofil.net.xml",
    "slo3.si": "https://tvprofil.net/xmltv/data/slo3.si/weekly_slo3.si_tvprofil.net.xml",
    "ftv.ba": "https://tvprofil.net/xmltv/data/ftv.ba/weekly_ftv.ba_tvprofil.net.xml",
    "bht1.ba": "https://tvprofil.net/xmltv/data/bht1.ba/weekly_bht1.ba_tvprofil.net.xml",
    "nova-bh.ba": "https://tvprofil.net/xmltv/data/nova-bh.ba/weekly_nova-bh.ba_tvprofil.net.xml",
    "hayat-tv.ba": "https://tvprofil.net/xmltv/data/hayat-tv.ba/weekly_hayat-tv.ba_tvprofil.net.xml",
    "obn.ba": "https://tvprofil.net/xmltv/data/obn.ba/weekly_obn.ba_tvprofil.net.xml",
    "cmc.music": "https://tvprofil.net/xmltv/data/cmc.music/weekly_cmc.music_tvprofil.net.xml",
    "pink.sr": "https://tvprofil.net/xmltv/data/pink.sr/weekly_pink.sr_tvprofil.net.xml",
    "rts1.sr": "https://tvprofil.net/xmltv/data/rts1.sr/weekly_rts1.sr_tvprofil.net.xml",
    "rts2.sr": "https://tvprofil.net/xmltv/data/rts2.sr/weekly_rts2.sr_tvprofil.net.xml",
    "b92.sr": "https://tvprofil.net/xmltv/data/b92.sr/weekly_b92.sr_tvprofil.net.xml",
    "rtrs.sr": "https://tvprofil.net/xmltv/data/rtrs.sr/weekly_rtrs.sr_tvprofil.net.xml",
    "prva-srpska-tv.sr": "https://tvprofil.net/xmltv/data/prva-srpska-tv.sr/weekly_prva-srpska-tv.sr_tvprofil.net.xml",
    "nova-s.sr": "https://tvprofil.net/xmltv/data/nova-s.sr/weekly_nova-s.sr_tvprofil.net.xml",
    "arena-sport-1-ba.sport": "https://tvprofil.net/xmltv/data/arena-sport-1-ba.sport/weekly_arena-sport-1-ba.sport_tvprofil.net.xml",
    "sportklub-hr.sport": "https://tvprofil.net/xmltv/data/sportklub-hr.sport/weekly_sportklub-hr.sport_tvprofil.net.xml",
    "eurosport.sport": "https://tvprofil.net/xmltv/data/eurosport.sport/weekly_eurosport.sport_tvprofil.net.xml",
    "tv-arena-sport-1.sport": "https://tvprofil.net/xmltv/data/tv-arena-sport-1.sport/weekly_tv-arena-sport-1.sport_tvprofil.net.xml",
    "tv-arena-sport-2.sport": "https://tvprofil.net/xmltv/data/tv-arena-sport-2.sport/weekly_tv-arena-sport-2.sport_tvprofil.net.xml",
    "tv-arena-sport-3.sport": "https://tvprofil.net/xmltv/data/tv-arena-sport-3.sport/weekly_tv-arena-sport-3.sport_tvprofil.net.xml",
    "tv-arena-sport-1-hr.sport": "https://tvprofil.net/xmltv/data/tv-arena-sport-1-hr.sport/weekly_tv-arena-sport-1-hr.sport_tvprofil.net.xml",
    "nova-m.cg": "https://tvprofil.net/xmltv/data/nova-m.cg/weekly_nova-m.cg_tvprofil.net.xml",
    "rtl-de.de": "https://tvprofil.net/xmltv/data/rtl-de.de/weekly_rtl-de.de_tvprofil.net.xml",
    "kabel-1.de": "https://tvprofil.net/xmltv/data/kabel-1.de/weekly_kabel-1.de_tvprofil.net.xml",
    "pro-7.de": "https://tvprofil.net/xmltv/data/pro-7.de/weekly_pro-7.de_tvprofil.net.xml",
    "sat-1.de": "https://tvprofil.net/xmltv/data/sat-1.de/weekly_sat-1.de_tvprofil.net.xml",
    "zdf.de": "https://tvprofil.net/xmltv/data/zdf.de/weekly_zdf.de_tvprofil.net.xml",
    "rai-1.it": "https://tvprofil.net/xmltv/data/rai-1.it/weekly_rai-1.it_tvprofil.net.xml",
    "cartoon-network.toons": "https://tvprofil.net/xmltv/data/cartoon-network.toons/weekly_cartoon-network.toons_tvprofil.net.xml",
    "kika.toons": "https://tvprofil.net/xmltv/data/kika.toons/weekly_kika.toons_tvprofil.net.xml",
    "disney-channel.toons": "https://tvprofil.net/xmltv/data/disney-channel.toons/weekly_disney-channel.toons_tvprofil.net.xml",
    "hbo.movie": "https://tvprofil.net/xmltv/data/hbo.movie/weekly_hbo.movie_tvprofil.net.xml",
    "cinestar-tv.movie": "https://tvprofil.net/xmltv/data/cinestar-tv.movie/weekly_cinestar-tv.movie_tvprofil.net.xml",
    "scifi.movie": "https://tvprofil.net/xmltv/data/scifi.movie/weekly_scifi.movie_tvprofil.net.xml",
    "doma-tv.movie": "https://tvprofil.net/xmltv/data/doma-tv.movie/weekly_doma-tv.movie_tvprofil.net.xml",
}


# Aliasi: provider često šalje .rs (Srbija), hrt vs htv, ili drugačiji id – mapiraj na naš id koji ima URL
# key (lower) -> canonical key u TVPROFIL_EXACT (da dobijemo isti URL)
TVPROFIL_ALIASES: Dict[str, str] = {
    "rts1.rs": "rts1.sr",
    "rts2.rs": "rts2.sr",
    "b92.rs": "b92.sr",
    "prva.rs": "prva-srpska-tv.sr",
    "novas.sr": "nova-s.sr",  # nova s (već imamo .sr)
    "hayat.ba": "hayat-tv.ba",
    "novatv.hr": "nova.hr",
    "rtrs.ba": "rtrs.sr",  # RTRS ima program u rs EPG
    "hrt1.hr": "htv1.hr",
    "hrt2.hr": "htv2.hr",
    "hrt3.hr": "htv3.hr",
    "hrt4.hr": "htv4.hr",
}


def get_tvprofil_exact_sources() -> Dict[str, str]:
    """Vraća rječnik channel_id (lower) -> EPG URL. Uključuje i aliase (npr. rts1.rs -> URL za rts1.sr)."""
    out = dict(TVPROFIL_EXACT)
    for alias_key, canonical_key in TVPROFIL_ALIASES.items():
        if canonical_key in TVPROFIL_EXACT and alias_key not in out:
            out[alias_key] = TVPROFIL_EXACT[canonical_key]
    return out
