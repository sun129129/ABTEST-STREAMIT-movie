# analysis/dashboard.py
# MLflow 'MAB_Online' 실험을 읽어 arm별 CTR 요약/추이를 시각화하는 Streamlit 대시보드

import os
from datetime import timedelta

import mlflow
import pandas as pd
import streamlit as st

# ===== 설정 =====
MLFLOW_URI_DEFAULT = "http://127.0.0.1:5000"
EXPERIMENT_DEFAULT = "MAB_Online"

st.set_page_config(page_title="MAB + MLflow Dashboard", layout="wide")

st.title("📊 MAB + MLflow Dashboard")
st.caption("arm별 CTR 요약과 시간 추이를 시각화합니다.")

with st.sidebar:
    st.header("⚙️ 설정")
    mlflow_uri = st.text_input("MLflow Tracking URI", os.getenv("MLFLOW_TRACKING_URI", MLFLOW_URI_DEFAULT))
    experiment_name = st.text_input("Experiment name", os.getenv("MAB_EXPERIMENT", EXPERIMENT_DEFAULT))
    time_window_mins = st.number_input("이동평균 창 크기(분)", min_value=1, max_value=240, value=20)
    st.markdown("---")
    st.caption("※ MLflow 서버가 먼저 실행 중이어야 합니다.")

@st.cache_data(show_spinner=True, ttl=30)
def load_runs(mlflow_uri: str, experiment_name: str) -> pd.DataFrame:
    mlflow.set_tracking_uri(mlflow_uri)
    exp = mlflow.get_experiment_by_name(experiment_name)
    if exp is None:
        return pd.DataFrame()
    df = mlflow.search_runs(experiment_ids=[exp.experiment_id], order_by=["start_time ASC"])
    return df

df = load_runs(mlflow_uri, experiment_name)

if df.empty:
    st.warning(f"실험 `{experiment_name}`에서 run을 찾지 못했습니다. Streamlit UI에서 선택 이벤트를 발생시킨 뒤 다시 열어보세요.")
    st.stop()

# 안전 추출
def has(col: str) -> bool: return col in df.columns
required_metrics = ["metrics.reward"]
required_params = ["params.arm"]
if not all(has(c) for c in required_metrics + required_params):
    st.error("필수 컬럼이 부족합니다. /update에서 reward(메트릭), arm(파라미터)을 기록하는지 확인하세요.")
    st.dataframe(df.head(10))
    st.stop()

# 가공
gdf = df[["run_id", "start_time", "metrics.reward", "params.arm"]].copy()
gdf["ts"] = pd.to_datetime(gdf["start_time"], unit="ms", utc=True).dt.tz_convert(None)
gdf.rename(columns={"metrics.reward": "reward", "params.arm": "arm"}, inplace=True)
gdf["reward"] = gdf["reward"].astype(float)

# 사이드바 필터 (기간)
min_ts, max_ts = gdf["ts"].min(), gdf["ts"].max()
start_ts, end_ts = st.sidebar.date_input("기간(시작/끝)", value=(min_ts.date(), max_ts.date()))
# 날짜 필터 반영
mask = (gdf["ts"].dt.date >= start_ts) & (gdf["ts"].dt.date <= end_ts)
gdf = gdf.loc[mask].copy()

# 요약 테이블
summary = (
    gdf.groupby("arm")
       .agg(n_runs=("run_id", "count"),
            ctr=("reward", "mean"))
       .sort_values("ctr", ascending=False)
)
summary["traffic_share"] = summary["n_runs"] / summary["n_runs"].sum()

st.subheader("✅ ARM Summary")
st.dataframe(summary.style.format({"ctr":"{:.3f}", "traffic_share":"{:.2%}"}), use_container_width=True)

# 시간 추이 계산
gdf = gdf.sort_values(["arm","ts"]).copy()
gdf["cum_exposure"] = gdf.groupby("arm").cumcount() + 1
gdf["cum_reward"]   = gdf.groupby("arm")["reward"].cumsum()
gdf["cum_ctr"]      = gdf["cum_reward"] / gdf["cum_exposure"]

# 이동평균: time_window_mins 기준으로 리샘플링(분) 평균
window = f"{time_window_mins}min"
ma_df = (
    gdf.set_index("ts")
       .groupby("arm")["reward"]
       .rolling(window=window).mean()
       .reset_index()
       .rename(columns={"reward":"ma_ctr"})
)

# 시각화
import altair as alt

st.subheader("📈 누적 CTR (Cumulative CTR)")
cum_chart = alt.Chart(gdf).mark_line().encode(
    x='ts:T', y='cum_ctr:Q', color='arm:N'
).properties(height=300)
st.altair_chart(cum_chart, use_container_width=True)

st.subheader(f"📈 이동평균 CTR (window={time_window_mins}분)")
ma_chart = alt.Chart(ma_df).mark_line().encode(
    x='ts:T', y='ma_ctr:Q', color='arm:N'
).properties(height=300)
st.altair_chart(ma_chart, use_container_width=True)

st.subheader("🧾 최근 이벤트")
st.dataframe(
    gdf.sort_values("ts", ascending=False)[["ts","arm","reward"]].head(30),
    use_container_width=True
)

st.caption("Tip: 이동평균 창 크기를 조절하며 수렴 상황을 확인해 보세요.")
