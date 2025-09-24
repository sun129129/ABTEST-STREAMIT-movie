import os

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
MLFLOW_EXPERIMENT = os.getenv("MLFLOW_EXPERIMENT", "MAB_Online")
DISCOUNT = float(os.getenv("BANDIT_DISCOUNT", "1.0"))   # 1.0 = 감쇠 없음
MIN_EXPOSURE = int(os.getenv("MIN_EXPOSURE", "5"))      # 가드레일(선택)
MAX_CAP = float(os.getenv("MAX_CAP", "0.9"))            # arm 최대 90% (선택)
