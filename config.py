DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (compatible; WebshopAuditBot/1.0; +https://github.com/your-org/webshop-audit)"
)

DEFAULT_TIMEOUT = 20
DEFAULT_DELAY = 0.5
DEFAULT_MAX_RETRIES = 3
DEFAULT_MAX_URLS = 50
DEFAULT_OUTPUT_DIR = "outputs"

# Concurrent fetching
DEFAULT_MAX_WORKERS = 8  # threads for parallel HTTP requests

# Playwright (JS rendering)
DEFAULT_USE_PLAYWRIGHT = False

# Score weights (must sum to 1.0; scorer normalises automatically)
DEFAULT_CATALOG_WEIGHT = 0.30
DEFAULT_MACHINE_WEIGHT = 0.35
DEFAULT_COMMERCE_WEIGHT = 0.35
DEFAULT_AGENT_READY_THRESHOLD = 65  # overall_score >= this for agent_ready=True

# Checkpoint / resume
CHECKPOINT_FILENAME = "fetch_checkpoint.json"

# Heuristic thresholds
MIN_VISIBLE_TEXT_LENGTH = 200
MIN_IMAGE_COUNT = 2

# Shortlist defaults
SHORTLIST_TOP_N = 50
BEST_SAMPLE_TOP_N = 20


# Product-like URL patterns (simple heuristics)
PRODUCT_URL_PATTERNS = [
    "/product",
    "/proizvod",
    "/p/",
    "/item",
    "/artik",       # artikal, artikli
    "/shop/",
    "/store/",
    "/catalog/",
    "/katalog/",
    "/dp/",         # Amazon style
    "/sku/",
    "/pd/",         # product detail
    "/goods/",
    "/detalj",      # detalji, detaljan
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
    "/pages/",      # Shopify static pages
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
