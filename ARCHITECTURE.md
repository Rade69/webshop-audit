# WebshopAudit — Architecture Overview

> Radna arhitektonska mapa za razvoj. Nije marketinški dokument — opisuje stvarno stanje koda.

---

## 1. Svrha projekta

WebshopAudit je CLI/GUI alat koji skenira web shopove i ocjenjuje kvalitetu produktnih stranica za:
- **SEO** (indexability, canonical, structured data)
- **Machine-readability** (schema.org, SKU, GTIN, brand)
- **Commerce clarity** (cijena, slike, dostava, povrat, opis)
- **AI-agent readiness** (binary signal: da li agent može pouzdano preporučiti proizvod)

**Glavni outputi:**
- `products_raw.csv` — sirovi ekstraktovani podaci
- `products_scored.csv` — scored podaci sa flag kolonama
- `manual_review_candidates.csv` — shortlist za ručni review
- `best_products_sample.csv` — uzorak najboljih stranica za benchmark
- `category_summary.csv` — agregacija po kategorijama (ako ima breadcrumbs)
- `errors.csv` — neuspjeli fetch/extract
- `run_summary.json` — agregatna statistika runa
- `audit_report.docx` — Word report sa LLM-generisanim narativom

---

## 2. Glavni tok podataka

```
Input (sitemap / domain / URL file / pre-loaded URLs)
  │
  ▼
┌─────────────────────────────────────────────────┐
│  audit/pipeline.py  —  run_audit()              │
│  (shared orchestration — CLI i GUI koriste ovo) │
└─────────────────────────────────────────────────┘
  │
  ├── Step 1: URL collection (sitemap autodiscover / file / pre-loaded)
  │
  ├── Step 2: Fetch pages  (audit/fetcher.py)
  │       └── concurrent threads, checkpoint/resume, stop_event
  │
  ├── Step 3: Extract data  (audit/extractor.py)
  │       └── HTML parsing + schema parsing → ProductAuditRow (57 fields)
  │
  ├── Step 4: Export raw CSV  (products_raw.csv)
  │
  ├── Step 5: Score  (audit/scorer.py)
  │       └── catalog_score, machine_score, commerce_score,
  │           overall_score, flag columns, agent_ready
  │
  ├── Step 6: Export scored CSV  (products_scored.csv)
  │
  ├── Step 7: Shortlist  (audit/shortlist.py)
  │       ├── manual_review_candidates.csv  (severity-based)
  │       └── best_products_sample.csv      (top-scoring)
  │
  ├── Step 8: Category summary  (audit/scorer.py)
  │       └── category_summary.csv  (samo ako ima breadcrumbs)
  │
  ├── Step 9: Errors  (errors.csv)
  │
  ├── Step 10: Run summary  (run_summary.json)
  │
  └── Step 11: Run-to-run diff (optional) — `run_diff_summary.json`, `run_diff_urls.csv`, `run_diff_categories.csv`
```

---

## 3. Source-of-truth moduli

| Šta | Gdje | Napomena |
|-----|------|----------|
| **Data contract** (ekstraktovana polja) | `audit/extractor.py` → `ProductAuditRow` dataclass | 57 polja — ovo je canonical schema |
| **Scoring logika** | `audit/scorer.py` | 3 dimenzije + overall + flag kolone |
| **Shortlist / review kandidati** | `audit/shortlist.py` | Severity + sample bucket tuning + explanation + evidence |
| **Category inference** | `audit/scorer.py` → `summarize_by_category()` | Hijerarhijski: breadcrumb → URL → title → "Unknown" |
| **Report generator** | `audit/report_generator.py` | DOCX iz postojećih CSV/JSON fajlova |
| **Run diff** | `audit/run_diff.py` | Poređenje dva run-a, URL matching, score delta, issue detection |
| **Explainability** | `audit/explainability.py` | Human-readable objašnjenja za reason code-ove |
| **Evidence snapshots** | `audit/evidence.py` | Dokazni paket za audit nalaze |
| **Shared orchestration** | `audit/pipeline.py` → `run_audit()` | Jedini entry point za CLI i GUI |
| **Centralni config** | `config.py` | Svi tunable defaulti i pragovi |
| **GUI adapteri** | `gui/adapters/results_adapter.py`, `gui/adapters/review_adapter.py` | Izoliraju GUI od data model promjena |
| **GUI state** | `gui/viewmodels/run_state.py`, `results_state.py`, `review_state.py` | Plain dataclasses — bez logike |

---

## 4. Podjela odgovornosti po slojevima

### Domain sloj (`audit/`)
- **fetcher.py** — HTTP fetch, retries, Playwright fallback, checkpoint
- **extractor.py** — HTML/schema parsing → `ProductAuditRow` (data contract)
- **scorer.py** — scoring, flag detekcija, category inference, summaries
- **shortlist.py** — severity-based shortlist, sample bucket tuning, explanation + evidence generation
- **sitemap.py** — sitemap discovery, URL collection, product-like filtering
- **exporters.py** — CSV/JSON export helperi (+ diff export functions)
- **report_generator.py** — DOCX report iz output fajlova
- **run_diff.py** — run-to-run comparison, URL matching, score delta, issue detection
- **explainability.py** — human-readable objašnjenja za audit nalaze
- **evidence.py** — evidence snapshots za dokazni paket
- **pipeline.py** — `run_audit()` — shared orchestration (+ optional diff step)

### Entry pointovi
- **main.py** — CLI entry point (argparse → `run_audit()`)
- **gui/** — PyQt6 aplikacija

### GUI sloj (`gui/`)
- **controllers/** — `AuditRunController` (upravlja workerima, emituje signale)
- **adapters/** — `ResultsAdapter`, `ReviewAdapter` (formatiranje, filtering, column mapping)
- **tabs/** — `InputTab`, `RunTab`, `ResultsTab`, `ReviewQueueTab` (UI samo — bez business logike)
- **viewmodels/** — `RunState`, `ResultsState`, `ReviewState` (plain dataclasses)
- **app.py** — glavna aplikacija, tab management
- **theme.py** — dark/light teme, stilovi

### Pravilo
> GUI tabovi **nikad** ne računavaju business logiku. Sve ide kroz adaptere.
> GUI controlleri **nikad** ne dupliciraju pipeline logiku — koriste `run_audit()`.

---

## 5. Pravila za buduće izmjene

1. **Ne uvoditi nove alias kolone** — koristi canonical imena iz `ProductAuditRow`. Ako treba mapping, dodaj u `ResultsAdapter._create_column_mapping()`.
2. **Ne računati business logiku u tabovima** — filtering, scoring, shortlist pripadaju domain sloju.
3. **Ne raditi report-only hackove** — ako report pokazuje pogrešno, problem je u scorer-u ili shortlist-u, ne u report generatoru.
4. **Ne uvoditi paralelni CLI/GUI tok** — oba koriste `run_audit()`. Ako treba nova opcija, dodaj u config dict.
5. **Ne dodavati sample bucket logiku u GUI** — sample bucket je domain logika u `shortlist.py`.
6. **Ne mijenjati severity/reason codes bez adapter update-a** — `ReviewAdapter` mapira codes u Serbian.
7. **Ne dirati score weights bez testa** — weights su u `config.py`, scorer ih auto-normalizuje.
8. **Category summary je optional** — kreira se samo ako ima breadcrumb signala. Ne očekuj ga uvijek.
9. **Diff je opciona faza** — pokreće se samo ako je `compare_with_previous` postavljen u config-u.
10. **Diff URL matching koristi normalizaciju** — bez tracking parametara, www, http/https razlika.

---

## 6. Poznati preostali tehnički dugovi

### Category inference
- Baziran na keyword listama (~100+ termina po kategoriji) u `scorer.py`
- Radi dobro za modne web shopove (glavni use case), ali nije univerzalan
- Fallback na "Unknown" kada nema breadcrumbs signala
- Nije konfigurabilan izvana — liste su hardcoded u `summarize_by_category()`

### DOCX report
- LLM pozivi (Gemini Flash → DeepSeek fallback) — mogu failati bez mreže
- Placeholder tekst kada LLM nije dostupan
- Formatting edge case-ovi za tabele sa puno kolona
- `category_summary.csv` se ne uključuje u report ako ne postoji

### GUI
- Nema automatizovanih GUI testova (samo unit testovi za viewmodele i adaptere)
- QSettings čuvaju user preference — može doći do drift-a ako se defaulti promijene
- `ResultsAdapter.filter_data()` očekuje boolean kolone, ali CSV eksport daje 0/1 — adapter mora konvertovati

### Fetch layer
- Playwright mode nije thread-safe — forsira sequential fetch
- Checkpoint/resume radi samo unutar istog output direktorija
- Nema rate-limiting osim `delay` parametra

### Ostalo
- `ProductAuditRow` ima 57 polja — velika dataclass, ali nema boljeg načina za ovakav scope
- Nema YAML/JSON config fajla — sve je u `config.py` (dovoljno za ovaj projekat)

---

## 7. Preporučeni redoslijed za budući razvoj

### Bezbedno za proširenje
1. **Novi score sub-metrics** — dodati u postojeće score funkcije u `scorer.py`
2. **Novi URL patterns** — dodati u `config.py` → `PRODUCT_URL_PATTERNS` / `PRODUCT_URL_EXCLUSIONS`
3. **Novi LLM provideri** — dodati u `report_generator.py` → `call_llm()`
4. **Novi GUI adapter mappings** — dodati u `ResultsAdapter._create_column_mapping()`
5. **Novi severity reasons** — dodati u `ShortlistCandidate._calculate_reasons()` + update `ReviewAdapter.REASON_MAP`

### Prvo provjeriti prije većih izmjena
1. **Data contract promjene** — provjeriti da li svi downstream moduli (scorer, shortlist, exporters, adapteri, report) rade sa novim poljima
2. **Score weight promjene** — pokrenuti `tests/test_scorer.py` i `tests/test_config_defaults.py`
3. **Shortlist promjene** — pokrenuti `tests/test_shortlist.py` i `tests/test_e2e_integration.py`
4. **Config promjene** — pokrenuti `tests/test_config_defaults.py`

### Osjetljive tačke
- `ProductAuditRow` dataclass — promjena polja zahtijeva propagaciju kroz scorer, shortlist, adaptere, report
- `run_audit()` return dict — GUI i CLI zavise od ključeva
- `ResultsAdapter` column mapping — GUI zavisi od ovoga za sva polja
- `ReviewAdapter` reason/severity maps — GUI review tab zavisi od ovoga
- `run_diff.compare_runs()` — zavisi od canonical score/flag kolona, ne smije break-ovati sa novim run-ovima

---

## 8. Šta ne dirati napamet

- ❌ **Canonical kolone** — ne mijenjati imena bez pune propagacije kroz scorer, shortlist, adaptere, report
- ❌ **`run_audit()` return keys** — GUI i CLI zavise od `output_dir`, `total_urls`, `processed`, `errors`, `candidates`
- ❌ **Score weights u scoreru** — ako mijenjaš, radi to u `config.py`, ne hardcoded u funkcijama
- ❌ **Sample bucket logiku** — ne dodavati u GUI, ne mijenjati limite bez testova
- ❌ **Category summary u reportu** — ako fali, problem je u breadcrumb extraction, ne u reportu
- ❌ **`ProductAuditRow` polja** — dodavanje je OK, brisanje/renaming zahtijeva full audit
- ❌ **Diff URL matching** — ne mijenjati normalizaciju bez testa za tracking parametre i www handling

---

## 9. Test coverage

| Test fajl | Šta štiti |
|-----------|-----------|
| `test_extractor.py` | Row extraction iz fetch rezultata |
| `test_scorer.py` | Scoring funkcije, flag detekcija |
| `test_shortlist.py` | Shortlist selekcija, sample bucket limiti |
| `test_pipeline_integration.py` | Pipeline koraci, exporter roundtrip |
| `test_e2e_integration.py` | End-to-end run, output fajlovi, adapteri, data contract |
| `test_config_defaults.py` | Config vrijednosti, CLI/GUI konzistentnost, pipeline fallback |
| `test_parser.py`, `test_schema_parser.py` | HTML i JSON-LD parsing |
| `test_sitemap.py` | Sitemap discovery, URL filtering |
| `test_utils.py` | URL normalizacija, noindex detekcija, description quality |
| `test_gui_*.py` | GUI viewmodeli, adapteri, controlleri, tabovi |
| `test_run_diff.py` | Run-to-run diff logic, URL matching, score delta, issue detection |
| `test_explainability.py` | Explanation generation, priority ordering, sample detection |
| `test_evidence.py` | Evidence snapshots, finding-specific evidence, display formatting |

> **255 testova** (non-GUI) — svi prolaze. GUI testovi postoje ali se ignoriraju u CI zbog headless okruženja.
