"""
Wrapper za audit pipeline.

Odgovornost: Omogućiti pokretanje audit pipeline-a sa callback-ovima
za progress i log poruke. Koristi se i iz CLI-ja i iz GUI-a.
"""
import json
import os
import time
from datetime import datetime
from typing import Callable, Optional

from audit import extractor, fetcher, shortlist
from audit.exporters import export_dataframe_csv, export_errors, export_json_summary
from audit.scorer import build_scored_dataframe, summarize_by_category, summarize_sitewide_scores
from audit.sitemap import (
    collect_urls_from_sitemap,
    discover_sitemap_urls,
    fetch_sitemap,
    filter_product_like_urls,
)
from config import (
    DEFAULT_DELAY,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_MAX_WORKERS,
    DEFAULT_USE_PLAYWRIGHT,
    DEFAULT_CATALOG_WEIGHT,
    DEFAULT_MACHINE_WEIGHT,
    DEFAULT_COMMERCE_WEIGHT,
    DEFAULT_AGENT_READY_THRESHOLD,
    CHECKPOINT_FILENAME,
)


def run_audit(
    config: dict,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    log_callback: Optional[Callable[[str, str], None]] = None
) -> dict:
    """
    Pokreće cijeli audit pipeline.

    Args:
        config: Rječnik sa konfiguracijom. Očekuje:
            - input_file (str): putanja do fajla sa URL-ovima
            - domain (str): domen za autodiscover sitemap-a
            - sitemap_url (str): direktan URL sitemap-a
            - output_dir (str): izlazni direktorijum
            - max_urls (int): maksimalan broj URL-ova
            - delay (float): kašnjenje između zahtjeva
        
        progress_callback: Funkcija za reportiranje progressa.
            Signature: (processed: int, total: int, phase: str)
        
        log_callback: Funkcija za log poruke.
            Signature: (level: str, message: str)
            level: "info" | "warning" | "error"

    Returns:
        Rječnik sa rezultatima:
            - output_dir: putanja do izlaznog direktorijuma
            - total_urls: ukupan broj URL-ova
            - processed: broj obrađenih
            - errors: broj grešaka
            - candidates: broj kandidata
    """
    def log(level: str, message: str):
        if log_callback:
            log_callback(level, message)
        else:
            print(f"[{level.upper()}] {message}")

    def report_progress(processed: int, total: int, phase: str = ""):
        if progress_callback:
            progress_callback(processed, total, phase)

    # Ekstraktuj konfiguraciju
    input_file = config.get("input_file")
    domain = config.get("domain")
    sitemap_url = config.get("sitemap_url")
    output_dir = config.get("output_dir")
    max_urls = config.get("max_urls")
    delay = config.get("delay", DEFAULT_DELAY)
    max_workers = config.get("max_workers", DEFAULT_MAX_WORKERS)
    use_playwright = config.get("use_playwright", DEFAULT_USE_PLAYWRIGHT)
    catalog_weight = config.get("catalog_weight", DEFAULT_CATALOG_WEIGHT)
    machine_weight = config.get("machine_weight", DEFAULT_MACHINE_WEIGHT)
    commerce_weight = config.get("commerce_weight", DEFAULT_COMMERCE_WEIGHT)
    agent_ready_threshold = config.get("agent_ready_threshold", DEFAULT_AGENT_READY_THRESHOLD)
    resume_from = config.get("resume_from", "")  # path to previous output_dir

    run_start = time.time()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if not output_dir:
        output_dir = os.path.join(DEFAULT_OUTPUT_DIR, timestamp)
    os.makedirs(output_dir, exist_ok=True)

    log("info", f"Audit run started: {timestamp}")
    log("info", f"Output dir: {output_dir}")

    # --- Step 1: Collect URLs ---
    if input_file and os.path.isfile(input_file):
        log("info", f"Loading URLs from file: {input_file}")
        urls = _collect_urls_from_file(input_file)
        if max_urls:
            urls = urls[:max_urls]
    elif domain:
        log("info", f"Discovering sitemap for domain: {domain}")
        sitemap_url = _discover_sitemap(domain, log_callback)
        if not sitemap_url:
            raise RuntimeError("Could not find sitemap")
        urls = collect_urls_from_sitemap(sitemap_url, max_urls=max_urls)
    elif sitemap_url:
        urls = collect_urls_from_sitemap(sitemap_url, max_urls=max_urls)
    else:
        raise ValueError("Must provide input_file, domain, or sitemap_url")

    if not urls:
        raise ValueError("No URLs to process")

    total_urls = len(urls)
    log("info", f"Collected {total_urls} URLs")
    report_progress(0, total_urls, "url_collection")

    # --- Step 2: Fetch pages (with optional resume from checkpoint) ---
    checkpoint_path = os.path.join(output_dir, CHECKPOINT_FILENAME)
    fetch_results: list[dict] = []

    if resume_from:
        prev_checkpoint = os.path.join(resume_from, CHECKPOINT_FILENAME)
        if os.path.isfile(prev_checkpoint):
            log("info", f"Resuming from checkpoint: {prev_checkpoint}")
            with open(prev_checkpoint, encoding="utf-8") as f:
                fetch_results = json.load(f)
            log("info", f"Loaded {len(fetch_results)} cached pages from checkpoint")
        else:
            log("warning", f"Checkpoint not found at {prev_checkpoint}, fetching fresh")

    if not fetch_results:
        report_progress(0, total_urls, "fetch")
        mode = "Playwright" if use_playwright else f"{max_workers} workers"
        log("info", f"Fetching {total_urls} pages ({mode}, delay={delay}s)...")

        def _fetch_progress(done: int, total: int) -> None:
            report_progress(done, total, "fetch")

        fetch_results = fetcher.fetch_pages(
            urls,
            delay_seconds=delay,
            max_workers=max_workers,
            use_playwright=use_playwright,
            progress_callback=_fetch_progress,
        )

        # Persist checkpoint so this run can be resumed if it's interrupted later
        try:
            with open(checkpoint_path, "w", encoding="utf-8") as f:
                json.dump(fetch_results, f)
            log("info", "Checkpoint saved")
        except OSError as e:
            log("warning", f"Could not save checkpoint: {e}")

    # Izdvoji greške
    errors = [
        {"url": r["url"], "error": r["error"], "status_code": r.get("status_code")}
        for r in fetch_results
        if r["error"] or not r["html"]
    ]
    successful_fetches = [r for r in fetch_results if r["html"]]

    log("info", f"Fetched: {len(successful_fetches)} OK, {len(errors)} errors")
    report_progress(len(successful_fetches), total_urls, "parse")

    # --- Step 3: Parse and extract ---
    log("info", "Extracting data from pages...")
    rows = []
    for i, fetch_result in enumerate(successful_fetches):
        try:
            row = extractor.build_product_audit_row(fetch_result)
            rows.append(row)
        except Exception as e:
            errors.append({
                "url": fetch_result.get("url", ""),
                "error": f"ExtractionError: {e}",
                "status_code": fetch_result.get("status_code"),
            })
        # Progress update svakih 10 stranica
        if (i + 1) % 10 == 0:
            report_progress(i + 1, len(successful_fetches), "parse")

    if not rows:
        log("warning", "No pages could be parsed")
        export_errors(errors, os.path.join(output_dir, "errors.csv"))
        return {
            "output_dir": output_dir,
            "total_urls": total_urls,
            "processed": 0,
            "errors": len(errors),
            "candidates": 0
        }

    report_progress(len(rows), total_urls, "score")
    
    # --- Step 4: Build raw DataFrame ---
    df_raw = extractor.rows_to_dataframe(rows)
    export_dataframe_csv(df_raw, os.path.join(output_dir, "products_raw.csv"))
    log("info", f"Exported products_raw.csv — {len(df_raw)} rows")

    # --- Step 5: Score ---
    log("info", "Scoring products...")
    df_scored = build_scored_dataframe(
        df_raw,
        catalog_weight=catalog_weight,
        machine_weight=machine_weight,
        commerce_weight=commerce_weight,
        agent_ready_threshold=agent_ready_threshold,
    )
    export_dataframe_csv(df_scored, os.path.join(output_dir, "products_scored.csv"))
    log("info", f"Exported products_scored.csv — {len(df_scored)} rows")

    # --- Step 6: Non-product pages ---
    non_product = df_scored[~df_scored["is_likely_product_page"].astype(bool)]
    if not non_product.empty:
        export_dataframe_csv(non_product, os.path.join(output_dir, "non_product_pages.csv"))
        log("info", f"Exported non_product_pages.csv — {len(non_product)} rows")

    # --- Step 7: Shortlist ---
    report_progress(len(rows), total_urls, "shortlist")
    log("info", "Creating shortlist...")
    
    candidates = shortlist.select_manual_review_candidates(df_scored)
    export_dataframe_csv(candidates, os.path.join(output_dir, "manual_review_candidates.csv"))
    log("info", f"Exported manual_review_candidates.csv — {len(candidates)} rows")

    best_sample = shortlist.select_best_products_sample(df_scored)
    export_dataframe_csv(best_sample, os.path.join(output_dir, "best_products_sample.csv"))
    log("info", f"Exported best_products_sample.csv — {len(best_sample)} rows")

    # --- Step 8: Category summary ---
    cat_summary = summarize_by_category(df_scored)
    if cat_summary is not None and not cat_summary.empty:
        export_dataframe_csv(cat_summary, os.path.join(output_dir, "category_summary.csv"))
        log("info", f"Exported category_summary.csv — {len(cat_summary)} categories")

    # --- Step 9: Errors ---
    export_errors(errors, os.path.join(output_dir, "errors.csv"))
    log("info", f"Exported errors.csv — {len(errors)} errors")

    # --- Step 10: Run summary ---
    elapsed = round(time.time() - run_start, 1)
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
        "stopped_early": config.get("stopped_early", False),
        **sitewide,
    }

    export_json_summary(run_summary, os.path.join(output_dir, "run_summary.json"))
    log("info", f"Run completed in {elapsed}s")

    return {
        "output_dir": output_dir,
        "total_urls": total_urls,
        "processed": len(rows),
        "errors": len(errors),
        "candidates": len(candidates)
    }


def _collect_urls_from_file(path: str) -> list[str]:
    """Pomoćna funkcija za čitanje URL-ova iz fajla."""
    urls = []
    seen = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.lower().startswith("http"):
                if line not in seen:
                    seen.add(line)
                    urls.append(line)
            elif "," in line:
                first = line.split(",", 1)[0].strip().strip('"')
                if first.lower().startswith("http") and first not in seen:
                    seen.add(first)
                    urls.append(first)
    return urls


def _discover_sitemap(domain: str, log_callback: Optional[Callable] = None) -> Optional[str]:
    """Pomoćna funkcija za autodiscover sitemap-a."""
    candidates = discover_sitemap_urls(domain)
    for candidate in candidates:
        if log_callback:
            log_callback("info", f"Trying sitemap: {candidate}")
        xml = fetch_sitemap(candidate)
        if xml:
            return candidate
    return None