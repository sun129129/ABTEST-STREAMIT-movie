# preprocess.py
# MovieLens 100K에서 아이템 타이틀을 뽑아 data/sample_items.csv 생성
# - 가능한 경로를 자동으로 탐색하고, zip이 있으면 풀어서 사용
# - 사용처: variants/variant_*.py 가 이 CSV를 읽어 Streamlit UI에 아이템 노출

from __future__ import annotations
import csv
import os
import sys
import zipfile
from pathlib import Path
from typing import Optional

# ----- 설정 -----
DATA_DIR = Path(__file__).resolve().parent          # .../data
ZIP_CANDIDATES = [
    DATA_DIR / "ml-100k.zip",
    DATA_DIR / "movielens_100k.zip",
]
EXTRACT_DIR_CANDIDATES = [
    DATA_DIR / "ml-100k",                           # 흔한 구조: data/ml-100k/u.item
    DATA_DIR / "movielens_100k" / "ml-100k",        # 예전 스크립트 구조: data/movielens_100k/ml-100k/u.item
    DATA_DIR / "movielens_100k",                    # 혹시 바로 여기 풀렸다면: data/movielens_100k/u.item
]
OUTPUT_CSV = DATA_DIR / "sample_items.csv"


def find_u_item_path() -> Optional[Path]:
    """
    u.item 파일 경로를 최대한 자동으로 찾는다.
    1) EXTRACT_DIR_CANDIDATES 후보 내에서 u.item 탐색
    2) data/ 이하를 광범위 검색(백업)
    """
    # 1) 후보 경로 우선 탐색
    for base in EXTRACT_DIR_CANDIDATES:
        candidate = base / "u.item"
        if candidate.exists():
            return candidate

    # 2) 백업: data/ 이하를 광범위하게 스캔 (깊이 3단계까지만)
    for p in DATA_DIR.rglob("u.item"):
        # 너무 깊은 곳은 제외(안전장치)
        try:
            rel = p.relative_to(DATA_DIR)
            if len(rel.parts) <= 5:
                return p
        except Exception:
            continue

    return None


def extract_zip_if_needed() -> Optional[Path]:
    """
    data/ 아래에 있는 ml-100k 관련 zip을 찾아 풀고,
    풀린 경로 후보(EXTRACT_DIR_CANDIDATES) 중 존재하는 곳을 반환.
    zip이 없으면 None 반환(이미 풀려있을 수 있음).
    """
    zip_path = None
    for z in ZIP_CANDIDATES:
        if z.exists():
            zip_path = z
            break

    if zip_path is None:
        # zip이 없어도 이미 풀려 있을 수 있음
        return None

    print(f"[INFO] Found zip: {zip_path}")
    # 어디에 풀지? 가장 일반적인 경로: data/ml-100k/
    target_root = DATA_DIR / "ml-100k"
    target_root.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        # zip 안의 최상위 폴더가 ml-100k/라면 그대로 풀림
        zf.extractAll = zf.extractall  # type: ignore  # older editors friendliness
        zf.extractall(DATA_DIR)

    # 일부 배포본은 data/ 바로 아래에 ml-100k/가 생성됨
    # 혹시 다른 폴더명으로 풀렸을 경우를 대비해서 u.item을 다시 찾아본다.
    return find_u_item_path()


def generate_sample_items_csv(u_item_path: Path, out_csv: Path, max_rows: int | None = None) -> None:
    """
    u.item에서 (item_id, title)를 추출해 CSV로 저장.
    인코딩은 원본 특성상 'latin-1'이 안전.
    """
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    seen = set()
    rows = 0

    with u_item_path.open("r", encoding="latin-1") as fin, \
         out_csv.open("w", newline="", encoding="utf-8") as fout:
        writer = csv.DictWriter(fout, fieldnames=["item_id", "title"])
        writer.writeheader()
        for line in fin:
            parts = line.strip().split("|")
            if not parts or len(parts) < 2:
                continue
            item_id, title = parts[0], parts[1]
            # 중복 타이틀 제거(간단한 안전장치)
            key = (item_id, title)
            if key in seen:
                continue
            seen.add(key)
            writer.writerow({"item_id": item_id, "title": title})
            rows += 1
            if max_rows is not None and rows >= max_rows:
                break

    print(f"[OK] Wrote {rows} items → {out_csv}")


def main():
    print(f"[INFO] DATA_DIR = {DATA_DIR}")

    # 1) u.item 경로를 먼저 찾아본다
    u_item = find_u_item_path()
    if u_item is None:
        print("[INFO] u.item not found — trying to extract zip if present...")
        u_item = extract_zip_if_needed()

    # 2) 그래도 없으면 실패
    if u_item is None:
        print("[ERROR] Could not locate 'u.item'.")
        print("        다음 중 하나를 확인하세요:")
        print("        - data/ml-100k.zip 또는 data/movielens_100k.zip 위치")
        print("        - 또는 수동으로 압축을 풀어 data/ml-100k/u.item 가 존재하도록 맞춰주세요.")
        sys.exit(1)

    print(f"[INFO] Using u.item at: {u_item}")

    # 3) sample_items.csv 생성
    generate_sample_items_csv(u_item_path=u_item, out_csv=OUTPUT_CSV, max_rows=None)


if __name__ == "__main__":
    main()
