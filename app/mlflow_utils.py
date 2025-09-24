import mlflow, time
from .config import MLFLOW_TRACKING_URI, MLFLOW_EXPERIMENT

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow.set_experiment(MLFLOW_EXPERIMENT)

def log_online_event(arm: str, reward: float, meta: dict | None = None, samples: dict | None = None):
    with mlflow.start_run(run_name=f"{arm}_{int(time.time())}", nested=False):
        mlflow.log_param("arm", arm)
        mlflow.log_metric("reward", reward)
        if samples:
            for k, v in samples.items():
                mlflow.log_metric(f"sample_{k}", float(v))
        if meta:
            for k, v in meta.items():
                if isinstance(v, (int, float)):
                    mlflow.log_metric(str(k), float(v))
                else:
                    mlflow.set_tag(str(k), str(v))
