#!/usr/bin/env python3
"""
Poboljšani test za provjeru data contract konsolidacije.

Traži samo stvarne reference na kolone, ne lažne pozitive.
"""

import os
import re
import sys

def check_file_for_column_references(filepath):
    """Provjerava fajl za zastarjele reference na kolone."""
    deprecated_aliases = {
        'breadcrumb': 'breadcrumb_text',
        'schema_product': 'schema_product_present',
        'price_html': 'html_price_text',
        'price_schema': 'schema_price',
        'robots_noindex': 'flag_noindex',
        'canonical_issue': 'flag_canonical_mismatch',
        'flag_canonical_missing': 'flag_canonical_mismatch',
        'is_product_page': 'is_likely_product_page',
        'missing_price': 'suspicious_price_missing',
        'missing_schema': 'suspicious_schema_missing',
        'html_price_found': 'html_price_text',
        'shipping_info_found': 'shipping_signal',
        'returns_info_found': 'returns_signal',
        'sku': 'schema_sku',
        'gtin': 'schema_gtin',
    }
    
    issues = []
    
    with open(filepath, 'r') as f:
        content = f.read()
        
        for deprecated, canonical in deprecated_aliases.items():
            # Patterni za reference na kolone
            patterns = [
                rf'df\["{deprecated}"\]',  # df["breadcrumb"]
                rf"df\['{deprecated}'\]",  # df['breadcrumb']
                rf'\.get\("{deprecated}"',  # .get("breadcrumb"
                rf"\.get\('{deprecated}'",  # .get('breadcrumb'
                rf'self\._df\["{deprecated}"\]',  # self._df["breadcrumb"]
                rf'candidate\["{deprecated}"\]',  # candidate["breadcrumb"]
                rf'row\["{deprecated}"\]',  # row["breadcrumb"]
                rf'product\["{deprecated}"\]',  # product["breadcrumb"]
            ]
            
            # Provjeri da li postoji deprecated reference
            has_deprecated = any(re.search(pattern, content) for pattern in patterns)
            
            if has_deprecated:
                # Provjeri da li postoji canonical reference
                has_canonical = any(
                    re.search(pattern.replace(deprecated, canonical), content) 
                    for pattern in patterns
                )
                
                if not has_canonical:
                    issues.append(f"  - '{deprecated}' → treba biti '{canonical}'")
    
    return issues

def main():
    print("🔍 Provjera data contract konsolidacije (poboljšana)...")
    print()
    
    # Lista fajlova za provjeru
    files_to_check = [
        'gui/controllers/results_controller.py',
        'gui/tabs/results_tab.py',
        'gui/controllers/review_controller.py',
        'gui/tabs/review_queue_tab.py',
        'audit/report_generator.py',
    ]
    
    all_issues = []
    
    for filepath in files_to_check:
        if os.path.exists(filepath):
            print(f"📄 Provjeravam {filepath}...")
            issues = check_file_for_column_references(filepath)
            if issues:
                all_issues.extend([(filepath, issue) for issue in issues])
                for issue in issues:
                    print(f"  ⚠️  {issue}")
            else:
                print(f"  ✅ Nema zastarjelih referenci na kolone")
        else:
            print(f"  ❌ Fajl ne postoji: {filepath}")
    
    print()
    
    if all_issues:
        print("❌ Pronađene su zastarjele reference na kolone:")
        for filepath, issue in all_issues:
            print(f"  {filepath}: {issue}")
        return 1
    else:
        print("✅ Svi fajlovi su usklađeni sa canonical nazivima kolona!")
        return 0

if __name__ == '__main__':
    sys.exit(main())