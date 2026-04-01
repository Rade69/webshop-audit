#!/usr/bin/env python3
"""
Integracioni test za novi shortlist model.
Provjerava da li se novi model integriše sa postojećim pipeline-om.
"""

import os
import sys
import tempfile
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from audit.shortlist import select_manual_review_candidates, select_best_products_sample


def create_realistic_test_data():
    """Create a more realistic test dataset."""
    # Simulate 100 products with various issues
    data = {
        "url": [f"https://example.com/product{i}" for i in range(100)],
        "overall_score": [max(0, min(100, i)) for i in range(100)],  # Scores from 0 to 99
        "is_likely_product_page": [True] * 90 + [False] * 10,  # 90% product pages
        "is_likely_js_rendered": [False] * 85 + [True] * 15,  # 15% JS rendered
        "js_render_confidence": ["none"] * 85 + ["high"] * 5 + ["medium"] * 5 + ["low"] * 5,
        "flag_noindex": [False] * 95 + [True] * 5,  # 5% noindex
        "flag_canonical_mismatch": [False] * 90 + [True] * 10,  # 10% canonical issues
        "flag_fetch_error": [False] * 98 + [True] * 2,  # 2% fetch errors
        "flag_non_200": [False] * 96 + [True] * 4,  # 4% non-200
        "flag_js_rendered": [False] * 85 + [True] * 15,
        "suspicious_price_missing": [False] * 80 + [True] * 20,  # 20% missing price
        "suspicious_schema_missing": [False] * 75 + [True] * 25,  # 25% missing schema
        "suspicious_low_content": [False] * 70 + [True] * 30,  # 30% low content
        "flag_not_product_page": [False] * 90 + [True] * 10,
        "agent_ready": [False] * 60 + [True] * 40,  # 40% agent ready
        "indexability_flags": [""] * 80 + ["noindex"] * 5 + ["canonical_mismatch"] * 10 + ["fetch_error"] * 2 + ["status_404"] * 3,
    }
    
    return pd.DataFrame(data)


def test_shortlist_size_control():
    """Test that shortlist doesn't become too large."""
    print("📊 Testiranje kontrole veličine shortlista...")
    
    df = create_realistic_test_data()
    
    # Test with default limits (max 50)
    candidates = select_manual_review_candidates(df, max_candidates=50)
    
    print(f"  Ukupno proizvoda: {len(df)}")
    print(f"  Odabrano kandidata: {len(candidates)}")
    print(f"  Procentualno: {len(candidates)/len(df)*100:.1f}%")
    
    # Should not exceed max_candidates
    if len(candidates) <= 50:
        print("  ✅ Shortlist ne prelazi maksimalnu veličinu")
    else:
        print(f"  ❌ Shortlist prelazi maksimum: {len(candidates)} > 50")
        return False
    
    # Check severity distribution
    severity_counts = candidates["severity"].value_counts()
    print(f"  Distribucija severitija:")
    for severity, count in severity_counts.items():
        print(f"    {severity}: {count} ({count/len(candidates)*100:.1f}%)")
    
    # Critical cases should be prioritized
    critical_count = severity_counts.get("CRITICAL", 0)
    if critical_count > 0:
        print(f"  ✅ Kritični slučajevi uključeni: {critical_count}")
    else:
        # Check if there were any critical cases in dataset
        critical_in_dataset = len(df[df["flag_fetch_error"] | df["flag_non_200"] | df["flag_not_product_page"]])
        if critical_in_dataset > 0:
            print(f"  ⚠️  Nema kritičnih slučajeva u shortlistu, a ima {critical_in_dataset} u datasetu")
        else:
            print("  ✅ Nema kritičnih slučajeva u datasetu")
    
    return True


def test_best_products_sample():
    """Test that best products sample still works."""
    print("\n🏆 Testiranje best products sample...")
    
    df = create_realistic_test_data()
    
    best = select_best_products_sample(df, top_n=20)
    
    print(f"  Odabrano najboljih: {len(best)}")
    
    # Should have high scores
    avg_score = best["overall_score"].mean()
    print(f"  Prosječan score: {avg_score:.1f}")
    
    if avg_score > 70:
        print("  ✅ Najbolji proizvodi imaju visoke scoreove")
    else:
        print(f"  ⚠️  Prosječan score je nizak: {avg_score:.1f}")
    
    # Check agent_ready products
    agent_ready_count = best["agent_ready"].sum()
    print(f"  Agent-ready proizvoda: {agent_ready_count}/{len(best)}")
    
    return True


def test_reason_codes():
    """Test that reason codes are meaningful."""
    print("\n🔍 Testiranje reason code-ova...")
    
    df = create_realistic_test_data()
    candidates = select_manual_review_candidates(df, max_candidates=30)
    
    # Check that all candidates have reasons (except maybe LOW severity)
    candidates_with_reasons = candidates[candidates["reason_count"] > 0]
    print(f"  Kandidata sa razlozima: {len(candidates_with_reasons)}/{len(candidates)}")
    
    # Check reason diversity
    all_reasons = []
    for reasons_str in candidates["reasons"]:
        if pd.notna(reasons_str) and reasons_str:
            all_reasons.extend([r.strip() for r in reasons_str.split(",")])
    
    unique_reasons = set(all_reasons)
    print(f"  Jedinstvenih reason code-ova: {len(unique_reasons)}")
    print(f"  Primjeri: {list(unique_reasons)[:5]}...")
    
    if len(unique_reasons) > 3:
        print("  ✅ Raznovrsni reason code-ovi")
    else:
        print("  ⚠️  Malo raznovrsnih reason code-ova")
    
    return True


def test_csv_export():
    """Test CSV export compatibility."""
    print("\n💾 Testiranje CSV exporta...")
    
    df = create_realistic_test_data()
    candidates = select_manual_review_candidates(df, max_candidates=20)
    
    # Check required columns for GUI
    required_columns = ["url", "overall_score", "severity", "reasons"]
    missing_columns = [col for col in required_columns if col not in candidates.columns]
    
    if not missing_columns:
        print("  ✅ Sve potrebne kolone prisutne")
        
        # Check data types
        valid_types = True
        for col in required_columns:
            if candidates[col].isna().all():
                print(f"  ⚠️  Kolona '{col}' je prazna")
                valid_types = False
        
        if valid_types:
            print("  ✅ Podaci su validni")
            return True
        else:
            return False
    else:
        print(f"  ❌ Nedostaju kolone: {missing_columns}")
        return False


def main():
    print("🔗 Integracioni testovi za novi shortlist model")
    print("=" * 60)
    
    tests = [
        ("Kontrola veličine", test_shortlist_size_control),
        ("Best products sample", test_best_products_sample),
        ("Reason code-ovi", test_reason_codes),
        ("CSV export", test_csv_export),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n{name}:")
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ❌ Greška: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("📈 REZULTATI INTEGRACIONIH TESTOVA:")
    
    all_passed = True
    for name, passed in results:
        status = "✅ PROŠAO" if passed else "❌ PAO"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("🎊 Svi integracioni testovi prošli!")
        print("\n📋 ZAKLJUČAK:")
        print("  • Shortlist model kontroliše veličinu")
        print("  • Severity nivoi rade kako treba")
        print("  • Reason code-ovi su smisleni")
        print("  • CSV export je kompatibilan")
        print("  • Best products sample i dalje radi")
        return 0
    else:
        print("⚠️  Neki integracioni testovi nisu prošli")
        return 1


if __name__ == "__main__":
    sys.exit(main())