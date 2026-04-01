# AGENTS.md — projektni standard za **WebshopAudit**

**Čitaj zajedno sa globalnim agent uputstvima, ali ovaj fajl ima prvenstvo za ovaj projekat.**  
Ovaj dokument je specifičan za projekat **WebshopAudit** — desktop + CLI alat za audit produktnih stranica webshopova sa fokusom na **agent-readiness**, structured data, cijene, opis, slike i ručnu reviziju.

---

## 1. Stack

| Komponenta | Verzija / detalj |
|------------|------------------|
| Jezik | Python 3.11+ |
| Desktop GUI | **PyQt6** |
| CLI | `argparse` |
| HTTP fetch | `requests` + retry logika |
| Parsing HTML | BeautifulSoup (`bs4`) |
| Structured data | JSON-LD / Schema.org parsing |
| Data obrada | `pandas` |
| Progres u CLI | `tqdm` (opcionalno) |
| Izvještaj | `.docx` generator u `audit/report_generator.py` |
| Testovi | `pytest` |

---

## 2. Arhitektura — obavezna podjela odgovornosti

Projekat ima dva glavna moda rada:

1. **CLI audit tok**
2. **GUI audit tok**

Oba moda **moraju koristiti isto jezgro domena**.  
Ne smije se desiti da CLI i GUI implementiraju istu poslovnu logiku na dva različita načina.

### Osnovni slojevi

```text
GUI View / CLI Entry
        ↓
Controller / Orchestration
        ↓
Domain pipeline (audit/*)
        ↓
Export / Reporting
```

### Obavezna pravila

- **View sloj**: samo UI, signali, prikaz, validacija unosa koja je čisto UI prirode
- **Controller sloj**: orchestration, state sync, pozivanje pipeline-a, mapiranje akcija
- **Domain sloj (`audit/*`)**: parsing, extraction, scoring, shortlist, eksport
- **Config sloj (`config.py`)**: svi tunable pragovi, defaulti i heuristike

### Strogo zabranjeno

- Business logika u `gui/tabs/*.py`
- Dupliciranje scoring logike u GUI kontrolerima
- Dupliciranje shortlist logike u rezultat tabovima
- Ručno rekalkulisanje kolona u exporterima ili report generatoru ako već postoje u scoreru
- Posebna “GUI verzija” data modela koja odstupa od `ProductAuditRow` / scored DataFrame contracta

---

## 3. Jedini izvor istine za podatke — KRITIČNO

Najveći rizik u ovom projektu je **drift naziva kolona i semantike podataka** između:

- `audit/extractor.py`
- `audit/scorer.py`
- `audit/shortlist.py`
- `audit/exporters.py`
- `audit/report_generator.py`
- `gui/controllers/*.py`
- `gui/tabs/results_tab.py`
- `gui/tabs/review_queue_tab.py`

### Pravilo

**Ako se promijeni naziv polja ili značenje polja u extractor/scorer sloju, moraju se ažurirati svi zavisni dijelovi.**

### Trenutni canonical nazivi sirovih kolona

```text
url
final_url
status_code
fetch_error
content_type
response_time_ms
title
meta_description
h1
canonical
robots_meta
breadcrumb_text
visible_text_length
image_count
product_image_count
html_price_text
shipping_signal
returns_signal
description_word_count
has_feature_list
has_spec_table
description_quality_score
schema_product_present
schema_offer_present
schema_name
schema_description
schema_sku
schema_gtin
schema_brand
schema_price
schema_price_value
schema_currency
schema_availability
is_likely_product_page
is_likely_js_rendered
js_render_confidence
```

### Trenutni canonical nazivi score/flag kolona

```text
catalog_score
machine_score
commerce_score
overall_score
missing_fields
indexability_flags
flag_noindex
flag_canonical_mismatch
flag_fetch_error
flag_non_200
flag_js_rendered
suspicious_price_missing
suspicious_schema_missing
suspicious_low_content
flag_not_product_page
agent_ready
```

### Zabranjeni zastarjeli aliasi

Ako ih nađeš u kodu, tretiraj ih kao bug ili tehnički dug:

| Ispravno | Zastarjelo / pogrešno |
|----------|------------------------|
| `breadcrumb_text` | `breadcrumb` |
| `schema_product_present` | `schema_product` |
| `html_price_text` | `price_html`, `html_price` |
| `schema_price` | `price_schema` |
| `flag_canonical_mismatch` | `canonical_issue`, `flag_canonical_missing` |
| `is_likely_product_page` | `is_product_page` |
| `is_likely_js_rendered` | `flag_js_only`, `js_rendered` |

**Agent ne smije uvoditi nove alias nazive bez eksplicitne potrebe i migracionog plana.**

---

## 4. Domain pipeline — šta koji modul smije raditi

### `audit/sitemap.py`
Odgovoran za:
- discovery sitemapa
- fetch sitemap XML-a
- parsiranje sitemap URL-ova
- heurističko filtriranje product-like URL-ova

Ne smije raditi:
- scoring
- HTML parsing produktne stranice
- eksport rezultata

### `audit/fetcher.py`
Odgovoran za:
- HTTP request
- retry
- timeout
- user-agent
- optional concurrency / optional Playwright integration

Ne smije raditi:
- DOM parsing
- scoring
- shortlist odluke

### `audit/parser.py`
Odgovoran za:
- HTML signal extraction
- title, H1, meta, canonical, breadcrumb, slike, cijena, text signals
- description quality signale
- JS-render heuristiku

Ne smije raditi:
- DataFrame transformacije
- scoring
- eksport

### `audit/schema_parser.py`
Odgovoran za:
- JSON-LD blokove
- flatten graph objekata
- Product / Offer pronalazak
- ekstrakciju schema polja

Ne smije raditi:
- HTML heuristike van schema domene
- scoring

### `audit/extractor.py`
Odgovoran za:
- sklapanje `fetch_result` + `parser` + `schema_parser`
- gradnju `ProductAuditRow`
- konverziju rows → DataFrame

Ne smije raditi:
- scoring
- shortlist
- reporting business logiku

### `audit/scorer.py`
Odgovoran za:
- score izračun
- flag detekciju
- `agent_ready`
- sitewide summary
- category summary

Ne smije raditi:
- fetch
- HTML parsing
- GUI prilagodbe

### `audit/shortlist.py`
Odgovoran za:
- izbor kandidata za manual review
- izbor best sample stranica

Ne smije raditi:
- eksport
- GUI status management
- ručno tumačenje detalja stranice

### `audit/report_generator.py`
Odgovoran za:
- čitanje postojećih output fajlova
- generisanje izvještaja iz stabilnog data contracta

Ne smije:
- uvoditi vlastite “lokalne” nazive kolona
- tiho pretpostavljati stare kolone bez fallback logike i validacije

---

## 5. GUI pravila

### Struktura GUI-a

```text
gui/
├── controllers/
├── tabs/
├── viewmodels/
├── widgets/
└── styles/
```

### Obavezna pravila

- Tabovi su primarno **view sloj**
- Kontroleri orkestriraju
- Viewmodels/state objekti čuvaju UI stanje
- `theme.py` je isključivo za vizuelne stilove i helper funkcije za stil

### Strogo zabranjeno

- da tab direktno računa shortlist
- da tab sam tumači kolone koje nisu mapirane kroz controller/state
- da controller uvodi nove “privremene” kolone koje ne postoje u canonical data contractu
- da GUI izmišlja fallback vrijednosti koje skrivaju backend problem

### Ako GUI ne nalazi kolonu

Ne “krpi” je lokalno.  
Prvo provjeri:
1. `ProductAuditRow`
2. `build_scored_dataframe()`
3. export CSV
4. report generator
5. results/review controller mapiranje

---

## 6. Shortlist i review queue — posebna pravila

Ovaj projekat razlikuje dva koncepta:

1. **automatski shortlist kandidata**
2. **korisnički review queue workflow**

To nisu iste stvari.

### Obavezno

- `manual_review_candidates.csv` dolazi iz `audit/shortlist.py`
- GUI review queue može nad tim dodati statuse i bilješke
- Ali GUI ne smije mijenjati sam shortlist kriterije bez promjene u domain sloju

### Trenutni problem koji treba poštovati

Ako shortlist puni listu “do `top_n`” najlošijim ostalim stranicama, review queue gubi smisao.  
Kod svih izmjena shortlist logike mora se paziti na:

- prioritetne tierove
- severity
- deduplikaciju
- realan broj kandidata
- odvajanje “kritično za pregled” od “samo niska ocjena”

---

## 7. Pravila za scoring i agent-ready logiku

- `catalog_score`, `machine_score`, `commerce_score` su odvojene dimenzije
- `overall_score` je ponderisani rezultat
- `agent_ready` je strogo izveden signal i ne smije se računati u GUI-u

### Zabranjeno

- mijenjati score težine direktno u kodu tabova
- uvoditi skriveni bonus/malus mimo `scorer.py`
- prebacivati schema signale u `catalog_score`
- miješati `image_count` i `product_image_count` bez jasnog razloga

---

## 8. Kategorije i breadcrumb logika

Trenutna category summary logika koristi `breadcrumb_text` i izvlači kategoriju iz segmenta.

To je heuristika, ne apsolutna istina.

### Pravila

- Ako mijenjaš category inference, uradi to u `scorer.py` ili izdvojenom domain helperu
- Ne uvoditi category heuristiku u GUI filterima kao drugi izvor istine
- Ako breadcrumb ne postoji, fallback mora biti eksplicitan (`Unknown` ili druga jasno definisana vrijednost)

---

## 9. Config pravila

Sve tunable vrijednosti moraju biti u `config.py`, uključujući:
- delay
- timeout
- retries
- max workers
- default score weights
- shortlist veličine
- heurističke pragove
- URL pattern liste

### Zabranjeno

- hardkodirati pragove u GUI tabovima
- imati drugi set defaulta u testovima bez jasnog razloga
- uvoditi magične brojeve u scoring ili shortlist funkcije

---

## 10. Testiranje — obavezna disciplina

### Kad mijenjaš domain sloj

Moraš provjeriti relevantne testove:
- parser
- schema_parser
- extractor
- scorer
- shortlist / pipeline
- eksport / report ako je zahvaćen

### Kad mijenjaš GUI sloj

Moraš provjeriti:
- controller testove
- state/viewmodel testove
- tab testove pogođenog taba

### Posebno obavezno

Ako se mijenja naziv kolone ili shape DataFrame-a:
- testirati `extractor`
- testirati `scorer`
- testirati `results_controller`
- testirati `review_controller`
- testirati report generator scenarije

### Zabranjeno

- “fix” bez provjere uticaja na CSV output
- mock-ovati sve do te mjere da se ne vidi realan problem data contracta
- dodavati test koji samo potvrđuje bug umjesto da štiti ponašanje

---

## 11. Pravila za refaktor

Kad agent radi refaktor, mora poštovati sljedeći redoslijed:

1. Identifikuj canonical source-of-truth modul
2. Mapiraj sve zavisne module
3. Refaktoriši domain sloj
4. Ažuriraj GUI adaptore/controller mapiranje
5. Ažuriraj eksport/report sloj
6. Tek onda “počisti” stil i duplikate

### Zabranjeno

- prvo “ušminkati” GUI pa naknadno rješavati data contract
- refaktorisati više slojeva bez eksplicitnog popisa pogođenih fajlova
- mijenjati naziv kolona bez migracionog plana

---

## 12. Format izlaza koji agent treba vratiti

Za svaki zadatak agent mora vratiti:

1. **Šta je promijenjeno**
2. **Koji fajlovi su dirani**
3. **Koje među-zavisnosti su provjerene**
4. **Koji rizici ostaju**
5. **Koji testovi su pokrenuti / koje scenarije treba ručno provjeriti**

Ako nešto nije jasno ili je blokirano, označiti kao:

```text
BLOKIRANO:
- razlog
- koji fajl / sloj zavisi od toga
- šta treba razjasniti prije nastavka
```

---

## 13. Struktura projekta (aktuelna)

```text
webshop_audit/
├── main.py
├── config.py
├── audit/
│   ├── exporters.py
│   ├── extractor.py
│   ├── fetcher.py
│   ├── parser.py
│   ├── pipeline.py
│   ├── report_generator.py
│   ├── schema_parser.py
│   ├── scorer.py
│   ├── shortlist.py
│   ├── sitemap.py
│   └── utils.py
├── gui/
│   ├── app_state.py
│   ├── main_window.py
│   ├── controllers/
│   ├── tabs/
│   ├── viewmodels/
│   ├── widgets/
│   └── styles/
├── tests/
├── outputs/
└── requirements.txt
```

---

## 14. Ključni razvojni prioriteti za ovaj projekat

1. **Uskladiti data contract kroz cijeli sistem**
2. **Srediti shortlist da bude stvarno koristan**
3. **Razdvojiti GUI prikaz od domain interpretacije**
4. **Uskladiti report generator sa scorer kolonama**
5. **Pojačati category inference bez dupliranja logike**
6. **Držati CLI i GUI na istom orchestration putu**

---

## 15. Što je posebno zabranjeno u ovom projektu

| Zabrana | Razlog |
|---------|--------|
| Uvoditi novu “privremenu” kolonu samo u GUI-u | Stvara drift i skrivene bugove |
| Preimenovati canonical kolone bez pune propagacije | Lomi GUI, report i CSV |
| Pisati scoring u tabovima ili controllerima | Gubitak jednog izvora istine |
| Krpiti report generator lokalnim aliasima bez validacije | Izvještaj postaje nepouzdan |
| Puniti shortlist samo do `top_n` najnižim scoreovima bez severity logike | Review queue gubi smisao |
| Miješati ne-produktne stranice sa produktnim bez eksplicitne oznake | Kvari analizu i summary |
| Tumačiti GUI fallback kao “riješen backend problem” | Sakriva suštinski bug |

---

*Ovaj fajl je prilagođen projektu WebshopAudit kao stabilan skup pravila za agente i refaktor rad.*
