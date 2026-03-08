# EPG za TiviMate (IPTV)

Tri načina korištenja:

---

## 1. GitHub (bez vlastitog servera)

Workflow na GitHubu povlači playlistu s providera i generira `playlist_with_epg.m3u` i `epg.xml`. TiviMate povlači oba s **raw GitHub URL-a** – ne treba ti nikakav server.

### Postavljanje

1. **Fork ili novi repo**  
   Stvori repozitorij s ovim kodom (npr. `epg-iptv`).

2. **Secrets**  
   U repo: **Settings → Secrets and variables → Actions** → New repository secret. Dodaj:
   - `IPTV_BASE_URL` (npr. `http://line.ottcst.com:80`)
   - `IPTV_USERNAME`
   - `IPTV_PASSWORD`  
   (isti podaci kao za prijavu kod providera.)

3. **Prvo generiranje**  
   **Actions** → **Generate EPG and Playlist** → **Run workflow**. Nakon uspjeha u repou će biti mapa `output/` s `playlist_with_epg.m3u` i `epg.xml`.

4. **U TiviMateu**  
   Za ovaj repo (matijagorsek/iptvepg), nakon što workflow generira datoteke:
   - **Playlist URL**:  
     `https://raw.githubusercontent.com/matijagorsek/iptvepg/main/output/playlist_with_epg.m3u`
   - **EPG URL**:  
     `https://raw.githubusercontent.com/matijagorsek/iptvepg/main/output/epg.xml`  
   (Ako koristiš drugu granu, zamijeni `main`.)

Workflow se automatski pokreće **svakih 12 sati**; možeš ga i ručno pokrenuti u **Actions** → **Run workflow**. Nema uploadanja – sve se odrađuje na GitHubu.

### Važno – privatni repo

Generirana playlista sadrži **stream URL-ove** (često i credentials). **Koristi privatni repozitorij** da ti netko ne vidi te linkove.  
Za privatni repo: raw URL u TiviMateu možda zahtijeva prijavu; neki playeri ne podržavaju auth za URL. Ako TiviMate ne može učitati privatni raw link, opcije su: lokalni server (odjeljak 2) ili jednokratna skripta (odjeljak 4).

Ako provider **blokira zahtjeve s GitHubovih IP-ova**, workflow će padati na “Dohvaćam playlistu…”. Tada koristi lokalni server ili skriptu.

---

## 2. Server u aplikaciji (bez uploadanja)

Mali server drži tvoje **podatke za prijavu** (URL providera, username, password). Na zahtjev dohvaća playlistu s providera, **dodaje EPG linkove** (tvg-id) i servira ih. U TiviMateu **jednom** postaviš dva linka i više ne moraš ništa updateati – sve se odrađuje u pozadini.

### Postavljanje

1. **Kopiraj konfiguraciju**
   ```bash
   cp .env.example .env
   ```
   Uredi `.env`: stavi `IPTV_BASE_URL`, `IPTV_USERNAME`, `IPTV_PASSWORD` (isti podaci kao za prijavu u TiviMate).

2. **Instaliraj ovisnosti i pokreni server**
   ```bash
   pip install -r requirements.txt
   python3 iptv_epg_server.py
   ```
   Server sluša na `http://0.0.0.0:8765` (ili `PORT`/`HOST` iz `.env`).

3. **U TiviMateu**
   - **Playlist**: dodaj po URL-u (ne “Xtream Codes login”), npr.  
     `http://<tvoj-ip>:8765/playlist.m3u`  
     (ako server radi na računalu u mreži, `<tvoj-ip>` je npr. 192.168.1.10)
   - **EPG**: za tu playlistu dodaj EPG izvor:  
     `http://<tvoj-ip>:8765/epg.xml`

Kad TiviMate osvježi playlistu ili EPG, server na zahtjev dohvaća novu listu s providera i vraća je s tvg-id. **Ne trebaš više ručno uploadati liste.**

### Gdje pokretati server

- Na računalu koje je uvijek u istoj mreži kao TV/telefon (npr. NAS, Raspberry Pi, stalno uključen PC). U TiviMateu onda staviš `http://192.168.x.x:8765/...`.
- Ili na VPS/u oblaku i staviš u TiviMateu `https://tvoja-domena.com/playlist.m3u` i `.../epg.xml` (trebaš HTTPS i eventualno reverse proxy).

---

## 3. Jednokratna skripta (M3U → epg.xml + playlist)

Ako ne želiš server, možeš iz **lokalne M3U datoteke** generirati `epg.xml` i `playlist_with_epg.m3u`, pa ih ručno učitati ili hostati negdje.

```bash
python3 m3u_to_epg.py /path/do/playliste.m3u [izlazni_folder]
```

- **Playlist u TiviMateu**: učitaj `playlist_with_epg.m3u` (file ili URL).
- **EPG u TiviMateu**: izvor = `epg.xml` (file ili URL).

Kad provider promijeni listu, moraš ponovno pokrenuti skriptu i ponovo učitati/hostati datoteke.

---

## Napomene

- **Programski sadržaj**: ovaj EPG samo “registrira” kanale (tvg-id); nema stvarnih programa (vremena, naslovi). Ako nađeš EPG izvor koji koristi iste ID-ove, možeš ga dodati.
- **Cache**: server (odjeljak 2) kešira odgovor providera 5 minuta; nakon toga dohvaća novu listu.
