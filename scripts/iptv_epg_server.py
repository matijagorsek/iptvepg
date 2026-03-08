#!/usr/bin/env python3
"""
Pokreće EPG server (Flask) iz epg_iptv paketa.
Korištenje (iz roota projekta): python3 scripts/iptv_epg_server.py
  .env treba biti u rootu projekta.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from epg_iptv.iptv_epg_server import run_server

if __name__ == "__main__":
    run_server()
