# PROMPT — FAZA 1: Konsolidacija data contracta kroz cijeli sistem

Radiš na projektu **WebshopAudit**.

Prije rada obavezno pročitaj:
- `AGENTS_webshop_audit.md`
- `CLAUDE_webshop_audit.md`

Ovaj zadatak je **isključivo Faza 1** iz plana refaktora.  
Ne radi Fazu 2, 3, 4 ili 5.  
Ne dodaji nove featuree.  
Ne radi vizuelni polish GUI-a.  
Ne mijenjaj shortlist logiku osim ako je neophodno samo da se ukloni data-contract drift.

---

# 1. Cilj zadatka

Cilj je da kroz cijeli sistem uskladiš **canonical nazive kolona i njihovo značenje**, tako da:

- `extractor`
- `scorer`
- `exporters`
- `report_generator`
- `results_controller`
- `review_controller`
- `results_tab`
- `review_queue_tab`

koriste **ista imena polja** i **isto značenje polja**.

Na kraju rada mora važiti:

- jedno polje = jedno ime = jedno značenje
- GUI ne koristi zastarjele alias nazive
- report generator ne koristi zastarjele alias nazive
- eksport i prikaz koriste isti data contract
- nema “lokalnih” prevoda kolona samo da bi GUI proradio

---

# 2. Najvažnije pravilo

**Ne uvoditi nove alias kolone kao brzo rješenje.**

Ako je canonical naziv već definisan u source-of-truth sloju, onda:
- koristi taj naziv
- propagiraj ga u zavisne module
- ukloni zastarjele reference gdje je sigurno

Ne praviti:
- `breadcrumb` ako je canonical `breadcrumb_text`
- `schema_product` ako je canonical `schema_product_present`
- `price_html` ako je canonical `html_price_text`
- `price_schema` ako je canonical `schema_price`
- `canonical_issue` ako je canonical `flag_canonical_mismatch`
- `is_product_page` ako je canonical `is_likely_product_page`

Ako negdje postoji stari naziv, tretiraj to kao tehnički dug ili bug.

---

# 3. Scope — šta tačno radiš

## 3.1. Prvo identifikuj source-of-truth

Utvrdi:
- koji modul definiše shape raw audit reda
- koji modul definiše scored DataFrame shape
- koje kolone su canonical za raw nivo
- koje kolone su canonical za score/flag nivo

Očekivano je da to budu uglavnom:
- `audit/extractor.py`
- `audit/scorer.py`

Ali nemoj pretpostavljati — potvrdi čitanjem koda.

---

## 3.2. Mapiraj sve zavisne dijelove koji koriste te kolone

Obavezno pregledaj najmanje ove fajlove:

### Domain / export / report
- `audit/extractor.py`
- `audit/scorer.py`
- `audit/exporters.py`
- `audit/report_generator.py`
- `audit/pipeline.py`

### GUI controller / tab sloj
- `gui/controllers/results_controller.py`
- `gui/controllers/review_controller.py`
- `gui/tabs/results_tab.py`
- `gui/tabs/review_queue_tab.py`

### Po potrebi i ostale fajlove ako oni koriste iste kolone
- viewmodel/state sloj
- helper funkcije za tabelarni prikaz
- testove koji očekuju stara imena

---

## 3.3. Uskladi reference na kolone

Potrebno je:
- zamijeniti zastarjele nazive canonical nazivima
- ukloniti lokalne pretpostavke o starim imenima
- provjeriti da GUI filteri i detalji čitaju stvarne kolone
- provjeriti da report generator čita stvarne kolone
- provjeriti da exporter i CSV shape ostaju dosljedni

---

## 3.4. Zaštiti ponašanje testovima

Dodaj ili ažuriraj testove tako da štite:
- canonical shape raw DataFrame-a
- canonical shape scored DataFrame-a
- da `results_controller` koristi aktuelna imena kolona
- da `review_controller` koristi aktuelna imena kolona
- da report generator ne zavisi od starih naziva

Ne piši testove koji samo prate internu implementaciju.  
Piši testove koji štite **data contract**.

---

# 4. Među-zavisnosti koje moraš obavezno provjeriti

Ovo je najbitniji dio zadatka.

Ako promijeniš ili potvrdiš canonical naziv u `extractor/scorer`, moraš provjeriti uticaj na:

1. **CSV output**
   - da li izlazni fajlovi imaju očekivane kolone

2. **Report generator**
   - da li i dalje čita tačne kolone
   - da li koristi stara imena

3. **Results tab / results controller**
   - filteri
   - badge-ovi
   - detalji selektovanog reda
   - tabele i kolone

4. **Review queue**
   - prikaz kandidata
   - detalji
   - eventualne oznake razloga/flagova

5. **Pipeline**
   - da li orchestration i eksport koriste isti shape

6. **Testovi**
   - da li postoje testovi koji očekuju stara imena
   - da li treba dopuniti coverage

---

# 5. Šta je dozvoljeno, a šta nije

## Dozvoljeno
- refaktor reference na kolone
- dopuna testova
- manje helper funkcije ako smanjuju duplikaciju
- centralizacija mapping logike ako je mala i jasna
- eksplicitna validacija očekivanih kolona gdje ima smisla

## Nije dozvoljeno
- uvoditi nove featuree
- raditi shortlist redesign
- mijenjati score logiku osim ako je apsolutno neophodno zbog usklađivanja naziva
- raditi veći GUI redesign
- maskirati backend problem GUI fallbackom
- uvoditi “privremeni compatibility layer” bez jakog razloga

Ako misliš da je compatibility layer neophodan, moraš to posebno objasniti i svesti na minimum.

---

# 6. Kriterij uspjeha

Zadatak je završen tek kad su ispunjeni svi uslovi:

- nema aktivnog drift-a između canonical kolona i GUI/report sloja
- `results_controller` i `review_controller` ne koriste zastarjele alias nazive
- `results_tab` i `review_queue_tab` ne očekuju stara imena bez opravdanja
- `report_generator` koristi aktuelna canonical polja
- testovi štite shape i najvažnije zavisnosti
- nema lokalnih “krpljenja” samo da UI ne pukne

---

# 7. Očekivani izlaz od tebe

Vrati odgovor u ovom formatu:

## 1. Šta je promijenjeno
- kratko i jasno

## 2. Pogođeni fajlovi
- kompletan spisak

## 3. Source-of-truth potvrda
- gdje je potvrđen raw shape
- gdje je potvrđen scored shape

## 4. Među-zavisnosti provjerene
- CSV output
- report generator
- results controller/tab
- review controller/tab
- pipeline
- testovi

## 5. Rizici koji ostaju
- napiši iskreno ako nešto još nije potpuno zatvoreno

## 6. Testovi
- koje si pokrenuo
- koji su prošli
- šta ostaje za ručnu provjeru

Ako je nešto blokirano, napiši:

**BLOKIRANO**
- razlog
- fajlovi / slojevi koje blokira
- šta tačno treba razjasniti

---

# 8. Završna napomena

Ne pokušavaj “usput” sređivati shortlist, category summary, GUI strukturu ili orchestration.  
Ovaj zadatak je uspješan samo ako disciplinovano zatvoriš **Fazu 1 — data contract konsolidaciju**.

Ako vidiš druge probleme, navedi ih pod **Rizici koji ostaju**, ali ih ne rješavaj u ovom zadatku osim ako direktno blokiraju Fazu 1.
