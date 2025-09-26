# ABTEST-STREAMIT-movie

## 개요

Streamlit + FastAPI 기반의 A/B 테스트 및 MAB(Multi-Armed Bandit) 실험 데모 프로젝트입니다.

오프라인 데이터로 주기적인 실험을 수행하고, 실제 사용자 클릭 로그를 받아 MLflow에 기록하여 A/B 테스트와 MAB의 최적화 추이를 비교 및 시각화합니다.

## 폴더 구조

```
app/                 # FastAPI 기반의 API
client/              # Streamlit 사용자 UI
analysis/            # 오프라인 분석 스크립트
offline/             # 데이터 및 시뮬레이션 관련 파일
variants/            # A/B 테스트 및 MAB 전략 정의
docker/              # Docker 관련 파일 (선택 사항)
.env.example         # 환경 변수 템플릿
requirements.txt     # Python 의존성 목록
pipeline.txt         # 파이프라인 아이디어 메모
mlflow.db           # MLflow SQLite 백엔드 DB
```

## 목표

- 데이터 주기 수집 및 적재 기반으로 A/B 테스트와 MAB 모두를 구동했을 때의 성능 추이 그래프 제공
- **실제 사용자 입력(클릭/선호)**을 받는 Streamlit 사용자 앱 제공
- 관리자 대시보드에서 로그, 실시간 성능, 분석 그래프를 포함하고 MLflow 연동을 통해 실험 거버넌스 확보

## 전체 아키텍처 (데이터 흐름)

```
┌──────────────────────────┐
│     사용자 / 브라우저    │
│   (Streamlit Frontend)   │
└─────────────┬────────────┘
              │  ① /choose (user_id, context)
              ▼
      ┌───────────────┐
      │  Policy API   │  FastAPI
      │(MAB Controller│—Thompson/UCB)
      └──────┬────────┘
             │  ② arm 선택
   ┌─────────┴───────────┐
   ▼                     ▼
┌───────┐            ┌────────┐
│Variant│ A          │Variant │ B       ... (팔 확장)
│(전략) │            │(전략)  │
└───┬───┘            └───┬────┘
    │  ③ 결과(아이템 목록)    │
    └───────────┬─────────────┘
                ▼
      ┌───────────────────┐
      │  Streamlit UI     │  ④ 노출 & 사용자 선택
      └─────────┬─────────┘
                │  ⑤ /update (arm, reward, meta)
                ▼
      ┌───────────────────┐
      │  Policy API       │  ⑥ α/β 업데이트
      │  + MLflow Logging │  ⑦ run 기록(arm, reward, etc.)
      └───────────────────┘

(오프라인 분석)
Streamlit/사용자 이벤트 → MLflow 로그 → analysis 스크립트/대시보드에서
arm별 CTR/트래픽/추이 집계 및 시각화
```

## 시퀀스 다이어그램

```
사용자      UI(Streamlit)      Policy(MAB)           Variant A/B         MLflow
  |              |                  |                    |                 |
  |  클릭        |                  |                    |                 |
  |------------> | /choose          |                    |                 |
  |              |----------------->| choose()           |                 |
  |              |                  | arm 샘플링         |                 |
  |              |                  | ----call---------> | serve()         |
  |              |                  | <---items----------|                 |
  |              |<-----------------| items + arm        |                 |
  |  목록 노출    |                  |                    |                 |
  |  항목 선택    |                  |                    |                 |
  |------------> | /update          |                    |                 |
  |              |----------------->| update(arm,reward) |                 |
  |              |                  | α/β 갱신           |                 |
  |              |                  | --------log------->| run 저장        |
  |              |<-----------------| {ok}               |                 |
```

## 컴포넌트 / 배포 구성

### Dev Laptop / Server
- **Streamlit 사용자 앱**: `client/` (기본 8501)
- **FastAPI Policy API**: `app/` (기본 8000)
- **MLflow Server**: 로컬 UI (기본 5000) / 백엔드: `mlflow.db` (SQLite)
- **데이터**: `data/` + `offline/` (샘플/시뮬레이션 데이터)
- **분석 대시보드**: `analysis/`
- **환경 변수**: `.env.example`로 환경 변수 스켈레톤 제공, `requirements.txt` 포함

### 확장 옵션
- **Docker Compose**로 API, UI, MLflow 컨테이너 분리
- **Kubernetes**: bandit-policy(Deployment), variants(Deployment), MLflow(Service)
- **모니터링**: MLflow (실험), Prometheus/Grafana (시스템), Loki (로그)

## 사용자/관리자 앱 구성

### 1) 사용자 Streamlit (Frontend)
- **실제 앱 같은 디자인**: 카드 UI, 아이콘, 최소 색 구성
- **목록 노출 & 클릭**: 추천 목록을 보여주고, 클릭 이벤트만 전송 (내부 로그/그래프는 비노출)
- **API 통신**: `GET /choose`로 추천 목록 요청, `POST /update`로 클릭 이벤트 전달

### 2) 관리자 Streamlit (Backend)
- **실시간 성능**: A/B vs MAB 성능 추이 (CTR, 누적 보상, 트래픽 비율)
- **팔(Variant)별 분포**: 톰슨 샘플링의 베타 분포 또는 UCB의 평균/불확실성 곡선
- **로그 & 분석**: 실시간 로그 테이블, 최근 세션, 사용자 세그먼트별 성과
- **MLflow 연동**: 실험, 런, 메트릭 그래프를 연동하여 주기성 트렌드(일/주/월) 분석

## 데이터 전략

### 데이터 타입 (2종)

#### 오프라인 실험 데이터
- 스케줄러로 주기 처리
- CSV/Parquet 형식으로 누적
- A/B는 50:50 고정, MAB는 실시간 보상으로 동적 트래픽 할당

#### 실사용자 로그
- Streamlit 사용자 앱 클릭 이벤트
- `user_id`, `arm`, `item_id`, `reward(0/1)`, `timestamp`, `context` 정보 포함
- MLflow 및 로컬 DB에 중복 기록 (분석 안정성 확보)

### 공개 데이터 추천
- **MovieLens 100K/1M**: 영화/장르/평점 기반 CTR 시뮬레이션
- **Goodbooks-10k**: 도서 추천 (아이템 수 적당)
- **MIND(News) Small**: 뉴스 CTR (클릭 로그 구조가 적합)

## 파이프라인

1. **데이터 준비**: `offline/`의 시뮬레이션 스크립트를 통해 `data/processed/*.parquet` 파일 생성
2. **전략 정의**: `variants/` 내에 A/B(고정), MAB(Thompson/UCB) 컨트롤러 정의
3. **API**: `app/main.py`
   - `GET /choose?user_id=...` → arm 샘플링 후 추천 목록 반환
   - `POST /update` → 보상 반영 및 MLflow 로깅
4. **사용자 UI**: `client/streamlit_app.py`
   - 카드 UI로 목록 노출 및 클릭 전송
5. **관리자 대시보드**: `client/pages/2_Admin_Dashboard.py`
   - A/B vs MAB 추이, 로그, 세그먼트 그래프 및 MLflow 메트릭 표시
6. **분석/리포팅**: `analysis/`
   - 일/주 단위 집계, 리그레션 분석, 이상 탐지

## 빠른 시작 (로컬)

### 0) 환경 변수 설정
```bash
cp .env.example .env
# 필요시 PORT/API_BASE/MLFLOW_TRACKING_URI/ARTIFACT_PATH 등 설정
```

### 1) 의존성 설치
```bash
pip install -r requirements.txt
```

### 2) MLflow 서버 실행
```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
```

### 3) Policy API (FastAPI) 실행
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 4) Streamlit 실행
```bash
streamlit run client/streamlit_app.py --server.port 8501
```

## 실험 모드

### A) A/B Test
- **트래픽**: A:B = 50:50 (고정)
- **메트릭**: CTR, 누적 클릭, 세션당 보상
- **대시보드**: A/B 성능 비교 라인 차트, 누적 차이(CUSUM)

### B) MAB (Thompson / UCB)
- **트래픽**: 보상 추정이 높은 arm에 동적 할당
- **메트릭**: CTR, 누적 보상, Regret
- **대시보드**: 팔별 베타분포 변화, 평균+상한 추이

## 로그 & MLflow

- **실시간 로깅**: `/update` 수신 시 MLflow `log_metric`, `log_param` 즉시 기록
- **실험 구조**: Experiment는 `abtest_movielens` 등, Run은 일자/세션/전략 조합
- **대시보드**: 로컬 테이블/캐시로 최근 이벤트 확인, MLflow 메트릭(일/주/월) 라인 차트, Variant별 성능 분포 히스토그램/ECDF

## 데이터 주기 (스케줄)

- **오프라인 시뮬**: 1~5분 간격으로 세션 배치 생성
- **실사용자 이벤트**: 실시간 수집
- **집계 잡**: 5~10분 간격으로 CTR/Regret/트래픽 비율 요약 → MLflow 및 로컬 기록
- **중장기 리포팅**: 하루 1회, 주 1회 스냅샷

## 디렉터리 가이드

```
app/                 # FastAPI (choose/update, MAB Controller, logging)
client/
  ├── streamlit_app.py   # 사용자 앱(카드 UI, 클릭 전송)
  └── pages/
      └── 2_Admin_Dashboard.py # 관리자 대시보드(로그+그래프+MLflow)
analysis/            # 오프라인 분석, MLflow 집계 스크립트
offline/             # 시뮬 데이터/제너레이터
variants/            # 전략/모델 정의(A/B, Thompson, UCB)
data/
  └── raw/ processed/  # 오프라인 변환 산출물
docker/              # (선택) compose/k8s 템플릿
mlflow.db            # SQLite 백엔드
.env.example         # 환경 변수 템플릿
requirements.txt     # 파이썬 의존성
pipeline.txt         # 파이프라인 메모
```

## API 사양 (요약)

### GET /choose
**요청**: `GET /choose?user_id=U&context=...`
**응답**: 
```json
{
  "arm": "A"|..., 
  "items": [{"item_id": "...", "title": "...", ...}]
}
```

### POST /update
**바디**: 
```json
{
  "user_id": "...",
  "arm": "...",
  "item_id": "...", 
  "reward": 0|1,
  "ts": "...",
  "meta": {...}
}
```
**효과**: 팔 파라미터 갱신 (Thompson: α/β, UCB: 평균/카운트), MLflow 로깅

## 시각화 (관리자)

- **A/B vs MAB 누적보상/CTR**: 시간 라인 차트
- **베타분포 스냅샷(Thompson)**: 팔별 PDF (선택 시점/애니메이션)
- **세그먼트별 성과**: 장르/카테고리/신작 여부/가격대
- **트래픽 할당 비율**: 스택 영역 차트
- **Regret**: 누적/구간 Regret

## 로드맵

- [ ] Thompson + UCB 컨트롤러 공용 인터페이스 정리
- [ ] Cold-start 최소 노출 보장 (ε-greedy/softmax 혼합)
- [ ] 세그먼트 MAB (컨텍스트 밴딧) 옵션
- [ ] MLflow Model Registry 이용해 router/PolicyA/PolicyB alias 운영
- [ ] Docker Compose 배포 템플릿
- [ ] Kubernetes 예시 Manifests + HPA
- [ ] Prometheus/Grafana/Loki 연동 문서화

## 개발/운영 팁

- **실험 설계**: 오프라인 점수가 높아도 온라인 CTR이 낮을 수 있으니, A/B 테스트를 거쳐 MAB로 확장하는 전략이 좋습니다.
- **로그 일관성**: Streamlit 캐시/세션 상태와 서버 로그가 이중화되도록 설계하여 데이터 유실을 방지합니다.
- **재현성**: MLflow run에 코드 버전, 파라미터, 데이터 스냅샷 경로를 기록해 실험의 재현성을 높입니다.

## 라이선스 / 크레딧

- 내부 코드 및 설정은 본 레포지토리 참조
- 데이터셋 라이선스는 원출처를 반드시 확인 후 사용

## 부록: 실행 체크리스트

1. [ ] `.env` 파일 생성 및 포트/URI 설정
2. [ ] `pip install -r requirements.txt`
3. [ ] `mlflow ui` 기동 (`mlflow.db` 경로 확인)
4. [ ] `uvicorn app.main:app --port 8000`
5. [ ] `streamlit run client/streamlit_app.py --server.port 8501`
6. [ ] 관리자 페이지에서 메트릭 표/그래프 확인 (A/B/MAB 토글)