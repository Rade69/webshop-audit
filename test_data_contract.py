#!/usr/bin/env python3
"""
Test za provjeru data contract konsolidacije.

Ovo je jednostavan test koji provjerava da li su svi fajlovi
usklađeni sa canonical nazivima kolona.
"""

import ast
import os
import sys

def extract_canonical_columns():
    """Ekstraktuje canonical kolone iz extractor.py i scorer.py."""
    canonical_columns = set()
    
    # Čitaj extractor.py
    with open('audit/extractor.py', 'r') as f:
        content = f.read()
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == 'ProductAuditRow':
                for item in node.body:
                    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                        canonical_columns.add(item.target.id)
    
    # Čitaj scorer.py - kolone koje dodaje build_scored_dataframe
    with open('audit/scorer.py', 'r') as f:
        content = f.read()
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'build_scored_dataframe':
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        if isinstance(item.targets[0], ast.Subscript) and isinstance(item.targets[0].value, ast.Name):
                            if item.targets[0].value.id == 'df':
                                col_name = None
                                if isinstance(item.targets[0].slice, ast.Constant):
                                    col_name = item.targets[0].slice.value
                                elif isinstance(item.targets[0].slice, ast.Str):
                                    col_name = item.targets[0].slice.s
                                if col_name:
                                    canonical_columns.add(col_name)
    
    return canonical_columns

def check_file_for_aliases(filepath, canonical_columns):
    """Provjerava fajl za zastarjele aliase."""
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
            # Provjeri da li se deprecated alias pojavljuje u kodu
            if deprecated in content:
                # Ali ne provjeravaj ako je canonical također prisutan (možda je već popravljeno)
                if canonical not in content or content.count(deprecated) > content.count(canonical):
                    issues.append(f"  - '{deprecated}' → treba biti '{canonical}'")
    
    return issues

def main():
    print("🔍 Provjera data contract konsolidacije...")
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
            issues = check_file_for_aliases(filepath, set())
            if issues:
                all_issues.extend([(filepath, issue) for issue in issues])
                for issue in issues:
                    print(f"  ⚠️  {issue}")
            else:
                print(f"  ✅ Nema zastarjelih aliasa")
        else:
            print(f"  ❌ Fajl ne postoji: {filepath}")
    
    print()
    
    if all_issues:
        print("❌ Pronađeni su zastarjeli aliasi:")
        for filepath, issue in all_issues:
            print(f"  {filepath}: {issue}")
        return 1
    else:
        print("✅ Svi fajlovi su usklađeni sa canonical nazivima kolona!")
        return 0

if __name__ == '__main__':
    sys.exit(main())