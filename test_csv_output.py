#!/usr/bin/env python3
"""
Test za provjeru CSV output kolona.

Provjerava da li CSV fajlovi imaju očekivane canonical kolone.
"""

import os
import pandas as pd
import sys

def get_expected_columns():
    """Vraća očekivane kolone za products_scored.csv."""
    # Osnovne kolone iz ProductAuditRow
    base_columns = [
        'url', 'final_url', 'status_code', 'fetch_error', 'content_type', 'response_time_ms',
        'title', 'meta_description', 'h1', 'canonical', 'robots_meta', 'breadcrumb_text',
        'visible_text_length', 'image_count', 'product_image_count', 'html_price_text',
        'shipping_signal', 'returns_signal', 'description_word_count', 'has_feature_list',
        'has_spec_table', 'description_quality_score', 'schema_product_present',
        'schema_offer_present', 'schema_name', 'schema_description', 'schema_sku',
        'schema_gtin', 'schema_brand', 'schema_price', 'schema_price_value',
        'schema_currency', 'schema_availability', 'is_likely_product_page',
        'is_likely_js_rendered', 'js_render_confidence'
    ]
    
    # Score kolone iz scorer.py
    score_columns = [
        'catalog_score', 'machine_score', 'commerce_score', 'overall_score',
        'missing_fields', 'indexability_flags', 'flag_noindex', 'flag_canonical_mismatch',
        'flag_fetch_error', 'flag_non_200', 'flag_js_rendered', 'suspicious_price_missing',
        'suspicious_schema_missing', 'suspicious_low_content', 'flag_not_product_page',
        'agent_ready'
    ]
    
    return base_columns + score_columns

def check_csv_columns(csv_path, expected_columns):
    """Provjerava da li CSV ima očekivane kolone."""
    if not os.path.exists(csv_path):
        return False, f"CSV fajl ne postoji: {csv_path}"
    
    try:
        df = pd.read_csv(csv_path, nrows=1)  # Čitaj samo header
        actual_columns = set(df.columns)
        expected_set = set(expected_columns)
        
        missing = expected_set - actual_columns
        extra = actual_columns - expected_set
        
        issues = []
        if missing:
            issues.append(f"Nedostaju kolone: {sorted(missing)}")
        if extra:
            issues.append(f"Extra kolone: {sorted(extra)}")
        
        if issues:
            return False, "; ".join(issues)
        return True, "OK"
        
    except Exception as e:
        return False, f"Greška pri čitanju CSV: {e}"

def main():
    print("🔍 Provjera CSV output kolona...")
    print()
    
    # Kreiraj testni output direktorij ako ne postoji
    test_output_dir = "test_output"
    os.makedirs(test_output_dir, exist_ok=True)
    
    # Očekivane kolone
    expected_columns = get_expected_columns()
    print(f"Očekivano {len(expected_columns)} kolona u products_scored.csv")
    print()
    
    # Provjeri da li postoji neki postojeći CSV za test
    test_csv = os.path.join(test_output_dir, "products_scored.csv")
    
    if os.path.exists(test_csv):
        print(f"📊 Provjeravam {test_csv}...")
        ok, message = check_csv_columns(test_csv, expected_columns)
        if ok:
            print(f"  ✅ CSV kolone su ispravne")
        else:
            print(f"  ❌ {message}")
    else:
        print(f"ℹ️  Nema testnog CSV fajla na {test_csv}")
        print(f"   Pokreni audit run da generiše testne podatke")
    
    print()
    print("📋 Očekivane kolone (prvih 20):")
    for i, col in enumerate(sorted(expected_columns)[:20]):
        print(f"  {i+1:2d}. {col}")
    if len(expected_columns) > 20:
        print(f"  ... i još {len(expected_columns) - 20} kolona")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())