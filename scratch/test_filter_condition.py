import sys
sys.stdout.reconfigure(encoding='utf-8')

def is_all_grup_brand_selected(filters: dict) -> bool:
    bg_val = filters.get("brand_groups") or filters.get("brand_group") or filters.get("grup_brand") or filters.get("brand")
    if not bg_val:
        return True
    if isinstance(bg_val, list):
        valid_bg = [str(bg).strip() for bg in bg_val if bg and str(bg).upper() not in ["ALL", "SEMUA", "SEMUA GRUP BRAND", "SEMUA BRAND"]]
        return len(valid_bg) == 0
    else:
        bg_str = str(bg_val).strip().upper()
        return bg_str in ["", "ALL", "SEMUA", "SEMUA GRUP BRAND", "SEMUA BRAND"]

test_cases = [
    ({}, True),
    ({'grup_brand': 'ALL'}, True),
    ({'grup_brand': 'SEMUA'}, True),
    ({'grup_brand': 'GB 1'}, False),
    ({'grup_brand': ['GB 1', 'GB 2']}, False),
    ({'brand_groups': ['ALL']}, True),
    ({'brand_group': 'GB 5'}, False),
]

for tc, expected in test_cases:
    res = is_all_grup_brand_selected(tc)
    print(f"Filter: {tc} => Result: {res} (Expected: {expected}) -> {'PASS' if res == expected else 'FAIL'}")
