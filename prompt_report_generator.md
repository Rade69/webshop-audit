# Prompt — Audit Report Generator

## Preduslov

Pročitati SKILL.md za docx kreiranje prije početka implementacije:
`/mnt/skills/public/docx/SKILL.md`

---

## Zadatak

Implementiraj modul koji iz rezultata završenog audit run-a generiše
strukturiran Word (.docx) izvještaj.

Izvještaj je namijenjen tome da se direktno pošalje klijentu ili
koristi kao osnova za prezentaciju nalaza.

---

## Arhitektura

### Novi fajl: `audit/report_generator.py`

Centralni modul koji:
- čita output fajlove iz zadanog direktorija
- računa agregatne statistike
- poziva Claude Haiku API za narativne sekcije
- generiše .docx izvještaj

### CLI integracija u `main.py`

Dodaj argument:
```
--generate-report PATH
```

Primjer:
```bash
python main.py --generate-report outputs/20240330_143000/
```

### GUI integracija

U Results tabu dodaj dugme **Generate Report** pored postojećih
akcijskih dugmadi. Dugme je enabled samo kada su rezultati učitani.

---

## Data sources

Modul čita iz output direktorija:

| Fajl | Svrha |
|---|---|
| `run_summary.json` | Agregatne statistike, metadata runa |
| `products_scored.csv` | Sve scored stranice |
| `manual_review_candidates.csv` | Prioritizovani problemi |
| `category_summary.csv` | Breakdown po kategoriji (ako postoji) |
| `errors.csv` | Fetch/parse greške |

Ako neki fajl ne postoji, taj dio izvještaja se preskače bez greške.

---

## Struktura izvještaja

### Sekcija 1 — Naslovna strana

Automatski generisana iz podataka, bez LLM-a:

```
[Logo placeholder ili prazan prostor]

WEBSHOP AUDIT REPORT
Agent-Friendly Readiness Assessment

Shop: [domain iz run_summary.json]
Datum: [timestamp iz run_summary.json]
Ukupno stranica: [total_urls]
Uspješno obrađeno: [successfully_parsed]
```

---

### Sekcija 2 — Executive Summary

**LLM generisano (Haiku).**

Prompt koji šalješ modelu:

```
You are writing an executive summary for a webshop audit report.
Write 3-4 concise paragraphs in a professional tone.
Language: use the same language as the shop domain suggests
(if .ba/.hr/.rs domain — write in Bosnian/Croatian/Serbian Latin,
otherwise write in English).

Data about the shop:
- Domain: {domain}
- Total product pages scanned: {total_urls}
- Successfully parsed: {successfully_parsed}
- Average overall score: {avg_overall_score}/100
- Average catalog score: {avg_catalog_score}/100
- Average machine score: {avg_machine_score}/100
- Average commerce score: {avg_commerce_score}/100
- Pages with Product schema: {pages_with_schema_product} ({schema_pct}%)
- Pages missing price: {pages_without_price} ({price_missing_pct}%)
- Pages with low content: {pages_with_low_content} ({low_content_pct}%)
- Pages with indexability flags: {pages_with_indexability_flags}
- Manual review candidates: {manual_review_candidates}
- Errors during fetch: {errors}

Cover these points:
1. Overall impression of the shop's data quality
2. Most critical finding (the biggest single problem)
3. What this means for AI agent discoverability specifically
4. General direction for improvement

Be direct and specific. Avoid generic phrases.
Do not use bullet points — write in paragraphs.
Maximum 250 words.
```

---

### Sekcija 3 — Scorecard

**Automatski generisano iz podataka.**

Tabela sa 4 reda:

| Dimenzija | Prosječan score | Što mjeri |
|---|---|---|
| Catalog Score | XX/100 | HTML kompletnost |
| Machine Score | XX/100 | Schema i structured data |
| Commerce Score | XX/100 | Buyer signali |
| **Overall Score** | **XX/100** | Ukupno |

Vizuelno:
- Score >= 70: zelena boja ćelije (RGB: 230, 244, 239)
- Score 40-69: žuta boja ćelije (RGB: 253, 243, 227)
- Score < 40: crvena boja ćelije (RGB: 253, 234, 234)

Ispod tabele, kratki redovi sa ključnim metrikama:
- Stranica sa Product schema: X (Y%)
- Stranica bez cijene: X (Y%)
- Stranica sa malo sadržaja: X (Y%)
- Stranica sa indexability problemima: X
- Greške pri fetch-u: X

---

### Sekcija 4 — Ključni nalazi

**Automatski generisano iz podataka.**

4 subsekcije, svaka sa naslovom i kratkim tabelom nalaza:

#### 4.1 Schema i structured data

Tabela:
| Nalaz | Broj stranica | % od ukupno |
|---|---|---|
| Nema Product schema | X | Y% |
| Nema Offer schema | X | Y% |
| Nema cijene u schema | X | Y% |
| Nema availability | X | Y% |
| Nema SKU | X | Y% |
| Nema brand | X | Y% |

#### 4.2 HTML sadržaj i kompletnost

Tabela:
| Nalaz | Broj stranica | % od ukupno |
|---|---|---|
| Nema H1 | X | Y% |
| Nema meta description | X | Y% |
| Malo vidljivog teksta (<200 znakova) | X | Y% |
| Nema HTML price signala | X | Y% |
| Nema shipping signala | X | Y% |
| Nema returns signala | X | Y% |

#### 4.3 Indexability i tehnički problemi

Tabela:
| Nalaz | Broj stranica |
|---|---|
| Noindex stranice | X |
| Canonical mismatch | X |
| JS-rendered (nepouzdani podaci) | X |
| Fetch greške (4xx/5xx) | X |

#### 4.4 Kategorije (ako postoji category_summary.csv)

Tabela top 5 kategorija sa najnižim avg_overall_score:
| Kategorija | Broj proizvoda | Avg score | Bez schema | Bez cijene |
|---|---|---|---|---|
| ... | ... | ... | ...% | ...% |

Ako category_summary.csv ne postoji, ovu subsekiju preskači.

---

### Sekcija 5 — Quick Wins

**LLM generisano (Haiku).**

Prompt:

```
Based on this webshop audit data, identify the top 3 quick wins —
specific, actionable improvements that would have the highest impact
with the least effort.

Data:
- Pages missing Product schema: {no_schema_count} ({no_schema_pct}%)
- Pages missing price in schema: {no_price_count} ({no_price_pct}%)
- Pages missing H1: {no_h1_count}
- Pages missing meta description: {no_meta_count}
- Pages with low content: {low_content_count}
- Pages with canonical mismatch: {canonical_mismatch_count}
- Pages likely JS-rendered: {js_rendered_count}
- Platform hints from URL patterns: {platform_hint}

Write exactly 3 quick wins.
Format each as:
**[Short title]**
[2-3 sentences: what to fix, why it matters for AI agent discoverability,
expected impact]

Language: Bosnian/Croatian/Serbian Latin if .ba/.hr/.rs domain,
otherwise English.
```

---

### Sekcija 6 — 30/60/90 dana plan

**LLM generisano (Haiku).**

Prompt:

```
Create a practical 30/60/90 day improvement plan for this webshop
based on the audit findings.

Key findings:
- Biggest problem: {biggest_problem} (affects {biggest_problem_pct}% of pages)
- Second problem: {second_problem}
- Third problem: {third_problem}
- Overall score: {avg_overall_score}/100
- Machine readability score: {avg_machine_score}/100

Structure the plan as three phases:

**Prvih 30 dana — Kritični popravci**
[3-4 bullet points: things to fix immediately, highest impact]

**31-60 dana — Sistemski popravci**
[3-4 bullet points: structural improvements]

**61-90 dana — Optimizacija i provjera**
[3-4 bullet points: monitoring, testing, iterating]

Be specific and practical.
Language: Bosnian/Croatian/Serbian Latin if .ba/.hr/.rs domain,
otherwise English.
```

---

### Sekcija 7 — Prilog: Top 20 kandidata za pregled

**Automatski generisano iz `manual_review_candidates.csv`.**

Tabela prvih 20 redova:

| URL | Overall | Razlog | Flags |
|---|---|---|---|
| ... | ... | ... | ... |

URL trunkuj na 60 znakova ako je duži.
Razlog uzmi iz `missing_fields` i `indexability_flags` kolona —
prikaži human-readable verziju (npr. "Missing Schema, Missing Price").

---

## LLM pozivi — tehnička implementacija

### Model

Koristi `claude-haiku-4-5-20251001` — najjeftiniji model, dovoljan
za ovaj tip strukturiranog pisanja.

### API poziv

```python
import anthropic

def call_llm(prompt: str, max_tokens: int = 400) -> str:
    """Call Claude Haiku for narrative generation."""
    client = anthropic.Anthropic()  # čita ANTHROPIC_API_KEY iz env
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text
```

### Greška pri API pozivu

Ako API poziv ne uspije (nema API ključa, network greška, itd.):
- ne ruši generisanje dokumenta
- umjesto LLM teksta ubaci placeholder:
  `"[LLM generation failed — please add narrative manually]"`
- ispiši warning u terminal/log
- generiši dokument sa svim automatskim sekcijama

### Preporučeni redoslijed poziva

Sva tri LLM poziva radi sekvencijalno prije nego počneš graditi
dokument. Tako ako jedan padne, znaš to odmah.

---

## Output

Report se snima u isti output direktorij run-a:

```
outputs/20240330_143000/audit_report.docx
```

Naziv fajla: `audit_report.docx` (uvijek isti, overwrite ako postoji).

---

## Formatiranje dokumenta

### Font i opšti stil
- Font: Arial
- Default veličina: 12pt
- Boje headinga: tamno plava (#1F3864)
- Page size: A4

### Headinzi
- H1: 18pt, bold, plava (#1F3864), spacing before 240, after 120
- H2: 14pt, bold, plava (#1F3864), spacing before 180, after 90
- H3: 12pt, bold, tamno siva (#404040), spacing before 120, after 60

### Tabele
- Header red: pozadina (#1F3864), bijeli tekst, bold
- Data redovi: alternating bijela / (#F2F7FF)
- Border: tanki, siva (#CCCCCC)
- Cell padding: top/bottom 80, left/right 120

### Naslovna strana
- Page break na kraju
- Naziv firme/domena velik i centriran (24pt bold)
- Datum manji (12pt, siva)

### Scorecard tabela
- Score ćelije obojene prema vrijednosti (zelena/žuta/crvena)
- Score tekst bold, centriran

---

## Arhitekturna pravila

- `audit/report_generator.py` ne importuje ništa iz GUI sloja
- `audit/report_generator.py` je standalone — može se koristiti
  i bez GUI-a (iz CLI-a)
- LLM pozivi su izolovani u posebnoj funkciji `call_llm()`
- Sva računanja su u Pythonu, ne u LLM promoptima
- LLM dobiva samo agregatne brojeve, nikad raw CSV podatke
- Dokument se gradi koristeći `docx` npm paket prema SKILL.md uputstvima

## Novi fajlovi

```
audit/report_generator.py
```

## Izmjene postojećih fajlova

```
main.py                      — dodaj --generate-report argument
gui/tabs/results_tab.py      — dodaj Generate Report dugme
gui/controllers/results_controller.py  — dodaj generate_report() metodu
```

## Isporuka

- `audit/report_generator.py` sa svim sekcijama
- CLI `--generate-report` radi standalone
- GUI dugme Generate Report poziva kontroler koji poziva generator
- LLM greške ne ruše generisanje
- Dokument se snima u output direktorij run-a
- Terminal/log ispisuje putanju do generisanog fajla
