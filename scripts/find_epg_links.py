#!/usr/bin/env python3
"""Launcher za epg_iptv.find_epg_links. Pokreni iz roota: python3 scripts/find_epg_links.py ..."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from epg_iptv.find_epg_links import main

if __name__ == "__main__":
    main()
