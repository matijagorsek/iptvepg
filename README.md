# EPG za TiviMate (IPTV)

Tri načina korištenja.

### Struktura projekta

```
epg-iptv/
├── epg_iptv/              # Zajednički moduli (biblioteka)
│   ├── channel_aliases.py   # Aliasi tvg-id po zemljama (.uk→.gb, .rs→.sr, …)
│   ├── epg_sources_exact.py  # Točni EPG URL-ovi (tvprofil.net, 1 URL = 1 kanal)
│   ├── find_epg_links.py    # Parsiranje M3U, dohvat EPG izvora (iptv-epg.org)
│   └── iptv_epg_server.py   # Logika servera: M3U + EPG XML
├── scripts/                # Izvršne skripte (pokretati iz roota projekta)
│   ├── build_merged_epg.py  # Generira epg_merged.xml (svi kanali + programi)
│   ├── generate_epg_github.py  # Za GitHub Actions: playlist + epg.xml
│   ├── find_epg_links.py   # CLI: koji kanali imaju EPG (CSV/JSON)
│   ├── iptv_epg_server.py  # Pokreće lokalni EPG/playlist server
│   └── m3u_to_epg.py       # Jednokratno: M3U → epg.xml + playlist s tvg-id
├── output/                 # Generirane datoteke (playlist, epg.xml, epg_merged.xml)
├── .env.example
├── requirements.txt
└── README.md
```

Sve skripte pokrećeš **iz roota repozitorija**, npr. `python3 scripts/build_merged_epg.py ...`.

---

## Ako fork-aš ovaj repo (što treba napraviti)

Kad **forkaš** repozitorij da koristiš svoj EPG za svoju playlistu:

1. **Fork**  
   Na GitHubu: **Fork** ovaj repo u svoj račun (npr. `tvojuser/epg-iptv` ili `tvojuser/iptvepg`).

2. **Secrets**  
   U **svom** forkanom repou: **Settings** → **Secrets and variables** → **Actions** → **New repository secret**. Dodaj tri tajne (podatci od tvog IPTV providera):
   - `IPTV_BASE_URL` – npr. `http://provider.com:8080`
   - `IPTV_USERNAME`
   - `IPTV_PASSWORD`

3. **Privatni repo (preporuka)**  
   **Settings** → **General** → **Danger Zone** → **Change repository visibility** → **Private**.  
   Playlista u `output/` sadrži stream linkove; u privatnom repu ih drugi ne vide.

4. **Prvo pokretanje**  
   **Actions** → **Generate EPG and Playlist** → **Run workflow**.  
   Kad workflow uspješno prođe, u repou će biti mapa **output/** s `playlist_with_epg.m3u`, `epg.xml` i `epg_merged.xml`.

5. **URL u TiviMateu**  
   Koristi **svoje** raw linkove (zamijeni `tvojuser` i ime repa/grane):
   - **EPG URL:**  
     `https://raw.githubusercontent.com/tvojuser/ime-repa/main/output/epg_merged.xml`
   - Ako koristiš playlistu s GitHuba (ne Xtream Codes):  
     **Playlist URL:**  
     `https://raw.githubusercontent.com/tvojuser/ime-repa/main/output/playlist_with_epg.m3u`

Workflow se zatim automatski pokreće svakih 12 sati; EPG i playlista ostaju aktualni. Detalji u odjeljku **1. GitHub** ispod.

---

## Koristiš Xtream Codes login?

Ako u TiviMateu dodaješ playlistu **preko Xtream Codes prijave** (URL + username + password), **ne moraš mijenjati način dodavanja**. Samo dodaš **EPG izvor** za tu playlistu:

1. Generiraj EPG (npr. GitHub Actions ispod – isti Secrets kao za prijavu).
2. U TiviMateu: **Playlist** ostaje onako kako jest (Xtream Codes login).  
   Za tu playlistu otvori postavke → **EPG** → dodaj EPG izvor i stavi **samo EPG URL**, npr.:  
   `https://raw.githubusercontent.com/matijagorsek/iptvepg/main/output/epg.xml`

EPG ima channel id = stream ID (broj iz URL-a streama). TiviMate kanale iz Xtream Codesa obično identificira tim istim ID-om, pa se EPG automatski spoji na kanale. **Playlistu ne prebacuješ na URL** – ostaje login, a EPG se ubacuje preko ovog linka.

---

## 1. GitHub (bez vlastitog servera)

Workflow na GitHubu povlači playlistu s providera i generira `playlist_with_epg.m3u` i `epg.xml`. TiviMate povlači oba s **raw GitHub URL-a** – ne treba ti nikakav server.

### Postavljanje

*Ako si **fork-ao** repo, korak po korak imaš u odjeljku **"Ako fork-aš ovaj repo"** na vrhu.*

1. **Fork ili novi repo**  
   Stvori repozitorij s ovim kodom (npr. fork ovog repa ili novi repo s kopijom koda).

2. **Secrets**  
   U repo: **Settings → Secrets and variables → Actions** → New repository secret. Dodaj:
   - `IPTV_BASE_URL` (npr. `http://line.ottcst.com:80`)
   - `IPTV_USERNAME`
   - `IPTV_PASSWORD`  
   (isti podaci kao za prijavu kod providera.)

3. **Prvo generiranje**  
   **Actions** → **Generate EPG and Playlist** → **Run workflow**. Nakon uspjeha u repou će biti mapa `output/` s:
   - `playlist_with_epg.m3u` – playlista s tvg-id
   - `epg.xml` – samo kanali (bez programa)
   - **`epg_merged.xml`** – svi kanali + stvarni programi (TV vodič) gdje ih ima na iptv-epg.org → **ovaj stavi u TiviMate**

4. **U TiviMateu**  
   Nakon što workflow u **tvom** repou generira datoteke, stavi **svoje** raw URL-ove (zamijeni `TVOJ_USER/TVOJ_REPO` i granu ako nije `main`):
   - **Preporučeno – jedan EPG s programima**:  
     **EPG URL**: `https://raw.githubusercontent.com/TVOJ_USER/TVOJ_REPO/main/output/epg_merged.xml`
   - **Ako koristiš Xtream Codes login**: Playlist ostaje preko prijave; za EPG stavi gornji `epg_merged.xml` link.
   - **Ako koristiš playlist po URL-u**:  
     Playlist: `https://raw.githubusercontent.com/TVOJ_USER/TVOJ_REPO/main/output/playlist_with_epg.m3u`  
     EPG: `https://raw.githubusercontent.com/TVOJ_USER/TVOJ_REPO/main/output/epg_merged.xml`  
   (Za samo kanale bez programa možeš koristiti `epg.xml`.)

Workflow se automatski pokreće **svakih 12 sati**; možeš ga i ručno pokrenuti u **Actions** → **Run workflow**. Nema uploadanja – sve se odrađuje na GitHubu.

**Testiranje:** Nakon što workflow uspješno prođe, u TiviMateu dodaj playlistu (ili ostani na Xtream Codes login), u EPG postavke zalijepi URL na `epg_merged.xml` i pokreni **Osvježi EPG**. Za kanale s programom (Croatia, General, Sport, itd.) trebao bi se pojaviti TV vodič.

**Uskladiivanje kanala:** Prvo se koriste **točni EPG linkovi** (1 URL = 1 kanal) s [tvprofil.net](http://tvprofil.net/xmltv/?channels=): za kanale čiji se channel id točno poklapa (npr. `htv1.hr`, `rtl.hr`, `pink.sr`, Arena Sport, Eurosport…) – nema krivog linkanja. Zatim se dodaju izvori s **iptv-epg.org** po zemljama: spajanje po **channel id** i po **normaliziranom imenu** (npr. "|EXYU| PINK HD" ↔ "Pink"). Workflow koristi sve zemlje s iptv-epg.org (bez limita).

**Pokrivenost po zemljama:** EPG se povlači za **sve zemlje** na iptv-epg.org (AL, AR, AU, AT, BA, BE, BR, BG, CA, HR, CZ, DK, FI, FR, DE, GR, HU, IN, IT, JP, MK, ME, NL, NO, PL, PT, RO, RU, RS, SI, ES, SE, CH, TR, UA, GB, US, …). Ako provider šalje drugačiji tvg-id sufiks (npr. `.uk` umjesto `.gb` za UK, `.rs`↔`.sr` za Srbiju), u `epg_iptv/channel_aliases.py` su definirani **aliasi po zemljama** tako da se kanali i dalje ispravno spoje.

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
   python3 scripts/iptv_epg_server.py
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
python3 scripts/m3u_to_epg.py /path/do/playliste.m3u [izlazni_folder]
```

- **Playlist u TiviMateu**: učitaj `playlist_with_epg.m3u` (file ili URL).
- **EPG u TiviMateu**: izvor = `epg.xml` (file ili URL).

Kad provider promijeni listu, moraš ponovno pokrenuti skriptu i ponovo učitati/hostati datoteke.

---

## Jedan EPG file za TiviMate (s programima gdje ih ima)

**Želiš jedan link koji u TiviMateu učitavaš kao EPG i koji sadrži i stvarne programe?**  
Koristi `build_merged_epg.py`. On generira **jedan** XML file u koji:

- **Svi** tvoji kanali ulaze kao `<channel>` – svaki kanal ima ulaz u EPG-u;
- za kanale koji se poklapaju s [iptv-epg.org](https://iptv-epg.org) (po zemljama) uključuje i **stvarne programe** (TV vodič).

**Nemaju svi kanali programe** – samo oni koji se uspiju uskladiti s iptv-epg.org (po **channel id** ili po **normaliziranom imenu**). Zato mogu dobiti programe i kanali iz General, Sport, EXYU, UK, itd., ne samo Croatia. Ostali kanali i dalje su u fileu (TiviMate ih prikaže), ali bez rasporeda.

```bash
python3 scripts/build_merged_epg.py /path/do/playliste.m3u -o epg_merged.xml
# Opcionalno: --limit-countries 50 (brže, manje zemalja)
```

Izlaz: `epg_merged.xml`. U TiviMateu dodaj **EPG URL** na taj file (npr. ako ga hostaš na GitHubu: raw link na `epg_merged.xml`). Jedan link = svi kanali + programi gdje su dostupni.

---

## Pronalaženje EPG linkova za sve kanale s liste (Playwright)

Skripta `scripts/find_epg_links.py` uspoređuje tvoju M3U listu s EPG izvorima s **iptv-epg.org** (po zemljama) i ispisuje koje kanale imaju dostupan EPG s pravim programom (TV vodič).

1. **Bez Playwrighta** (fiksna lista zemalja):  
   `python3 scripts/find_epg_links.py /path/do/playliste.m3u -o channels_with_epg.csv`  
   Skenira EPG XML-ove za sve zemlje na iptv-epg.org i upisuje u CSV kanale koji se poklapaju (channel_id, name, epg_url).

2. **S Playwrightom** (dohvat liste EPG linkova s weba):  
   `pip install playwright && playwright install chromium`  
   `python3 scripts/find_epg_links.py /path/do/playliste.m3u --use-playwright -o channels_with_epg.csv`

Opcionalno: `--limit-countries 10` (npr. prve 10 zemalja), `--limit-channels 1000` (test na 1000 kanala). Izlaz može biti `.json` umjesto CSV.

---

## Napomene

- **Programski sadržaj**: ovaj EPG samo “registrira” kanale (tvg-id); nema stvarnih programa (vremena, naslovi). Ako nađeš EPG izvor koji koristi iste ID-ove, možeš ga dodati.
- **Cache**: server (odjeljak 2) kešira odgovor providera 5 minuta; nakon toga dohvaća novu listu.
