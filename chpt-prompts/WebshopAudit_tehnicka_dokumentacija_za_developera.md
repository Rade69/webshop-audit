# WebshopAudit — Tehnička dokumentacija za developere

## 1. Svrha ovog dokumenta

Ovaj dokument služi kao **tehnička dokumentacija za developera** koji prvi put ulazi u projekat **WebshopAudit** i treba da:

- razumije kako aplikacija radi
- razumije zašto je arhitektura postavljena ovako
- zna gdje živi koja logika
- zna koje među-zavisnosti postoje
- može bezbjedno održavati i proširivati sistem bez vraćanja starog tehničkog duga

Ovo nije korisničko uputstvo.  
Ovo nije marketinški opis proizvoda.  
Ovo je radna tehnička mapa sistema.

---

# 2. Šta je WebshopAudit

WebshopAudit je desktop audit alat koji analizira produktne stranice webshopova i procjenjuje njihovu spremnost za:

- katalogsku potpunost
- mašinsku čitljivost
- komercijalnu upotrebljivost
- AI / agent discoverability

Aplikacija radi nad listom URL-ova ili sitemap ulazom, prolazi kroz audit pipeline i proizvodi:

- sirove ekstraktovane podatke
- bodovane podatke
- shortlist za ručnu reviziju
- kategorijski summary
- izvještaj za ljude

Drugim riječima, to je **audit engine + GUI preglednik + reporting sloj**.

---

# 3. Visok nivo arhitekture

Aplikacija je organizovana oko jednog glavnog toka:

```text
Input (domain/sitemap/URL list)
    ↓
Discovery
    ↓
Fetch
    ↓
Parse / Extract
    ↓
Score
    ↓
Shortlist / Summary
    ↓
Export
    ↓
Report / GUI prikaz
```

Najvažnija arhitektonska odluka projekta je:

**postoji jedno audit jezgro koje koriste i CLI i GUI.**

To znači da GUI ne smije imati vlastiti “mini audit engine”, niti CLI smije imati svoju paralelnu audit logiku.

---

# 4. Glavni slojevi sistema

## 4.1. Domain sloj (`audit/*`)
Ovo je najvažniji sloj sistema.  
Tu živi stvarna audit logika.

Odgovoran je za:
- discovery URL-ova
- fetch HTML-a
- parsing stranica
- structured data extraction
- scoring
- shortlist
- summary
- eksport rezultata
- report data pripremu

To je **source-of-truth sloj** za audit ponašanje.

## 4.2. Orchestration sloj
Ovaj sloj povezuje domain module u jedan glavni tok.

Najvažniji modul:
- `audit/pipeline.py`

Najvažnija funkcija:
- `run_audit(...)`

Odgovoran je za:
- redoslijed koraka
- shared audit lifecycle
- orchestration za CLI i GUI

## 4.3. Entry point sloj
To su ulazne tačke u aplikaciju.

### CLI
- `main.py`

### GUI
- `main_gui.py`
- `gui/controllers/audit_run_controller.py`

Njihova odgovornost nije da implementiraju audit logiku, nego da:
- prikupe input
- pozovu shared orchestration
- prikažu rezultat korisniku

## 4.4. GUI sloj (`gui/*`)
GUI služi za:
- konfiguraciju run-a
- praćenje progresa
- pregled rezultata
- rad sa review redom

Tokom refaktora je uvedeno pravilo da GUI ne smije nositi business logiku koja pripada domain sloju.

## 4.5. Report / export sloj
Odgovoran za:
- CSV/JSON output
- DOCX izvještaj
- pripremu summary podataka za čitljiv izvještaj

---

# 5. Source-of-truth moduli

Ovo je jedna od najvažnijih sekcija dokumenta.

## 5.1. Data contract
Glavni source-of-truth za shape podataka je:

- `audit/extractor.py`
- `audit/scorer.py`

`extractor.py` definiše šta se izvlači sa stranice.  
`scorer.py` definiše kako se ti podaci pretvaraju u audit signal, flagove i score kolone.

Ako mijenjaš canonical kolone ili značenje polja, moraš pratiti posljedice kroz:
- export
- report
- GUI adaptere
- review tok
- testove

## 5.2. Shared orchestration
Glavni source-of-truth za audit lifecycle je:

- `audit/pipeline.py`

Ovdje živi shared `run_audit()` tok koji koriste:
- CLI
- GUI

Ako se audit lifecycle mijenja, to se radi ovdje, ne u `main.py` i ne u GUI kontroleru.

## 5.3. Shortlist logika
Source-of-truth:
- `audit/shortlist.py`

Ovdje živi:
- izbor kandidata za ručni pregled
- severity
- reason code logika
- sample bucket logika

GUI smije koristiti rezultat ove logike, ali ne smije graditi svoju shortlist semantiku.

## 5.4. Category inference
Source-of-truth:
- `audit/scorer.py`

Category inference nije report trik, nego domain logika.  
Report i CSV summary moraju koristiti rezultat iz ovog sloja.

## 5.5. Report logika
Source-of-truth:
- `audit/report_generator.py`

Report ne smije biti drugi “mini domain engine”.  
Smije:
- koristiti canonical output podatke
- formatirati ih za ljude
- generisati zaključke bazirane na podacima

Ne smije:
- ispravljati domain probleme lokalnim hackovima

## 5.6. GUI display semantika
Source-of-truth za prikaznu semantiku u GUI-u:

- `gui/adapters/results_adapter.py`
- `gui/adapters/review_adapter.py`

Ovi adapteri postoje da spriječe curenje domain interpretacije direktno u tabove.

---

# 6. Struktura projekta i odgovornosti po modulima

## 6.1. `config.py`
Centralno mjesto za ključne default vrijednosti i pragove, npr:
- fetch defaulti
- worker count
- delay
- max URLs
- score težine
- agent-ready prag
- osnovni shortlist limiti

Napomena:
ne mora svaki literal završiti ovdje.  
Heuristike koje su čvrsto dio logike mogu ostati uz modul koji ih koristi.

---

## 6.2. `audit/sitemap.py`
Odgovoran za:
- sitemap discovery
- učitavanje sitemap XML-a
- izvlačenje URL-ova
- osnovno filtriranje URL-ova

Zašto postoji odvojeno:
- discovery logika je odvojena od fetch i parse logike
- lakše je testirati sitemap ponašanje bez ostatka pipeline-a

---

## 6.3. `audit/fetcher.py`
Odgovoran za:
- HTTP request lifecycle
- timeout
- retries
- user-agent
- concurrency
- checkpoint/resume ponašanje
- optional JS-related tokove ako postoje

Zašto postoji odvojeno:
- fetch problemi ne smiju biti pomiješani sa parsing logikom
- omogućava kontrolu nad mrežnim ponašanjem i politeness strategijom

---

## 6.4. `audit/parser.py`
Odgovoran za HTML-level extraction:
- title
- meta description
- H1
- canonical
- robots
- breadcrumb_text
- text length
- image signale
- HTML price signale
- shipping / returns signale

Zašto postoji odvojeno:
- parser se bavi onim što je u HTML-u
- ne treba znati ništa o scoringu ili reportu

---

## 6.5. `audit/schema_parser.py`
Odgovoran za:
- JSON-LD / structured data extraction
- Product / Offer detekciju
- schema field extraction

Zašto postoji odvojeno:
- structured data je zaseban audit kanal
- lakše je testirati i održavati ga odvojeno od HTML parsera

---

## 6.6. `audit/extractor.py`
Odgovoran za spajanje fetch + parser + schema parser rezultata u jedan audit red.

Ovdje nastaje praktični raw data contract.

Zašto postoji:
- jedan URL treba da se pretvori u jednu dosljednu audit jedinicu
- raw extraction mora biti odvojena od scoring logike

---

## 6.7. `audit/scorer.py`
Odgovoran za:
- katalog score
- machine score
- commerce score
- overall score
- flagove
- agent-ready logiku
- category inference
- category summary

Zašto postoji:
- ovo je glavni domain interpretacioni sloj
- sve što znači “šta ti podaci zapravo znače” treba da završi ovdje ili u bliskom helperu

---

## 6.8. `audit/shortlist.py`
Odgovoran za:
- izbor kandidata za ručni pregled
- reason code-ove
- severity nivoe
- sample bucket

Zašto postoji:
- shortlist je poseban domain output, nije samo “najniži score”
- review tok mora biti objašnjiv i stabilan

---

## 6.9. `audit/exporters.py`
Odgovoran za:
- upis CSV/JSON output fajlova
- konzistentan export shape

Zašto postoji:
- eksport ne treba biti razbacan kroz pipeline i GUI
- izlazni fajlovi moraju biti stabilni i testabilni

---

## 6.10. `audit/report_generator.py`
Odgovoran za:
- pretvaranje output podataka u DOCX izvještaj
- scorecard
- key findings
- quick wins
- shortlist prilog
- category summary sekciju

Zašto postoji:
- report je završni sloj za ljude
- treba koristiti canonical podatke bez dupliranja domain logike

---

## 6.11. `audit/pipeline.py`
Najvažniji orchestration modul.

Odgovoran za shared lifecycle:
1. ulaz
2. URL discovery
3. fetch
4. extraction
5. scoring
6. shortlist
7. summary
8. export
9. report (kada je uključen)
10. structured rezultat izvršavanja

Zašto je važan:
- i CLI i GUI moraju ići kroz isti put
- to sprječava drift između entry pointova

---

# 7. GUI arhitektura

## 7.1. Opšti princip
GUI je organizovan tako da ne nosi domain logiku.

Pravilo:
- tabovi prikazuju
- controlleri orkestriraju GUI tok
- state/viewmodel čuva stanje
- adapteri pripremaju display semantiku

---

## 7.2. `gui/tabs/*`
Tabovi su view sloj.

Najvažniji:
- `input_tab.py`
- `results_tab.py`
- `review_queue_tab.py`

Oni smiju:
- renderovati podatke
- emitovati akcije
- raditi UI formatiranje
- reagovati na selekciju

Ne smiju:
- uvoditi scoring semantiku
- tumačiti reason/severity iz sirovih kolona po svom
- graditi vlastite shortlist odluke
- imati paralelne fallback engine-e

---

## 7.3. `gui/controllers/*`
Najvažniji:
- `audit_run_controller.py`
- `results_controller.py`
- `review_controller.py`

Odgovorni su za:
- povezivanje GUI akcija sa logikom
- pripremu i tok podataka prema tabovima
- rad sa state/viewmodel slojem
- pokretanje shared orchestration toka gdje treba

Ne smiju postati novi domain engine.

---

## 7.4. `gui/viewmodels/*`
Odgovorni za:
- čuvanje GUI stanja
- filter state
- selection state
- review state
- prikazne promjene stanja

Zašto postoje:
- razdvajaju UI stanje od domain logike
- smanjuju kompleksnost samih tabova

---

## 7.5. `gui/adapters/*`
Najvažniji:
- `results_adapter.py`
- `review_adapter.py`

Odgovorni za:
- pretvaranje canonical domain podataka u GUI-friendly prikaz
- severity/reason display
- badge i flag display
- formatirane vrijednosti za tabelu i detalje

Zašto postoje:
- da tabovi ne barataju direktno sirovim kolonama i semantikom
- da display mapiranje bude centralizovano

Napomena:
tokom stabilizacije uklonjeni su opasni fallbackovi koji su održavali staru logiku paralelno.

---

# 8. Tok podataka detaljno

## 8.1. Ulaz
Ulaz može doći iz:
- domena
- sitemap-a
- ručne liste URL-ova

## 8.2. Discovery
Ako postoji sitemap ili domen, aplikacija pokušava prikupiti product-like URL-ove.

## 8.3. Fetch
Svaki URL se preuzima preko fetch layera.

## 8.4. Parse / Extract
Parser i schema parser izvlače signale i `extractor.py` ih sklapa u raw audit podatke.

## 8.5. Score
Scorer pretvara raw podatke u:
- score kolone
- flagove
- agent-ready signal
- category inference
- summary

## 8.6. Shortlist
Shortlist layer bira:
- stvarne problematične kandidate
- mali broj sample kandidata kada to ima smisla

## 8.7. Export
Output fajlovi se upisuju u output direktorij.

## 8.8. Report
Ako je uključeno, report layer generiše DOCX dokument.

## 8.9. GUI prikaz
GUI učitava rezultate, adapteri ih mapiraju u prikazni sloj, a korisnik radi pregled i reviziju.

---

# 9. Canonical output fajlovi

Najvažniji output fajlovi su:

- `products_raw.csv`
- `products_scored.csv`
- `manual_review_candidates.csv`
- `best_products_sample.csv`
- `category_summary.csv`
- `non_product_pages.csv`
- `errors.csv`
- `run_summary.json`
- `audit_report.docx` (ako je uključen)

Ovi fajlovi su važni jer:
- predstavljaju ugovor između domain sloja i ljudskog rada
- koriste se i za ručnu analizu i za report
- služe kao praktični izlazni interfejs alata

---

# 10. Zašto su neke odluke donesene ovako

## 10.1. Zašto jedan shared `run_audit()`
Zato što paralelni CLI i GUI tok vrlo brzo vode ka:
- drugačijim rezultatima
- duplim bugfixevima
- rastućem tehničkom dugu

Jedan shared tok smanjuje rizik.

## 10.2. Zašto adapteri u GUI-u
Zato što je ranije GUI curio u domain interpretaciju:
- flagovi
- severity
- reason display
- detalji

Adapteri to centralizuju i čuvaju tabove tanjim.

## 10.3. Zašto shortlist ima severity + reasons
Zato što “najnižih N scoreova” nije dovoljno korisno za ručni rad.

Review red mora biti:
- objašnjiv
- prioritetan
- praktičan za ljude

## 10.4. Zašto sample bucket postoji
Sample bucket nije problem lista.  
On služi za:
- benchmark
- sanity check
- poređenje dobrih i loših primjera

Ali nakon stabilizacije ograničen je tako da ne zatrpa shortlist.

## 10.5. Zašto category inference živi u scorer-u
Zato što kategorija nije report dekoracija, nego domain interpretacija.  
Ako bi report imao svoju category logiku, nastao bi drugi izvor istine.

---

# 11. Pravila za buduće izmjene

Ovo su najvažnija praktična pravila.

## 11.1. Ne uvoditi nove alias kolone bez pune propagacije
Ako mijenjaš canonical naziv kolone:
- moraš provjeriti extractor
- scorer
- export
- report
- GUI adaptere
- testove

## 11.2. Ne stavljati business logiku u tabove
Tab nije mjesto za:
- severity semantiku
- shortlist logiku
- score tumačenje
- category inference
- reason kod mapiranje kao source-of-truth

## 11.3. Ne popravljati domain problem u reportu
Ako je category summary loš zbog scorera, ne rješavaj to u report generatoru.

## 11.4. Ne uvoditi drugi orchestration put
Sve audit izmjene moraju proći kroz shared `run_audit()` put.

## 11.5. Ne vraćati fallback engine-e u GUI
Ako adapter nije spreman:
- prikaži prazan state
- ili jasan guard

Nemoj vraćati paralelni stari put.

## 11.6. Ne širiti heuristike bez testova
Ako dodaješ:
- category rules
- shortlist rules
- scoring heuristike

moraš dodati ili ažurirati testove.

---

# 12. Poznati preostali tehnički dugovi

Ovo su poznati dugovi koji još postoje ili mogu ostati osjetljive tačke.

## 12.1. Category inference nije savršen
Jeste mnogo bolji nego ranije, ali i dalje zavisi od:
- breadcrumb kvaliteta
- URL obrasca
- title/H1 signala
- ručno održavanih heuristika

To je sada upotrebljivo, ali nije “riješeno zauvijek”.

## 12.2. DOCX formatting edge-caseovi
Report radi i stabilan je, ali DOCX tekstualni layout i duži sadržaji mogu i dalje imati sitne formatting anomalije.

## 12.3. GUI smoke provjera ostaje važna
Automatizovani testovi su jaki, ali i dalje vrijedi povremeno ručno provjeriti:
- results tok
- review tok
- audit run iz GUI-a

## 12.4. Heurističke liste traže održavanje
Liste za:
- category inference
- product pattern filtering
- generic category filtering

su svjesno rule-based i tražiće povremeno održavanje kad se pojave novi sajtovi ili novi obrasci.

## 12.5. QSettings i user override granice
GUI čuva dio korisničkih postavki.  
To je namjerno, ali treba paziti na granicu između:
- config defaulta
- user override-a
- shared pipeline ponašanja

---

# 13. Test strategija

Projekt sada ima kombinaciju:

- unit testova
- integration testova
- end-to-end-like testova sa kontrolisanim inputom

Najvažniji ciljevi testova su:
- zaštita main audit lifecycle-a
- zaštita canonical output shape-a
- zaštita shortlist semantike
- zaštita category summary logike
- zaštita shared orchestration puta
- zaštita GUI adapter semantike

Pravilo za budući rad:
ako promjena utiče na više slojeva, treba testirati i njihovu vezu, ne samo jedan mali modul.

---

# 14. Preporučeni način održavanja

Ako developer prvi put ulazi u projekat, preporučeni redoslijed je:

1. pročitati ovaj dokument
2. pročitati `AGENTS_webshop_audit.md`
3. pročitati `CLAUDE_webshop_audit.md`
4. pregledati:
   - `config.py`
   - `audit/pipeline.py`
   - `audit/scorer.py`
   - `audit/shortlist.py`
   - `audit/report_generator.py`
   - `gui/adapters/results_adapter.py`
   - `gui/adapters/review_adapter.py`
5. pokrenuti testove
6. napraviti mali CLI run
7. napraviti mali GUI run

Tek poslije toga uvoditi izmjene.

---

# 15. Siguran redoslijed za budući razvoj

Najsigurniji razvojni redoslijed je:

1. prvo promijeni domain logiku
2. zatim update export/report ako treba
3. zatim update GUI adaptere ako treba
4. zatim update tabove/controller sloj ako je nužno
5. zatim update testove
6. na kraju uradi ručni smoke test

Ne obrnutim redom.

---

# 16. Šta ne dirati napamet

Bez detaljne provjere ne diraj napamet:

- canonical nazive kolona
- `run_audit()` lifecycle
- shortlist severity/reason model
- sample bucket pravila
- category inference fallback pravila
- GUI adapter source-of-truth mapiranja
- report ulazne kolone

To su osjetljive tačke sistema.

---

# 17. Kratak ASCII pregled sistema

```text
CLI / GUI
   ↓
shared orchestration
(audit/pipeline.py :: run_audit)
   ↓
discovery / fetch / parse / schema extract
   ↓
raw extraction contract
(audit/extractor.py)
   ↓
scoring / flags / categories
(audit/scorer.py)
   ↓
shortlist / sample selection
(audit/shortlist.py)
   ↓
export / report
(audit/exporters.py, audit/report_generator.py)
   ↓
GUI adapters / results / review
(gui/adapters/*, gui/tabs/*)
```

---

# 18. Završna napomena

Ako ovaj projekat ostane disciplinovan u pogledu:
- jednog data contracta
- jednog orchestration puta
- čistog razdvajanja GUI i domain logike
- testova za glavne tokove

onda je dalji razvoj razumno siguran.

Ako se ponovo krene sa:
- lokalnim hackovima
- report-only ispravkama
- logikom u tabovima
- paralelnim CLI/GUI putevima

projekat će se ponovo brzo vratiti u stanje tehničkog duga.

Zato ovaj dokument treba koristiti kao praktičnu mapu, ne kao formalnost.
