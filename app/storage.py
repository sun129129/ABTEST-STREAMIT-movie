# 데모에서는 bandit 내부 상태만 사용.
# 추후 Redis/SQLite로 노출/클릭 원시로그를 적재하고 리포트에 활용 가능.
LOGS = []

def append_log(event: dict):
    LOGS.append(event)

def get_logs():
    return LOGS
