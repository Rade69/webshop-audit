#!/usr/bin/env python3
"""
webshop_audit — main entry point.

Usage examples:
  python main.py --sitemap https://example.com/sitemap.xml --max-urls 300
  python main.py --domain https://example.com --max-urls 300
  python main.py --urls-file inputs/urls.txt --delay 0.5
  python main.py --diff-runs --old-output outputs/run1 --new-output outputs/run2
"""

import argparse
import os
import sys

import pandas as pd

from audit.pipeline import run_audit
from config import DEFAULT_DELAY, DEFAULT_OUTPUT_DIR


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="WebshopAudit — initial product audit tool",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    source = parser.add_mutually_exclusive_group(required=False)
    source.add_argument("--sitemap", metavar="URL", help="Direct URL to sitemap.xml")
    source.add_argument("--domain", metavar="URL", help="Shop domain — sitemap will be auto-discovered")
    source.add_argument("--urls-file", metavar="FILE", help="Path to .txt or .csv file with product URLs")

    # Diff mode
    diff_group = parser.add_argument_group("Run comparison mode")
    diff_group.add_argument("--diff-runs", action="store_true", help="Compare two audit runs instead of running new audit")
    diff_group.add_argument("--old-output", metavar="DIR", help="Path to older run's output directory (for --diff-runs)")
    diff_group.add_argument("--new-output", metavar="DIR", help="Path to newer run's output directory (for --diff-runs)")

    parser.add_argument("--max-urls", type=int, default=None, help="Maximum number of URLs to process")
    parser.add_argument("--generate-report", metavar="OUTPUT_DIR",
                        help="Generate Word report from existing output dir (skips audit)")
    parser.add_argument(
        "--delay", type=float, default=DEFAULT_DELAY,
        help=f"Delay between requests in seconds (default: {DEFAULT_DELAY})"
    )
    parser.add_argument(
        "--output-dir", default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--compare-with", metavar="DIR",
        help="Compare this run with a previous run's output directory"
    )

    # Export options
    export_group = parser.add_argument_group("Export options")
    export_group.add_argument(
        "--export-issues", action="store_true",
        help="Export issue-centric summary and mapping CSVs"
    )
    export_group.add_argument(
        "--export-evidence", action="store_true",
        help="Export evidence snapshots for all products"
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # Standalone report generation
    if hasattr(args, "generate_report") and args.generate_report:
        from audit.report_generator import generate_report
        path = generate_report(args.generate_report)
        print(f"Izvještaj sačuvan: {path}")
        return

    # Diff mode: compare two existing runs
    if args.diff_runs:
        if not args.old_output or not args.new_output:
            print("ERROR: --diff-runs requires both --old-output and --new-output")
            sys.exit(1)
        
        from audit.run_diff import compare_runs, summary_to_dict, url_diffs_to_dataframe
        from audit.exporters import export_run_diff_summary, export_run_diff_urls, export_run_diff_categories
        
        if not os.path.isdir(args.old_output):
            print(f"ERROR: Old output directory not found: {args.old_output}")
            sys.exit(1)
        if not os.path.isdir(args.new_output):
            print(f"ERROR: New output directory not found: {args.new_output}")
            sys.exit(1)
        
        print(f"\n{'='*60}")
        print(f"  WebshopAudit — Run Comparison")
        print(f"{'='*60}")
        print(f"  Old run: {args.old_output}")
        print(f"  New run: {args.new_output}")
        print(f"{'='*60}\n")
        
        try:
            summary, url_diffs = compare_runs(args.old_output, args.new_output)
            
            # Export diff outputs to new run's directory
            diff_dict = summary_to_dict(summary)
            export_run_diff_summary(diff_dict, os.path.join(args.new_output, "run_diff_summary.json"))
            print(f"  Exported: run_diff_summary.json")
            
            diff_df = url_diffs_to_dataframe(url_diffs)
            export_run_diff_urls(diff_df, os.path.join(args.new_output, "run_diff_urls.csv"))
            print(f"  Exported: run_diff_urls.csv ({len(url_diffs)} URLs)")
            
            if summary.category_changes:
                cat_diff_df = pd.DataFrame.from_dict(summary.category_changes, orient="index").reset_index().rename(columns={"index": "category"})
                export_run_diff_categories(cat_diff_df, os.path.join(args.new_output, "run_diff_categories.csv"))
                print(f"  Exported: run_diff_categories.csv ({len(summary.category_changes)} categories)")
            
            # Print summary
            print(f"\n{'='*60}")
            print(f"  DIFF SUMMARY")
            print(f"{'='*60}")
            print(f"  Score changes:")
            print(f"    Overall:  {summary.avg_overall_delta:+.1f}")
            print(f"    Catalog:  {summary.avg_catalog_delta:+.1f}")
            print(f"    Machine:  {summary.avg_machine_delta:+.1f}")
            print(f"    Commerce: {summary.avg_commerce_delta:+.1f}")
            print(f"\n  URL status:")
            print(f"    Unchanged:  {summary.unchanged_count}")
            print(f"    Improved:   {summary.improved_count}")
            print(f"    Degraded:   {summary.degraded_count}")
            print(f"    New URLs:   {summary.new_url_count}")
            print(f"    Removed:    {summary.removed_url_count}")
            print(f"\n  Issues:")
            print(f"    Critical/High (old): {summary.old_critical_high_count}")
            print(f"    Critical/High (new): {summary.new_critical_high_count}")
            print(f"    Change: {summary.critical_high_delta:+d}")
            print(f"\n  Issues resolved: {summary.resolved_issues_count}")
            print(f"  New issues:      {summary.new_issues_count}")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"ERROR: Run comparison failed: {e}")
            sys.exit(1)
        
        return

    if not args.sitemap and not args.domain and not getattr(args, "urls_file", None):
        print("ERROR: Navedite --sitemap, --domain ili --urls-file (ili --generate-report).")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  WebshopAudit — CLI Run")
    print(f"{'='*60}\n")

    # Build config for shared pipeline
    config = {
        "output_dir": args.output_dir,
        "max_urls": args.max_urls,
        "delay": args.delay,
    }

    # Determine input source
    if args.urls_file:
        config["input_file"] = args.urls_file
    elif args.domain:
        config["domain"] = args.domain
    elif args.sitemap:
        config["sitemap_url"] = args.sitemap

    # Optional: compare with previous run
    if args.compare_with:
        if not os.path.isdir(args.compare_with):
            print(f"WARNING: Compare directory not found: {args.compare_with}")
            print("  Running audit without comparison.")
        else:
            config["compare_with_previous"] = args.compare_with
            print(f"  Will compare with: {args.compare_with}")

    # Use shared pipeline - the same function that GUI uses
    result = run_audit(config=config)

    # Terminal summary
    print(f"\n{'='*60}")
    print("  AUDIT COMPLETE")
    print(f"{'='*60}")
    print(f"  URLs processed       : {result['total_urls']}")
    print(f"  Successfully parsed  : {result['processed']}")
    print(f"  Errors               : {result['errors']}")
    print(f"  Review candidates    : {result['candidates']}")
    print(f"\n  Outputs saved to: {result['output_dir']}")
    if args.compare_with and os.path.isdir(args.compare_with):
        print(f"  Diff outputs saved to: {result['output_dir']}")
    
    # Export options
    if args.export_issues:
        from audit.issue_grouping import create_issue_summary, create_issue_to_urls_mapping
        from audit.exporters import export_issue_summary, export_issue_to_urls
        import pandas as pd
        
        # Load scored data
        scored_path = os.path.join(result['output_dir'], "products_scored.csv")
        if os.path.isfile(scored_path):
            df = pd.read_csv(scored_path)
            
            # Export issue summary
            issue_summary = create_issue_summary(df)
            export_issue_summary(issue_summary, os.path.join(result['output_dir'], "issue_summary.csv"))
            print(f"  Exported: issue_summary.csv")
            
            # Export issue to URLs mapping
            issue_to_urls = create_issue_to_urls_mapping(df)
            export_issue_to_urls(issue_to_urls, os.path.join(result['output_dir'], "issue_to_urls.csv"))
            print(f"  Exported: issue_to_urls.csv")
        else:
            print(f"  WARNING: products_scored.csv not found, skipping issue export")
    
    if args.export_evidence:
        from audit.evidence import EvidenceSnapshot, format_evidence_for_display
        import pandas as pd
        
        # Load scored data
        scored_path = os.path.join(result['output_dir'], "products_scored.csv")
        if os.path.isfile(scored_path):
            df = pd.read_csv(scored_path)
            
            # Generate evidence for each row
            evidence_records = []
            for _, row in df.iterrows():
                evidence = EvidenceSnapshot.from_row(row)
                evidence_records.append({
                    "url": row.get("url", ""),
                    "status_code": row.get("status_code", ""),
                    "fetch_error": row.get("fetch_error", ""),
                    "canonical": row.get("canonical", ""),
                    "robots_meta": row.get("robots_meta", ""),
                    "html_price_text": row.get("html_price_text", ""),
                    "schema_price": row.get("schema_price", ""),
                    "schema_price_value": row.get("schema_price_value", ""),
                    "schema_currency": row.get("schema_currency", ""),
                    "schema_product_present": row.get("schema_product_present", False),
                    "schema_sku": row.get("schema_sku", ""),
                    "schema_brand": row.get("schema_brand", ""),
                    "breadcrumb_text": row.get("breadcrumb_text", ""),
                    "visible_text_length": row.get("visible_text_length", 0),
                })
            
            evidence_df = pd.DataFrame(evidence_records)
            export_path = os.path.join(result['output_dir'], "evidence_snapshots.csv")
            evidence_df.to_csv(export_path, index=False, encoding="utf-8-sig")
            print(f"  Exported: evidence_snapshots.csv ({len(evidence_records)} rows)")
        else:
            print(f"  WARNING: products_scored.csv not found, skipping evidence export")
    
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
