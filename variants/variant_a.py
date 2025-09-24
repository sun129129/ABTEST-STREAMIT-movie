import random, csv, os

ITEM_PATH = os.getenv("ITEM_PATH", "data/sample_items.csv")

def _load_items():
    with open(ITEM_PATH, newline='', encoding='utf-8') as f:
        rdr = csv.DictReader(f)
        items = [r["title"] for r in rdr]
    return items

ITEMS = _load_items()

def serve(user_id: str, context=None):
    # 간단히 상위 N 고정(데모용)
    return ITEMS[:3] if len(ITEMS) >= 3 else ITEMS
