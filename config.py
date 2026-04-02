# =============================================================================
# WebshopAudit — Central Configuration
# =============================================================================
# Tunable defaults for the audit pipeline.
# All entry points (CLI, GUI, shared run_audit) read from here.
# =============================================================================

# --- HTTP / Fetch ---

DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; WebshopAuditBot/1.0; +https://github.com/your-org/webshop-audit)"

DEFAULT_TIMEOUT = 20  # seconds per request
DEFAULT_DELAY = 0.5  # seconds between fetch batches
DEFAULT_MAX_RETRIES = 3  # retries per URL (exponential backoff)
DEFAULT_MAX_WORKERS = 8  # parallel HTTP threads
DEFAULT_USE_PLAYWRIGHT = False  # JS rendering (forces sequential fetch)

# --- Run limits ---

DEFAULT_MAX_URLS = 50  # max URLs when no explicit limit is set
DEFAULT_OUTPUT_DIR = "outputs"

# --- Scoring ---
# Weights are auto-normalised in scorer.py (they don't need to sum to 1.0).

DEFAULT_CATALOG_WEIGHT = 0.30  # title, H1, meta, breadcrumb, price, text
DEFAULT_MACHINE_WEIGHT = 0.35  # schema.org, canonical, SKU, GTIN, brand
DEFAULT_COMMERCE_WEIGHT = 0.35  # price, images, shipping, returns, description
DEFAULT_AGENT_READY_THRESHOLD = (
    65  # overall_score >= this + no JS + has price + has schema
)

# --- Heuristic thresholds ---

MIN_VISIBLE_TEXT_LENGTH = 200  # characters for "enough content" signal
MIN_IMAGE_COUNT = 2  # minimum product images for commerce_score

# --- Shortlist ---
# See audit/shortlist.py for sample bucket tuning constants:
#   SAMPLE_MAX_ABSOLUTE, SAMPLE_MAX_RATIO_OF_ISSUES, SAMPLE_DISABLE_ABOVE_ISSUES

SHORTLIST_TOP_N = 50  # max manual review candidates
BEST_SAMPLE_TOP_N = 20  # max best products sample

# --- Checkpoint / resume ---

CHECKPOINT_FILENAME = "fetch_checkpoint.json"

# --- Pipeline phases (display names) ---
# Used by both run_tab.py and main_window.py — single source of truth.

PHASE_DISPLAY_NAMES = {
    "url_collection": "Prikupljanje URL-ova",
    "fetch": "Preuzimanje",
    "parse": "Parsiranje HTML-a",
    "score": "Bodovanje",
    "shortlist": "Kratka lista",
    "export": "Izvoz",
    "done": "Završeno",
}

# --- URL classification ---
# Used by sitemap.py filter_product_like_urls()

PRODUCT_URL_PATTERNS = [
    "/product",
    "/proizvod",
    "/p/",
    "/item",
    "/artik",  # artikal, artikli
    "/shop/",
    "/store/",
    "/catalog/",
    "/katalog/",
    "/dp/",  # Amazon style
    "/sku/",
    "/pd/",  # product detail
    "/goods/",
    "/detalj",  # detalji, detaljan
]

PRODUCT_URL_EXCLUSIONS = [
    "/category",
    "/kategorija",
    "/tag",
    "/blog",
    "/news",
    "/vijesti",
    "/cart",
    "/checkout",
    "/account",
    "/login",
    "/register",
    "/search",
    "/page/",
    "/pages/",  # Shopify static pages
    "/collections",  # Shopify category listing
    "/policies/",
    "/contact",
    "/about",
    "/o-nama",
    "/dostava",
    "/povrat",
    "/wishlist",
    "/compare",
]
