import random, csv, os

ITEM_PATH = os.getenv("ITEM_PATH", "data/sample_items.csv")

def _load_items():
    with open(ITEM_PATH, newline='', encoding='utf-8') as f:
        rdr = csv.DictReader(f)
        items = [r["title"] for r in rdr]
    return items

ITEMS = _load_items()

def serve(user_id: str, context=None):
    # 유저ID 해시 기반 랜덤 시드 → 개인화 느낌
    rnd = random.Random(hash(user_id) % (2**32))
    return rnd.sample(ITEMS, k=min(3, len(ITEMS)))
