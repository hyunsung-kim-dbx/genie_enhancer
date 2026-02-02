# PAT Snowflake vs Databricks AI Agent 경쟁 POC

| 항목 | 내용 |
|------|------|
| **작성자** | Junghwan Chai (채정환) |
| **작성일자** | 2026년 1월 12일 |
| **목적** | Snowflake vs Databricks AI Agent 경쟁 POC에 활용할 수 있는 테이블 리스트 및 샘플 쿼리 제공 |

---

## 개요

### 배경

- Snowflake / Databricks를 통해 KPI와 소셜 데이터를 연계한 분석을 AI Agent를 통해 진행하는 시나리오
- Social 데이터의 범위에 맞춰 대상 게임은 **PUBG**와 **inZOI**로 진행 예정
- Databricks → Snowflake의 데이터 싱크는 **Delta Direct**를 통해 진행
  - 다만, ChangeDataFeed 및 deletionVector 옵션은 활용할 수 없음
  - → 대상 테이블을 바로 활용하는게 아닌 LDP를 통해 대상 게임에 대한 **Materialized View** (CDF와 deletionVector 옵션 X)를 생성하여 이를 제공

---

## Business Questions 예시

### PUBG 관련 질문

1. **PUBG 매출이 특정 기간에 많이 증가했는데, 왜 그런지 분석해줘**
   - 소셜 반응은 어떤지
   - 어떤 상품이 매출을 견인했는지

2. **PUBG 업데이트 이후 리텐션에 변화가 있는지?**

3. **MAU 등 주요 KPI가 작년 동기간 대비 어떤지?**

4. **PUBG PGC 상품에 대한 국가별 반응**
   - PGC란게 무엇인지 우리가 알려주지 않아도 AI가 직접 검색해서 이에 대한 컨텍스트를 유추할 수 있는가?

5. **트래픽이 별다른 이유 없이 빠지고 있는 상황에 대한 분석**
   - 시즈널 이펙트인지, 외부 요인인지, 특정 지역만이면 그 지역의 특별한 이슈가 있었는지 (정치적 사회적 등)

6. **PUBGM과 PUBG에 대한 질문을 구분할 수 있는지?**

### inZOI 관련 질문

1. **inZOI 업데이트에 대한 소셜 반응은 어떤지**
   - 내부 업데이트 캘린더가 없는 상황에서도 AI가 소셜 데이터 혹은 검색 등을 통해 파악할 수 있는지

---

## 평가 시나리오

### 평가 방식

1. **POC를 위해 제공된 데이터셋으로 분석할 수 있는 주제 선정**
   - 주제는 가설 설정이 되어 있는 질문, 동향에 따른 추적 분석 등 실제 비지니스 시나리오를 가정하여 다양한 케이스 선정
     - 예시: 트래픽/매출 트랜드 질의 후 이상 동향에 대한 분석, 특정 상품군의 판매량 부진 요인에 대한 분석 등
   - 제공된 데이터셋에 없는 정보는 웹 서치로 커버 가능한 정보로 한정하여 선정
     - 예시: PGC가 무엇인지, 경기 결과가 어땠는지 등
   - 선정한 분석 주제는 Snowflake와 Databricks 평가시 동일하게 사용

2. **챗봇을 통한 분석 평가**
   - 질문 의도에 맞는 데이터셋과 지표를 선택하는지
   - 쿼리는 정확한지
   - 에이전트가 접근 가능한 데이터셋의 한계를 인식하는지
     - 웹 서치가 필요한 영역이라면 적절히 이를 활용하는지
   - 피드백을 제대로 반영하는지
   - 대화 내용을 분석 리포트로 요약했을 때의 완성도

3. **AI Agent 구현 난이도 평가**
   - 업체 교육 + 직접 Semantic Layer와 Agent 구축해보기

---

### 평가 배점 기준

| 평가 항목 | 배점 | 세부 항목 |
|-----------|------|-----------|
| **답변 및 분석 품질 (정량 평가)** | 60% | 질의 이해 정확도, SQL 정확도, 결과 신뢰도 |
| **구축 난이도 (정량 평가)** | 20% | Semantic Layer, Agent |
| **사용자 경험 (정성 평가)** | 20% | Agent를 통한 분석 경험에 대한 평가, Agent 구축 경험에 대한 평가 |

---

## POC 대상 테이블

### 중요 사항

> **Snowflake에 Delta Direct로 연동하는 테이블은 새로운 데이터 업데이트 중**
> - Schedule: at 11, 14 PM KST

> **Databricks 대상 테이블은 Sandbox 환경에 구축되어 전달될 예정**

> **소셜 테이블은 별도 문서로 제공 예정**

### Snowflake POC Workflow

#### Common Filters

```
game_code IN ('bro', 'inzoi', 'pubgm')
event_date / end_date >= '20240101'
```

#### Key Dimensions

| 컬럼명 | 설명 |
|--------|------|
| `event_date` / `end_date` / `date` | 기준 일자 |
| `device` | 플랫폼 대분류: PC / CONSOLE / MOBILE |
| `platform` | 플랫폼 중분류: STEAM / KAKAO / EPIC / XBOX / PSN |
| `country_code` / `country` / `country_code_store` | 국가 코드 (ISO 3166-1 alpha-2) |
| `user_type` | 유저 구분 (접속 기록 기반) |

**User Type 분류:**
- **New**: 신규
- **Return**: 복귀 (14일 이상 이탈했다 복귀한 유저)
- **Exist**: 기존 유저

---

### KPI 테이블 상세

#### 1. Daily KPI Summary

| 항목 | 내용 |
|------|------|
| **테이블** | `main_dev.krafton_temp.poc_krafton_kpi_kad_ingame_summary_daily` |
| **S3 경로** | `s3://bifrost-silver-us-east-1/__unitystorage/schemas/6d2eb991-415e-46b7-8012-2f632ddec269/tables/35ebbb23-78d2-4717-a650-6a289864306a` |
| **관련 KPI** | DAU, DARPU, DARPPU, DPUR, Daily Avg. Online Time (mins) |

**Sample Query:**

```sql
SELECT 
    L.event_date,
    L.game_code,
    R.krafton_region,
    L.user_type,
    SUM(L.active_user) as dau,
    SUM(L.cash_revenue)::decimal as revenue,
    try_divide(SUM(L.cash_revenue), SUM(L.active_user)) as darpu,
    try_divide(SUM(L.cash_revenue), SUM(L.cash_paying_user)) as darppu,
    try_divide(SUM(L.cash_paying_user), SUM(L.active_user)) as dpur,
    try_divide(SUM(L.online_ts_sum), SUM(L.active_user)) as avg_online_time
FROM main_dev.krafton_temp.poc_krafton_kpi_kad_ingame_summary_daily L
LEFT JOIN main_dev.krafton_temp.poc_meta_krafton_region R
    ON L.country_code = R.country_code
GROUP BY ALL
```

---

#### 2. Weekly KPI Summary

| 항목 | 내용 |
|------|------|
| **테이블** | `main_dev.krafton_temp.poc_krafton_kpi_kad_ingame_summary_weekly` |
| **S3 경로** | `s3://bifrost-silver-us-east-1/__unitystorage/schemas/6d2eb991-415e-46b7-8012-2f632ddec269/tables/2d48b522-b71a-4f36-9028-ca713ecdca20` |
| **관련 KPI** | WAU, WARPU, WARPPU, WPUR, Weekly Avg. Online Time (mins) |
| **비고** | `week_start_day` 지정 필요 |

**Sample Query:**

```sql
SELECT 
    L.start_date,
    L.end_date,
    L.week_start_day,
    L.game_code,
    R.krafton_region,
    L.user_type,
    SUM(L.active_user) as wau,
    SUM(L.cash_revenue)::decimal as revenue,
    try_divide(SUM(L.cash_revenue), SUM(L.active_user)) as warpu,
    try_divide(SUM(L.cash_revenue), SUM(L.cash_paying_user)) as warppu,
    try_divide(SUM(L.cash_paying_user), SUM(L.active_user)) as wpur,
    try_divide(SUM(L.online_ts_sum), SUM(L.active_user)) as avg_online_time
FROM main_dev.krafton_temp.poc_krafton_kpi_kad_ingame_summary_weekly L
LEFT JOIN main_dev.krafton_temp.poc_meta_krafton_region R
    ON L.country_code = R.country_code
WHERE L.week_start_day = 2
GROUP BY ALL
```

---

#### 3. Monthly KPI Summary

| 항목 | 내용 |
|------|------|
| **테이블** | `main_dev.krafton_temp.poc_krafton_kpi_kad_ingame_summary_monthly` |
| **S3 경로** | `s3://bifrost-silver-us-east-1/__unitystorage/schemas/6d2eb991-415e-46b7-8012-2f632ddec269/tables/e1926bb5-9d9c-42ba-8226-24f0dc411e6c` |
| **관련 KPI** | MAU, MARPU, MARPPU, MPUR, Monthly Avg. Online Time (mins) |
| **비고** | Month To Date KPI 집계가 가능한 형태의 테이블 |

**Sample Query:**

```sql
SELECT 
    L.start_date,
    L.end_date,
    L.game_code,
    R.krafton_region,
    L.user_type,
    SUM(L.active_user) as mau,
    SUM(L.cash_revenue)::decimal as revenue,
    try_divide(SUM(L.cash_revenue), SUM(L.active_user)) as marpu,
    try_divide(SUM(L.cash_revenue), SUM(L.cash_paying_user)) as marppu,
    try_divide(SUM(L.cash_paying_user), SUM(L.active_user)) as mpur,
    try_divide(SUM(L.online_ts_sum), SUM(L.active_user)) as avg_online_time
FROM main_dev.krafton_temp.poc_krafton_kpi_kad_ingame_summary_monthly L
LEFT JOIN main_dev.krafton_temp.poc_meta_krafton_region R
    ON L.country_code = R.country_code
WHERE L.end_date = last_day(L.end_date)
GROUP BY ALL
```

---

#### 4. Daily Retention

| 항목 | 내용 |
|------|------|
| **테이블** | `main_dev.krafton_temp.poc_krafton_kpi_kad_ingame_summary_monthly` |
| **S3 경로** | `s3://bifrost-silver-us-east-1/__unitystorage/schemas/6d2eb991-415e-46b7-8012-2f632ddec269/tables/9a5c27dd-6629-4994-b7de-4a66f285c9c8` |
| **관련 KPI** | D+N Retention (N in 1, 3, 7, 14, 28) |
| **비고** | User Type 별 잔존율 집계가 가능한 형태 |

**Sample Query:**

```sql
SELECT 
    cohort_date,
    event_date,
    day_plus,
    game_code,
    try_divide(SUM(retained_user), SUM(cohort_size)) as retention_rate,
    SUM(cohort_size) as cohort_size
FROM main_dev.krafton_temp.poc_krafton_kpi_kad_retention
WHERE user_type = 'New'
GROUP BY ALL
```

---

#### 5. Daily PUBG GCoin Usage by Product

| 항목 | 내용 |
|------|------|
| **테이블** | `main_dev.krafton_temp.poc_pubg_economy_gcoin_used_by_product_with_refund_daily` |
| **S3 경로** | `s3://bifrost-silver-us-east-1/__unitystorage/schemas/6d2eb991-415e-46b7-8012-2f632ddec269/tables/f5692850-73c3-4226-9133-e5e32f05896b` |
| **관련 KPI** | unit_sold (아이템 판매량), paid_gcoin_used (유료 재화 사용량), free_gcoin_used (무료 재화 사용량) |
| **비고** | PUBG Only |

**Sample Query:**

```sql
SELECT 
    date,
    L.platform,
    Rb.category,
    Rb.sub_category,
    Rb.event_type,
    Rb.event_name,
    Rb.product_name,
    SUM(unit_sold) as unit_sold,
    SUM(paid_gcoin_used) as paid_gcoin_used
FROM main_dev.krafton_temp.poc_pubg_economy_gcoin_used_by_product_with_refund_daily L
LEFT JOIN main_dev.krafton_temp.poc_meta_krafton_region Ra
    ON L.country = Ra.country_code
LEFT JOIN main_dev.krafton_temp.poc_meta_pubg_gcoin_items Rb
    ON L.platform = Rb.platform
    AND L.sales_id = Rb.sales_id
    AND L.product_id = Rb.product_id
GROUP BY ALL
```

---

### Meta 테이블

#### KRAFTON Region Meta

| 항목 | 내용 |
|------|------|
| **테이블** | `main_dev.krafton_temp.poc_meta_krafton_region` |
| **S3 경로** | `s3://bifrost-silver-us-east-1/__unitystorage/schemas/6d2eb991-415e-46b7-8012-2f632ddec269/tables/9f6ad05d-6272-48c0-be4c-2647207daa5e` |
| **Join Key** | `country_code` / `country` |

---

#### PUBG GCoin Item Meta

| 항목 | 내용 |
|------|------|
| **테이블** | `main_dev.krafton_temp.poc_meta_pubg_gcoin_items` |
| **S3 경로** | `s3://bifrost-silver-us-east-1/__unitystorage/schemas/6d2eb991-415e-46b7-8012-2f632ddec269/tables/6827743f-25eb-46e4-885c-5e8ed561501a` |
| **Join Key** | `platform`, `sales_id`, `product_id` |
| **비고** | PUBG Only |
