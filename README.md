# WebshopAudit

Initial product audit tool — static HTML scraping, structured data parsing, rule-based scoring, and manual review shortlist.

---

## Installation

```bash
pip install -r requirements.txt
```

Python 3.11+ recommended.

---

## Usage

### From sitemap URL

```bash
python main.py --sitemap https://example.com/sitemap.xml --max-urls 300
```

### From domain (auto-discovers sitemap)

```bash
python main.py --domain https://example.com --max-urls 300
```

### From a URL list file

```bash
python main.py --urls-file inputs/urls.txt --delay 0.5
```

### All options

| Argument | Default | Description |
|---|---|---|
| `--sitemap URL` | — | Direct URL to sitemap.xml |
| `--domain URL` | — | Domain — sitemap auto-discovered via robots.txt and common paths |
| `--urls-file FILE` | — | .txt or .csv file with product URLs (one per line) |
| `--max-urls N` | unlimited | Cap the number of URLs to process |
| `--delay SECONDS` | 0.5 | Pause between HTTP requests |
| `--output-dir DIR` | outputs/ | Base output directory |

---

## Output files

Each run creates a timestamped subdirectory inside `outputs/`:

| File | Description |
|---|---|
| `products_raw.csv` | Raw extracted data per URL |
| `products_scored.csv` | Raw data + scoring columns |
| `manual_review_candidates.csv` | Products flagged for manual review |
| `best_products_sample.csv` | Top-scoring products (reference sample) |
| `category_summary.csv` | Aggregated scores by breadcrumb category (if available) |
| `errors.csv` | URLs that failed to fetch or parse |
| `run_summary.json` | Run metadata and aggregate statistics |

---

## Scoring model

This is an **agent-friendly webshop audit** tool. Scores measure how well an AI agent can identify, read, understand, and recommend a product.

Each product receives three independent scores (0–100):

| Score | Weight | What it measures |
|---|---|---|
| `catalog_score` | 30% | Can the agent identify and describe the product? (title, H1, meta, breadcrumb, price visible in HTML) |
| `machine_score` | 35% | Can the agent programmatically read the product? (Schema.org Product/Offer, SKU, GTIN, brand, canonical) |
| `commerce_score` | 35% | Can buyer and agent make a decision? (price visible, ≥2 product images, shipping signal, returns signal, description quality) |

**`overall_score`** = `catalog_score × 0.30 + machine_score × 0.35 + commerce_score × 0.35`

### Agent-ready flag

A special `agent_ready` binary flag indicates if a product is ready for AI recommendation:

```python
agent_ready = overall_score >= 65
            and not flag_js_rendered
            and not suspicious_price_missing
            and not suspicious_schema_missing
```

This combines:
- Sufficient overall quality (score ≥ 65)
- Not JS-rendered (data is reliable)
- Has a price (machine-readable or HTML)
- Has Schema.org Product (structured data)

---

## Known limitations (v1)

- **JS-rendered pages**: Fetches static HTML only. Products rendered entirely by JavaScript will appear empty. A future version can add Playwright/Selenium fetching as an optional mode.
- **Product variants**: Does not detect or compare variants (sizes, colors). Each URL is treated as a standalone page.
- **Price detection**: HTML price heuristic may miss prices in complex/dynamic layouts. Schema price is more reliable.
- **Availability**: Only reads structured data `availability` field — does not interpret "Out of stock" text in arbitrary HTML.
- **Not a replacement for manual audit**: This tool generates data signals and a prioritized shortlist. A human still needs to review the candidates.
- **Robots.txt / rate limiting**: The tool adds a configurable delay between requests but does not implement full crawl budget management. Respect the site's robots.txt.

---

## Architecture

```
webshop_audit/
├── main.py              # CLI entry point and orchestration
├── config.py            # All tunable constants
├── requirements.txt
│
├── inputs/              # Place URL list files here
├── outputs/             # Run outputs (timestamped subdirs)
│
└── audit/
    ├── sitemap.py       # Sitemap discovery, fetch, parse, URL filtering
    ├── fetcher.py       # HTTP requests with retry logic
    ├── parser.py        # HTML signal extraction (title, H1, price, images…)
    ├── schema_parser.py # JSON-LD / structured data parsing
    ├── extractor.py     # Combines parser + schema_parser into ProductAuditRow dataclass
    ├── scorer.py        # Rule-based scoring + flag detection + category summary
    ├── shortlist.py     # Selects manual review candidates and best sample
    ├── exporters.py     # CSV and JSON export helpers
    └── utils.py         # Small string/text utilities
```

### Why this module split?

- `sitemap` and `fetcher` are I/O only — easy to swap (e.g. add async fetching or Playwright).
- `parser` and `schema_parser` are pure HTML → data functions, fully testable without HTTP.
- `extractor` is the single assembly point — one function, one dataclass, one clear contract.
- `scorer` is isolated so scoring rules can be changed without touching extraction logic.
- `shortlist` and `exporters` are thin output layers.

### What comes next (logical next steps)

1. **Playwright mode** — optional `--js-render` flag for JS-heavy shops
2. **Feed comparison** — compare scraped data against a product feed (Google Merchant, CSV export)
3. **Platform adapters** — WooCommerce / Shopify / Magento often have consistent HTML patterns worth targeting specifically
4. **Screenshot capture** — Playwright screenshots of flagged products for visual review
5. **Async fetching** — `httpx` + `asyncio` for faster runs on large catalogs
