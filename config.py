DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (compatible; WebshopAuditBot/1.0; +https://github.com/your-org/webshop-audit)"
)

DEFAULT_TIMEOUT = 20
DEFAULT_DELAY = 0.5
DEFAULT_MAX_RETRIES = 3
DEFAULT_MAX_URLS = None
DEFAULT_OUTPUT_DIR = "outputs"

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
    "/artik",
    "/shop/",
    "/store/",
    "/catalog/",
    "/katalog/",
    "/dp/",       # Amazon style
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
]
