from fastapi import FastAPI
from .schemas import ChooseRequest, ChooseResponse, UpdateRequest
from .bandit import ThompsonBandit
from .mlflow_utils import log_online_event
from . import config
import variants.variant_a as A
import variants.variant_b as B
from typing import Dict

ARMS = {"A": A.serve, "B": B.serve}
bandit = ThompsonBandit(list(ARMS.keys()), discount=config.DISCOUNT)

app = FastAPI(title="MAB+MLflow Online API")

@app.get("/health")
def health():
    return {"status":"ok","arms":list(ARMS.keys())}

@app.post("/choose", response_model=ChooseResponse)
def choose(req: ChooseRequest):
    arm, samples = bandit.choose()
    items = ARMS[arm](req.user_id, req.context)
    resp = {"arm": arm, "items": items, "debug": {"samples": samples}}
    return resp

@app.post("/update")
def update(req: UpdateRequest):
    bandit.update(req.arm, req.reward)
    log_online_event(arm=req.arm, reward=req.reward, meta=req.meta, samples=None)
    return {"ok": True}
