# analysis/analyze_mlflow.py
# MLflow의 'MAB_Online' 실험에서 run을 읽어 arm별 CTR/트래픽 비중/시간 추이를 집계합니다.

import os
import math
from datetime import datetime, timezone

import mlflow
import pandas as pd
import matplotlib.pyplot as plt

# ===== 설정 =====
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
EXPERIMENT_NAME = os.getenv("MAB_EXPERIMENT", "MAB_Online")

print(f"[INFO] MLFLOW_TRACKING_URI = {MLFLOW_URI}")
mlflow.set_tracking_uri(MLFLOW_URI)

# ===== 실험 찾기 =====
exp = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
if exp is None:
    raise SystemExit(f"[ERROR] Experiment '{EXPERIMENT_NAME}' not found. MLflow UI에서 실험이 생성되었는지 확인하세요.")
exp_id = exp.experiment_id
print(f"[INFO] Experiment id = {exp_id}")

# ===== run 조회 =====
# NOTE: reward(메트릭), arm(파라미터) 기준
df = mlflow.search_runs(
    experiment_ids=[exp_id],
    order_by=["start_time ASC"],    # 시간순
    # filter_string="attributes.status = 'FINISHED'"  # 필요 시 필터
)

if df.empty:
    raise SystemExit("[WARN] runs가 없습니다. Streamlit에서 선택 이벤트를 몇 번 발생시킨 뒤 다시 실행하세요.")

# 필요한 컬럼만 추출(없어도 에러 안 나게 안전 처리)
def safe(col):
    return col if col in df.columns else None

cols = {
    "run_id": "run_id",
    "arm": safe("params.arm"),
    "reward": safe("metrics.reward"),
    "start_time": "start_time",
}
use_cols = [c for c in cols.values() if c is not None]
df = df[use_cols].copy()

# start_time → datetime
df["ts"] = pd.to_datetime(df["start_time"], unit="ms", utc=True).dt.tz_convert(None)

# NaN/이상치 정리
if "reward" in df.columns:
    df = df[df["metrics.reward"].notna()]
    df["reward"] = df["metrics.reward"].astype(float)
else:
    raise SystemExit("[ERROR] run에 metrics.reward가 없습니다. /update가 정상 기록되는지 확인하세요.")

if "params.arm" not in df.columns:
    raise SystemExit("[ERROR] run에 params.arm이 없습니다. /update에서 arm 파라미터가 기록되는지 확인하세요.")

df.rename(columns={"params.arm": "arm"}, inplace=True)

print(f"[INFO] 총 run 수: {len(df)}")
print(df.tail(5))

# ===== 집계: arm별 전체 CTR & 트래픽 비중 =====
summary = (
    df.groupby("arm")
      .agg(n_runs=("run_id", "count"),
           ctr=("reward", "mean"))
      .sort_values("ctr", ascending=False)
)
summary["traffic_share"] = summary["n_runs"] / summary["n_runs"].sum()
print("\n=== ARM SUMMARY ===")
print(summary.to_string(float_format=lambda x: f"{x:.4f}"))

# ===== 시간 추이: 이동평균/누적 CTR =====
# 1) 누적 CTR
df["cum_exposure"] = df.groupby("arm").cumcount() + 1
df["cum_reward"]   = df.groupby("arm")["reward"].cumsum()
df["cum_ctr"]      = df["cum_reward"] / df["cum_exposure"]

# 2) 이동평균 CTR (최근 20 이벤트 기준)
window = 20
df["ma_ctr"] = (
    df.groupby("arm")["reward"]
      .rolling(window=window, min_periods=1)
      .mean()
      .reset_index(level=0, drop=True)
)

# ===== 플롯 1: 누적 CTR =====
plt.figure(figsize=(9,5))
for arm, g in df.groupby("arm"):
    plt.plot(g["ts"], g["cum_ctr"], label=f"{arm} (cum)")
plt.title("Cumulative CTR by arm")
plt.xlabel("time")
plt.ylabel("cumulative CTR")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# ===== 플롯 2: 이동평균 CTR =====
plt.figure(figsize=(9,5))
for arm, g in df.groupby("arm"):
    plt.plot(g["ts"], g["ma_ctr"], label=f"{arm} (MA{window})")
plt.title(f"Moving-average CTR by arm (window={window})")
plt.xlabel("time")
plt.ylabel("moving-average CTR")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# ===== 요약 저장(선택) =====
out_csv = "analysis/arm_summary.csv"
os.makedirs("analysis", exist_ok=True)
summary.to_csv(out_csv)
print(f"[OK] arm summary saved → {out_csv}")
