#!/usr/bin/env python3
"""
webshop_audit — main entry point.

Usage examples:
  python main.py --sitemap https://example.com/sitemap.xml --max-urls 300
  python main.py --domain https://example.com --max-urls 300
  python main.py --urls-file inputs/urls.txt --delay 0.5
"""

import argparse
import os
import sys
import time
from datetime import datetime

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

from audit import extractor, fetcher, shortlist
from audit.exporters import export_dataframe_csv, export_errors, export_json_summary
from audit.scorer import build_scored_dataframe, summarize_by_category, summarize_sitewide_scores
from audit.sitemap import (
    collect_urls_from_sitemap,
    discover_sitemap_urls,
    fetch_sitemap,
    filter_product_like_urls,
)
from config import DEFAULT_DELAY, DEFAULT_OUTPUT_DIR


# ---------------------------------------------------------------------------
# URL collection helpers
# ---------------------------------------------------------------------------

def collect_urls_from_sitemap_source(args: argparse.Namespace) -> list[str]:
    sitemap_url = args.sitemap

    if not sitemap_url and args.domain:
        print(f"[sitemap] Discovering sitemap for: {args.domain}")
        candidates = discover_sitemap_urls(args.domain)
        sitemap_url = None
        for candidate in candidates:
            print(f"[sitemap] Trying: {candidate}")
            xml = fetch_sitemap(candidate)
            if xml:
                sitemap_url = candidate
                print(f"[sitemap] Found: {sitemap_url}")
                break
        if not sitemap_url:
            print("[sitemap] ERROR: Could not find a sitemap. Try --sitemap <url> directly.")
            sys.exit(1)

    print(f"[sitemap] Collecting URLs from: {sitemap_url}")
    urls = collect_urls_from_sitemap(sitemap_url, max_urls=args.max_urls)
    print(f"[sitemap] Total URLs in sitemap (deduplicated): {len(urls)}")

    filtered, used_fallback = filter_product_like_urls(urls)

    if used_fallback:
        print(
            f"[sitemap] WARNING: No product URL patterns matched — "
            f"returning ALL {len(filtered)} URLs (includes categories, blog, etc.).\n"
            f"[sitemap] Consider using --urls-file with a manual product URL list instead."
        )
    elif len(filtered) < len(urls):
        print(f"[sitemap] After product filter: {len(filtered)} URLs")
    else:
        print(f"[sitemap] Product filter kept all {len(filtered)} URLs")

    if args.max_urls:
        filtered = filtered[: args.max_urls]
        print(f"[sitemap] Capped to --max-urls: {len(filtered)}")

    return filtered


def collect_urls_from_file(path: str) -> list[str]:
    if not os.path.isfile(path):
        print(f"[urls-file] ERROR: File not found: {path}")
        sys.exit(1)

    urls = []
    seen = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Plain URL line
            if line.lower().startswith("http"):
                if line not in seen:
                    seen.add(line)
                    urls.append(line)
            elif "," in line:
                # Simple CSV: take first column (use split with maxsplit=1 for safety)
                first = line.split(",", 1)[0].strip().strip('"')
                if first.lower().startswith("http") and first not in seen:
                    seen.add(first)
                    urls.append(first)

    print(f"[urls-file] Loaded {len(urls)} URLs from {path} (deduplicated)")
    return urls


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="WebshopAudit — initial product audit tool",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--sitemap", metavar="URL", help="Direct URL to sitemap.xml")
    source.add_argument("--domain", metavar="URL", help="Shop domain — sitemap will be auto-discovered")
    source.add_argument("--urls-file", metavar="FILE", help="Path to .txt or .csv file with product URLs")

    parser.add_argument("--max-urls", type=int, default=None, help="Maximum number of URLs to process")
    parser.add_argument(
        "--delay", type=float, default=DEFAULT_DELAY,
        help=f"Delay between requests in seconds (default: {DEFAULT_DELAY})"
    )
    parser.add_argument(
        "--output-dir", default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})"
    )

    return parser.parse_args()





def main():
    args = parse_args()
    run_start = time.monotonic()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(args.output_dir, timestamp)
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  WebshopAudit — run started at {timestamp}")
    print(f"  Output dir: {output_dir}")
    print(f"{'='*60}\n")

    # --- Step 1: Collect URLs ---
    if args.urls_file:
        urls = collect_urls_from_file(args.urls_file)
        if args.max_urls:
            urls = urls[: args.max_urls]
    else:
        urls = collect_urls_from_sitemap_source(args)

    if not urls:
        print("ERROR: No URLs to process. Exiting.")
        sys.exit(1)

    total_urls = len(urls)
    print(f"\n[run] Processing {total_urls} URLs...\n")

    # --- Step 2: Fetch pages ---
    fetch_results = []
    if HAS_TQDM:
        for url in tqdm(urls, desc="Fetching", unit="page"):
            fetch_results.append(fetcher.fetch_page(url))
            if args.delay > 0:
                time.sleep(args.delay)
    else:
        print("[info] tqdm not installed — fetching without progress bar")
        fetch_results = fetcher.fetch_pages(urls, delay_seconds=args.delay)

    # --- Step 3: Separate errors ---
    errors = [
        {"url": r["url"], "error": r["error"], "status_code": r["status_code"]}
        for r in fetch_results
        if r["error"] or not r["html"]
    ]
    successful_fetches = [r for r in fetch_results if r["html"]]

    print(f"\n[run] Fetched: {len(successful_fetches)} OK, {len(errors)} errors")

    # --- Step 4: Parse and extract ---
    print("[run] Extracting data from pages...")
    rows = []
    for fetch_result in successful_fetches:
        try:
            row = extractor.build_product_audit_row(fetch_result)
            rows.append(row)
        except Exception as e:
            errors.append({
                "url": fetch_result.get("url", ""),
                "error": f"ExtractionError: {e}",
                "status_code": fetch_result.get("status_code"),
            })

    if not rows:
        print("ERROR: No pages could be parsed. Check errors.csv.")
        export_errors(errors, os.path.join(output_dir, "errors.csv"))
        sys.exit(1)

    # --- Step 5: Build raw DataFrame ---
    df_raw = extractor.rows_to_dataframe(rows)
    export_dataframe_csv(df_raw, os.path.join(output_dir, "products_raw.csv"))
    print(f"[export] products_raw.csv — {len(df_raw)} rows")

    # --- Step 6: Score ---
    print("[run] Scoring products...")
    df_scored = build_scored_dataframe(df_raw)
    export_dataframe_csv(df_scored, os.path.join(output_dir, "products_scored.csv"))
    print(f"[export] products_scored.csv — {len(df_scored)} rows")

    # --- Step 7: Non-product pages ---
    non_product = df_scored[~df_scored["is_likely_product_page"].astype(bool)]
    if not non_product.empty:
        export_dataframe_csv(non_product, os.path.join(output_dir, "non_product_pages.csv"))
        print(f"[export] non_product_pages.csv — {len(non_product)} rows")

    # --- Step 8: Shortlist ---
    candidates = shortlist.select_manual_review_candidates(df_scored)
    export_dataframe_csv(candidates, os.path.join(output_dir, "manual_review_candidates.csv"))
    print(f"[export] manual_review_candidates.csv — {len(candidates)} rows")

    best_sample = shortlist.select_best_products_sample(df_scored)
    export_dataframe_csv(best_sample, os.path.join(output_dir, "best_products_sample.csv"))
    print(f"[export] best_products_sample.csv — {len(best_sample)} rows")

    # --- Step 9: Category summary ---
    cat_summary = summarize_by_category(df_scored)
    if cat_summary is not None and not cat_summary.empty:
        export_dataframe_csv(cat_summary, os.path.join(output_dir, "category_summary.csv"))
        print(f"[export] category_summary.csv — {len(cat_summary)} categories")

    # --- Step 9: Errors ---
    export_errors(errors, os.path.join(output_dir, "errors.csv"))
    print(f"[export] errors.csv — {len(errors)} errors")

    # --- Step 10: Run summary ---
    elapsed = round(time.monotonic() - run_start, 1)
    sitewide = summarize_sitewide_scores(df_scored)

    run_summary = {
        "timestamp": timestamp,
        "total_urls": total_urls,
        "successfully_fetched": len(successful_fetches),
        "successfully_parsed": len(rows),
        "errors": len(errors),
        "pages_with_schema_product": int(df_scored["schema_product_present"].sum()),
        "pages_without_price": int(df_scored["suspicious_price_missing"].sum()),
        "pages_with_low_content": int(df_scored["suspicious_low_content"].sum()),
        "pages_with_indexability_flags": int((df_scored["indexability_flags"].str.len() > 0).sum()),
        "manual_review_candidates": len(candidates),
        "non_product_pages": int((~df_scored["is_likely_product_page"].astype(bool)).sum()),
        "elapsed_seconds": elapsed,
        **sitewide,
    }

    export_json_summary(run_summary, os.path.join(output_dir, "run_summary.json"))

    # --- Terminal summary ---
    print(f"\n{'='*60}")
    print("  AUDIT COMPLETE")
    print(f"{'='*60}")
    print(f"  URLs processed       : {total_urls}")
    print(f"  Successfully parsed  : {len(rows)}")
    print(f"  Errors               : {len(errors)}")
    print(f"  With Product schema  : {run_summary['pages_with_schema_product']}")
    print(f"  Missing price        : {run_summary['pages_without_price']}")
    print(f"  Low content pages    : {run_summary['pages_with_low_content']}")
    print(f"  Indexability flags   : {run_summary['pages_with_indexability_flags']}")
    if "avg_overall_score" in sitewide:
        print(f"  Avg overall score    : {sitewide['avg_overall_score']}")
    print(f"  Review candidates    : {len(candidates)}")
    print(f"  Elapsed              : {elapsed}s")
    print(f"\n  Outputs saved to: {output_dir}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
