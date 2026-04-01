#!/usr/bin/env python3
"""
Testovi za novi shortlist model sa severity i reason code-ovima.
"""

import pandas as pd
import sys
import os

# Add parent directory to path to import audit module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from audit.shortlist import ShortlistCandidate, select_manual_review_candidates


def create_test_dataframe():
    """Create a test DataFrame with various scenarios."""
    data = {
        "url": [
            "https://example.com/product1",  # CRITICAL: fetch error
            "https://example.com/product2",  # CRITICAL: non-200
            "https://example.com/product3",  # CRITICAL: not product page
            "https://example.com/product4",  # HIGH: noindex
            "https://example.com/product5",  # HIGH: canonical mismatch
            "https://example.com/product6",  # HIGH: missing price+schema on product page
            "https://example.com/product7",  # MEDIUM: missing price
            "https://example.com/product8",  # MEDIUM: missing schema
            "https://example.com/product9",  # MEDIUM: low content
            "https://example.com/product10", # MEDIUM: JS rendered
            "https://example.com/product11", # LOW: low score only
            "https://example.com/product12", # Good product
        ],
        "overall_score": [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 25, 95],
        "is_likely_product_page": [True, True, False, True, True, True, True, True, True, True, True, True],
        "is_likely_js_rendered": [False, False, False, False, False, False, False, False, False, True, False, False],
        "js_render_confidence": ["none", "none", "none", "none", "none", "none", "none", "none", "none", "high", "none", "none"],
        "flag_noindex": [False, False, False, True, False, False, False, False, False, False, False, False],
        "flag_canonical_mismatch": [False, False, False, False, True, False, False, False, False, False, False, False],
        "flag_fetch_error": [True, False, False, False, False, False, False, False, False, False, False, False],
        "flag_non_200": [False, True, False, False, False, False, False, False, False, False, False, False],
        "flag_js_rendered": [False, False, False, False, False, False, False, False, False, True, False, False],
        "suspicious_price_missing": [False, False, False, False, False, True, True, False, False, False, False, False],
        "suspicious_schema_missing": [False, False, False, False, False, True, False, True, False, False, False, False],
        "suspicious_low_content": [False, False, False, False, False, False, False, False, True, False, False, False],
        "flag_not_product_page": [False, False, True, False, False, False, False, False, False, False, False, False],
    }
    
    return pd.DataFrame(data)


def test_shortlist_candidate_class():
    """Test ShortlistCandidate class."""
    print("🧪 Testiranje ShortlistCandidate klase...")
    
    df = create_test_dataframe()
    results = []
    
    for _, row in df.iterrows():
        candidate = ShortlistCandidate(row)
        results.append({
            "url": candidate.url,
            "severity": candidate.severity,
            "reasons": candidate.reasons,
            "severity_score": candidate.severity_score
        })
    
    # Check specific cases
    test_cases = [
        ("CRITICAL for fetch error", results[0]["severity"] == "CRITICAL", "fetch-error" in results[0]["reasons"]),
        ("CRITICAL for non-200", results[1]["severity"] == "CRITICAL", "non-200" in results[1]["reasons"]),
        ("CRITICAL for not product page", results[2]["severity"] == "CRITICAL", "not-product-page" in results[2]["reasons"]),
        ("HIGH for noindex", results[3]["severity"] == "HIGH", "noindex" in results[3]["reasons"]),
        ("HIGH for canonical mismatch", results[4]["severity"] == "HIGH", "canonical-mismatch" in results[4]["reasons"]),
        ("HIGH for missing price+schema", results[5]["severity"] == "HIGH", 
         "missing-price-critical" in results[5]["reasons"] and "missing-schema-critical" in results[5]["reasons"]),
        ("MEDIUM for missing price", results[6]["severity"] == "MEDIUM", "missing-price" in results[6]["reasons"]),
        ("MEDIUM for missing schema", results[7]["severity"] == "MEDIUM", "missing-schema" in results[7]["reasons"]),
        ("MEDIUM for low content", results[8]["severity"] == "MEDIUM", "low-content" in results[8]["reasons"]),
        ("MEDIUM for JS rendered", results[9]["severity"] == "MEDIUM", "js-rendered-high" in results[9]["reasons"]),
        ("LOW for low score only", results[10]["severity"] == "LOW", "low-score" in results[10]["reasons"]),
        ("Good product not in shortlist", results[11]["severity"] == "LOW", len(results[11]["reasons"]) == 0),
    ]
    
    all_passed = True
    for name, severity_ok, reasons_ok in test_cases:
        passed = severity_ok and reasons_ok
        status = "✅" if passed else "❌"
        print(f"  {status} {name}")
        if not passed:
            print(f"    Severity: {severity_ok}, Reasons: {reasons_ok}")
            all_passed = False
    
    return all_passed


def test_selection_logic():
    """Test selection_manual_review_candidates function."""
    print("\n🧪 Testiranje logike selekcije...")
    
    df = create_test_dataframe()
    
    # Test with small limit
    candidates = select_manual_review_candidates(df, max_candidates=5)
    
    print(f"  Odabrano {len(candidates)} kandidata od {len(df)}")
    
    # Check that critical cases are included first
    critical_urls = ["https://example.com/product1", "https://example.com/product2", "https://example.com/product3"]
    selected_urls = candidates["url"].tolist()
    
    # First 3 should be critical
    first_three = selected_urls[:3]
    critical_included = all(url in first_three for url in critical_urls[:min(3, len(critical_urls))])
    
    if critical_included:
        print("  ✅ Kritični slučajevi uključeni prvi")
    else:
        print(f"  ❌ Kritični slučajevi nisu prvi: {first_three}")
    
    # Check severity distribution
    severity_counts = candidates["severity"].value_counts().to_dict()
    print(f"  Distribucija severitija: {severity_counts}")
    
    # Test severity limits
    severity_limits = {"CRITICAL": 2, "HIGH": 2, "MEDIUM": 1, "LOW": 0}
    limited_candidates = select_manual_review_candidates(df, max_candidates=10, severity_limits=severity_limits)
    
    limited_severity = limited_candidates["severity"].value_counts().to_dict()
    print(f"  Sa limitima: {limited_severity}")
    
    # Check limits are respected
    limits_respected = True
    for severity, limit in severity_limits.items():
        if limit is not None and limited_severity.get(severity, 0) > limit:
            limits_respected = False
            print(f"  ❌ Limit za {severity} premašen: {limited_severity.get(severity, 0)} > {limit}")
    
    if limits_respected:
        print("  ✅ Svi limiti poštovani")
    
    return critical_included and limits_respected


def test_csv_columns():
    """Test that CSV has expected columns."""
    print("\n🧪 Testiranje CSV kolona...")
    
    df = create_test_dataframe()
    candidates = select_manual_review_candidates(df, max_candidates=10)
    
    expected_columns = ["url", "overall_score", "severity", "reasons", "reason_count", 
                       "is_likely_product_page", "is_likely_js_rendered", "severity_score"]
    
    missing = [col for col in expected_columns if col not in candidates.columns]
    extra = [col for col in candidates.columns if col not in expected_columns and col not in ["title", "h1", "breadcrumb_text", "schema_product_present", "schema_price", "html_price_text", "visible_text_length", "catalog_score", "machine_score", "commerce_score"]]
    
    if not missing and not extra:
        print("  ✅ Sve očekivane kolone prisutne")
        return True
    else:
        if missing:
            print(f"  ❌ Nedostaju kolone: {missing}")
        if extra:
            print(f"  ❌ Neočekivane kolone: {extra}")
        return False


def main():
    print("🔬 Testiranje novog shortlist modela")
    print("=" * 50)
    
    tests = [
        ("ShortlistCandidate klasa", test_shortlist_candidate_class),
        ("Logika selekcije", test_selection_logic),
        ("CSV kolone", test_csv_columns),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n{name}:")
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ❌ Greška: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 50)
    print("📊 REZULTATI TESTOVA:")
    
    all_passed = True
    for name, passed in results:
        status = "✅ PROŠAO" if passed else "❌ PAO"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 Svi testovi prošli!")
        return 0
    else:
        print("\n⚠️  Neki testovi nisu prošli")
        return 1


if __name__ == "__main__":
    sys.exit(main())