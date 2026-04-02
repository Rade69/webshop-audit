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

    return parser.parse_args()


def main():
    args = parse_args()

    # Standalone report generation
    if hasattr(args, "generate_report") and args.generate_report:
        from audit.report_generator import generate_report
        path = generate_report(args.generate_report)
        print(f"Izvještaj sačuvan: {path}")
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
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
