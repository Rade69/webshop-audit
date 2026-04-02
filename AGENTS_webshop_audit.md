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

### `audit/run_diff.py`
Odgovoran za:
- poređenje dva audit run-a (old vs new)
- URL matching putem normaliziranih URL-ova
- score delta calculation (new_score - old_score)
- issue detection (resolved vs new issues)
- severity change detection (CRITICAL/HIGH/MEDIUM/LOW/NONE)
- category summary diff (ako postoji category_summary.csv)
- export diff rezultata u JSON/CSV format

Ne smije raditi:
- modificiranje originalnih run outputa
- GUI logiku (samo domain diff)
- scoring ili shortlist logiku (koristi postojeće iz scorer/shortlist)

### `audit/explainability.py`
Odgovoran za:
- human-readable objašnjenja za reason code-ove
- template-based explanation generation (deterministička)
- priority ordering objašnjenja (critical → high → medium → low)
- combined explanation (spajanje top 2 objašnjenja)
- sample candidate detection (razlikovanje uzoraka od problema)

Ne smije raditi:
- LLM generisanje teksta
- izmišljanje uzroka koji nisu u podacima
- dugačka objašnjenja (max 1-2 rečenice)

### `audit/evidence.py`
Odgovoran za:
- evidence snapshots za audit nalaze
- dokazni paket za svaki finding (cijena, schema, indexability, content)
- evidence extraction iz postojećih podataka (ne duplicira extraction)
- formatted display za GUI i report

Ne smije raditi:
- screenshot crawling
- heavy storage sistem
- dump cijelog HTML-a

### `audit/issue_grouping.py`
Odgovoran za:
- issue-centric grupisanje URL-ova po tipu problema
- issue summary (count, pct_affected, avg_score)
- issue-to-URLs mapping za CSV export
- filter preset-e za GUI (quick filter po problemu)

Ne smije raditi:
- drugi source-of-truth za issues (koristi flag kolone iz scorer-a)
- generički BI dashboard

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

## 8a. Run-to-run diff feature

Feature za poređenje dva audit run-a (old vs new) radi na nivou:
- **aggregate summary**: prosječni score-ovi, critical/high counts, price/schema counts
- **URL level**: score delta, resolved issues, new issues, severity change
- **category level**: promjene po kategorijama (ako postoji category_summary)

### Output fajlovi

Diff generiše tri nova output fajla u **new run** direktoriju:

```text
run_diff_summary.json    — aggregate statistike
run_diff_urls.csv        — URL-level diff (svi URL-ovi)
run_diff_categories.csv  — category-level diff (ako postoji category_summary)
```

### Matching logika

- **Primarni ključ**: normalizirani URL (bez tracking parametara, www, http/https razlika)
- **Novi URL-ovi**: postoje samo u new run → status "new"
- **Removed URL-ovi**: postoje samo u old run → status "removed"
- **Common URL-ovi**: postoje u oba → status "unchanged"/"improved"/"degraded"

### Severity inference

Diff module inferiše severity iz score + flags (isti princip kao `ShortlistCandidate`):
- **CRITICAL**: fetch_error, non_200, not_product_page
- **HIGH**: noindex, canonical_mismatch, missing price+schema together
- **MEDIUM**: missing price OR schema OR low_content OR js_rendered
- **LOW**: score < 40
- **NONE**: score >= 40, no flags

### Pravila

- Diff je **opciona** faza — pokreće se samo ako je `compare_with_previous` postavljen
- Diff ne smije modificirati originalne output fajlove
- Diff koristi canonical kolone iz scorer-a (ne uvodi nove alias-e)
- Category diff je optional — zavisi od postojanja `category_summary.csv`

---

## 8b. Explainability feature — human-readable objašnjenja

Feature za automatsko generisanje ljudski čitljivih objašnjenja zašto stranica ima problema.

### Kako radi

1. **Reason code-ovi** iz `ShortlistCandidate` se mapiraju u template objašnjenja
2. **Template** sadrži placeholder-e za stvarne podatke (npr. `{status_code}`, `{canonical}`)
3. **Priority ordering** osigurava da najkritičniji problemi budu prvi
4. **Combined explanation** spaja top 2 objašnjenja u jednu rečenicu

### Output

Objašnjenja su dostupna u:
- `manual_review_candidates.csv` — kolona `explanation`
- GUI review details panel — `ReviewAdapter.get_explanation()`
- `is_sample` flag — razlikuje uzorke od stvarnih problema

### Template primjeri

```
"fetch-error": "Stranica se ne može preuzeti — HTTP zahtjev nije uspio ({fetch_error})."
"canonical-mismatch": "Canonical URL ({canonical}) pokazuje na drugu stranicu — ova stranica možda nije glavna verzija."
"missing-price": "HTML nema jasan signal cijene — kupci možda ne vide cijenu odmah."
```

### Pravila

- Objašnjenja moraju biti **deterministička** (isti input → isti output)
- Moraju koristiti **stvarne podatke** iz row-a
- Ne smiju biti **preduga** (max 1-2 rečenice)
- **Single source-of-truth** — `audit/explainability.py`
- Sample kandidati imaju objašnjenje ali `is_sample=True`

---

## 8c. Evidence snapshots — dokazni paket za nalaze

Feature za pružanje dokaza zašto je alat donio određeni zaključak.

### Evidence fields

Evidence snapshot sadrži:

**HTTP/Response:**
- `status_code` — HTTP status kod
- `fetch_error` — greška pri preuzimanju (ako postoji)

**Indexability:**
- `canonical` — extracted canonical URL
- `robots_meta` — robots meta tag string

**Price evidence:**
- `html_price_text` — cijena iz HTML-a
- `schema_price` — cijena iz structured data
- `schema_price_value` — numeric price value
- `schema_currency` — currency code

**Product identification:**
- `schema_product_present` — da li postoji Product schema
- `schema_offer_present` — da li postoji Offer schema
- `schema_sku` — SKU iz structured data
- `schema_brand` — brand iz structured data

**Content:**
- `breadcrumb_text` — breadcrumb putanja
- `title` — page title
- `h1` — H1 heading
- `visible_text_length` — dužina vidljivog teksta

**Classification:**
- `is_likely_product_page` — da li je produktna stranica
- `is_likely_js_rendered` — da li je JS renderirana

### Output

Evidence je dostupan u:
- `manual_review_candidates.csv` — kolona `evidence_summary` (kratki string)
- GUI review details panel — `ReviewAdapter.get_evidence_summary()` i `get_full_evidence()`
- `audit/evidence.py` — `format_evidence_for_display()` za terminal/report

### Evidence summary format

Za CSV export, evidence_summary je string format:
```
HTML cijena: €99.99 | Schema cijena: nije pronađena | Product schema: ✓ | Canonical: https://...
```

### Pravila

- Koristiti **postojeće extracted podatke** — ne duplicirati extraction
- **Ne dumpovati cijeli HTML** — samo strukturirani signali
- **Fokus na 5-10 najkorisnijih signala** — ne pretrpavati
- Evidence mora biti **ljudski čitljiv** — ne mašinski format

---

## 8d. Issue-centric view — rad po problemima

Feature za pregled i rad po vrstama problema umjesto po URL-ovima.

### Issue definicije

Canonical issue definicije u `audit/issue_grouping.py`:

| issue_id | display_name | flag_column | priority |
|----------|--------------|-------------|----------|
| fetch_error | Fetch greška | flag_fetch_error | 1 |
| non_200 | Nije 200 OK | flag_non_200 | 1 |
| not_product_page | Nije produktna stranica | flag_not_product_page | 1 |
| noindex | Noindex | flag_noindex | 2 |
| canonical_mismatch | Canonical mismatch | flag_canonical_mismatch | 2 |
| missing_price | Nema cijene | suspicious_price_missing | 2 |
| missing_schema | Nema Product schema | suspicious_schema_missing | 2 |
| js_rendered | JS render | flag_js_rendered | 3 |
| low_content | Malo sadržaja | suspicious_low_content | 3 |

### Output fajlovi

Issue-centric generiše dva output fajla:

```text
issue_summary.csv      — summary po issue tipu (count, avg_score, pct_affected)
issue_to_urls.csv      — mapping issue → URL-ovi (jedan red po issue-URL paru)
```

### issue_summary.csv kolone

- `issue_id` — mašinski identifikator
- `display_name` — ljudsko ime
- `description` — kratak opis
- `priority` — prioritet (1 = najviši)
- `count` — broj pogođenih URL-ova
- `avg_score` — prosječan overall_score pogođenih
- `pct_affected` — postotak od ukupno
- `top_urls` — prvih 5 URL-ova (preview)

### GUI integration

`ResultsAdapter` pruža:
- `get_issue_filter_presets()` — dictionary {preset_name: flag_column}
- `filter_by_issue(issue_id)` — filter DataFrame po issue-u
- `get_issue_summary_stats()` — statistike za svaki issue

### Pravila

- **Jedan source-of-truth** — koristi flag kolone iz scorer-a
- **Ne praviti generički BI dashboard** — fokus na praktičan workflow
- **Priority ordering** — critical issues prvi (fetch error, non-200, not-product)

---

## 8e. Fix impact prioritization — šta prvo popraviti

Feature za prioritizaciju rada na osnovu očekivanog impact-a popravke.

### Razlika: Severity vs Impact

| Severity | Impact |
|----------|--------|
| Koliko je problem ozbiljan u audit logici | Koliko je korisno to prvo popraviti |
| CRITICAL/HIGH/MEDIUM/LOW | HIGH/MEDIUM/LOW |
| Koristi se za shortlist sortiranje | Koristi se za prioritizaciju popravki |

### Impact mapping

| Issue | Impact | Objašnjenje |
|-------|--------|-------------|
| fetch_error | HIGH | Stranica nije dostupna — kritično |
| non_200 | HIGH | Stranica ne radi — kritično |
| missing_price | HIGH | Kupci ne vide cijenu — gubitak prodaje |
| missing_schema | HIGH | AI agenti i Google teže razumiju |
| noindex | HIGH | Stranica nije u Google-u |
| canonical_mismatch | HIGH | SEO signal ide na drugu stranicu |
| not_product_page | MEDIUM | Zavisi od konteksta — možda namjerno |
| js_rendered | MEDIUM | Neki crawleri ne vide sadržaj |
| low_content | MEDIUM | Manje korisno za AI/kupce |

### Output

Impact je dostupan u:
- `manual_review_candidates.csv` — kolone `fix_impact`, `impact_score`
- GUI review details panel — `ReviewAdapter.get_fix_impact()`, `get_impact_color()`
- `audit/issue_grouping.py` — `calculate_fix_impact_score(issues)`

### Impact score

Za stranicu sa više issue-a, impact score se računa kao:
- **HIGH** ako ima barem jedan HIGH impact issue
- **MEDIUM** ako ima barem jedan MEDIUM impact issue (a nema HIGH)
- **LOW** ako ima samo LOW impact issue

### Pravila

- **Deterministički mapping** — isti issue → isti impact
- **Ne miješati sa severity** — severity je za shortlist, impact je za prioritizaciju popravki
- **Jasan source-of-truth** — `ISSUE_DEFINITIONS` u `audit/issue_grouping.py`

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
