"""
Wrapper za audit pipeline.

Odgovornost: Omogućiti pokretanje audit pipeline-a sa callback-ovima
za progress i log poruke. Koristi se i iz CLI-ja i iz GUI-a.
"""
import json
import os
import threading
import time
from datetime import datetime
from typing import Callable, Optional

import pandas as pd

from audit import extractor, fetcher, shortlist
from audit.exporters import (
    export_dataframe_csv,
    export_errors,
    export_issue_summary,
    export_issue_to_urls,
    export_json_summary,
    export_run_diff_summary,
    export_run_diff_urls,
)
from audit.run_diff import compare_runs, summary_to_dict, url_diffs_to_dataframe
from audit.scorer import build_scored_dataframe, summarize_by_category, summarize_sitewide_scores
from audit.issue_grouping import create_issue_summary, create_issue_to_urls_mapping
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
    log_callback: Optional[Callable[[str, str], None]] = None,
    stop_event: Optional[threading.Event] = None,
    compare_with_previous: Optional[str] = None,
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
        
        stop_event: Event za zaustavljanje pipeline-a.
        
        compare_with_previous: Optional path to previous run's output_dir
            for run-to-run comparison. If provided, generates diff outputs.

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
    # "input_file" i "urls_file" su sinonimi — GUI šalje "urls_file"
    input_file = config.get("input_file") or config.get("urls_file") or ""
    domain = config.get("domain") or ""
    sitemap_url = config.get("sitemap_url") or ""
    output_dir = config.get("output_dir") or ""
    # max_urls može doći kao string iz GUI QLineEdit — konvertuj u int ili None
    _raw_max = config.get("max_urls")
    try:
        max_urls = int(_raw_max) if _raw_max else None
    except (ValueError, TypeError):
        max_urls = None
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
    # Highest priority: URLs already collected by GUI (Load Sitemap / file browse)
    pre_loaded_urls: list[str] = config.get("urls") or []
    if pre_loaded_urls:
        urls = pre_loaded_urls
        if max_urls:
            urls = urls[:max_urls]
        log("info", f"Using {len(urls)} pre-loaded URLs")
    elif input_file and os.path.isfile(input_file):
        log("info", f"Loading URLs from file: {input_file}")
        urls = _collect_urls_from_file(input_file)
        if max_urls:
            urls = urls[:max_urls]
    elif domain:
        log("info", f"Discovering sitemap for domain: {domain}")
        sitemap_url = _discover_sitemap(domain, log_callback)
        if not sitemap_url:
            raise RuntimeError("Could not find sitemap")
        all_urls = collect_urls_from_sitemap(sitemap_url)
        urls, used_fallback = filter_product_like_urls(all_urls)
        if used_fallback:
            log("warning", f"No product URL patterns matched — using all {len(urls)} URLs (may include categories)")
        else:
            log("info", f"URL filter: kept {len(urls)} product-like URLs out of {len(all_urls)} total")
        if max_urls:
            urls = urls[:max_urls]
    elif sitemap_url:
        all_urls = collect_urls_from_sitemap(sitemap_url)
        urls, used_fallback = filter_product_like_urls(all_urls)
        if used_fallback:
            log("warning", f"No product URL patterns matched — using all {len(urls)} URLs (may include categories)")
        else:
            log("info", f"URL filter: kept {len(urls)} product-like URLs out of {len(all_urls)} total")
        if max_urls:
            urls = urls[:max_urls]
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
            stop_event=stop_event,
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

    # --- Step 8b: Issue-centric grouping ---
    log("info", "Creating issue-centric grouping...")
    issue_summary = create_issue_summary(df_scored)
    export_issue_summary(issue_summary, os.path.join(output_dir, "issue_summary.csv"))
    log("info", f"Exported issue_summary.csv — {len(issue_summary)} issue types")
    
    issue_to_urls = create_issue_to_urls_mapping(df_scored)
    export_issue_to_urls(issue_to_urls, os.path.join(output_dir, "issue_to_urls.csv"))
    log("info", f"Exported issue_to_urls.csv — {len(issue_to_urls)} URL-issue mappings")

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
        # Handle NaN values in indexability_flags
        "pages_with_indexability_flags": int((df_scored["indexability_flags"].fillna("").str.len() > 0).sum()),
        "manual_review_candidates": len(candidates),
        "non_product_pages": int((~df_scored["is_likely_product_page"].astype(bool)).sum()),
        "elapsed_seconds": elapsed,
        "stopped_early": config.get("stopped_early", False),
        **sitewide,
    }

    export_json_summary(run_summary, os.path.join(output_dir, "run_summary.json"))
    log("info", f"Run completed in {elapsed}s")

    # --- Step 11: Run-to-run comparison (optional) ---
    if compare_with_previous and os.path.isdir(compare_with_previous):
        log("info", f"Comparing with previous run: {compare_with_previous}")
        report_progress(len(rows), total_urls, "diff")
        
        try:
            diff_summary, url_diffs = compare_runs(compare_with_previous, output_dir)
            
            # Export diff summary
            diff_dict = summary_to_dict(diff_summary)
            export_run_diff_summary(
                diff_dict,
                os.path.join(output_dir, "run_diff_summary.json")
            )
            log("info", "Exported run_diff_summary.json")
            
            # Export URL-level diff
            diff_df = url_diffs_to_dataframe(url_diffs)
            export_run_diff_urls(
                diff_df,
                os.path.join(output_dir, "run_diff_urls.csv")
            )
            log("info", f"Exported run_diff_urls.csv — {len(url_diffs)} URLs compared")
            
            # Export category diff if available
            if diff_summary.category_changes:
                cat_diff_df = pd.DataFrame.from_dict(
                    diff_summary.category_changes,
                    orient="index"
                ).reset_index().rename(columns={"index": "category"})
                export_run_diff_categories(
                    cat_diff_df,
                    os.path.join(output_dir, "run_diff_categories.csv")
                )
                log("info", f"Exported run_diff_categories.csv — {len(diff_summary.category_changes)} categories")
            
            # Log summary
            log("info", f"Diff summary: {diff_summary.improved_count} improved, "
                       f"{diff_summary.degraded_count} degraded, "
                       f"{diff_summary.resolved_issues_count} issues resolved, "
                       f"{diff_summary.new_issues_count} new issues")
            
        except Exception as e:
            log("warning", f"Run comparison failed: {e}")

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