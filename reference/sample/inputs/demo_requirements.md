# Fashion Retail Analytics - Genie Demo Documentation

## 개요

| **목적** | Fashion Retail Analytics AI Agent Demo using Databricks Genie |
| --- | --- |
| **작성자** | Demo adaptation from KRAFTON POC |
| **작성일자** | 1/25/2026 |
| **Catalog.Schema** | `jongseob_demo.fashion_recommendations` |

---

## 📊 질문 목록 (FAQ)

총 27개 질문이 패션 리테일 도메인으로 변환되어 있습니다:

### 구체적인 질문 (1-20)

#### KPI & Sales Analysis
1. 지난 주 가장 많이 팔린 제품은 무엇인가요?
2. 어떤 카테고리가 가장 높은 매출을 기록했나요?
3. 전체 플랫폼에서 반응이 가장 좋은 브랜드는 무엇인가요?
4. 지금 가장 인기있는 제품 트렌드는 무엇인가요?
5. 고객 리뷰에서 평점이 가장 높은 제품은 무엇인가요?
6. 최근 24시간 동안 가장 많이 구매된 상품은 무엇인가요?
7. 어떤 고객 세그먼트가 가장 활발한가요?
8. 시간대별로 구매량이 가장 많은 시간은 언제인가요?

#### Sentiment & Trend Analysis
9. 긍정/부정 리뷰 동향이 있었는데, 반응이 많은 상세 내용을 요약해서 추출해줘
10. 부정 리뷰의 주요 키워드는 무엇인가요?
11. 고객 평점에서 부정 리뷰가 급증한 시점과 주요 불만 사항은 무엇인가요?
12. 온라인과 오프라인에서 긍정/부정 비율은 어떻게 다른가요?

#### Cross-Analysis
13. 브랜드별로 고객 반응을 비교해주세요
14. 카테고리별로 판매 트렌드를 비교해주세요
15. 프로모션 전후 판매량 변화는 어떻게 되나요?
16. 이 시간대에 어떤 제품이 많이 팔렸는지 시간 순서대로 보여줘
17. 이 시점에 고객들은 무슨 제품을 구매했나?
18. 매출이 특정 시점에 급증했는데, 그때 어떤 제품이 인기였나?
19. 지역별로 구매 패턴 차이는 어떻게 되나요?
20. 마케팅 캠페인별 매출 성과는 어떻게 되나요?

### 광범위한 탐색 질문 (21-27)
21. 그래서 우리 고객들은 우리 제품에 대해서 뭐라고 말하고 있어?
22. 최근 우리 제품에 대한 고객들의 반응은 어때?
23. 온라인과 오프라인에서 우리 제품에 대해 어떤 얘기들이 오가고 있어?
24. 고객들이 우리 제품에 대해 가장 많이 언급하는 것은 뭐야?
25. 전반적으로 우리 브랜드에 대한 분위기는 어떤가요?
26. 고객들이 우리 제품에 대해 좋아하는 것과 불만인 것은 뭐야?
27. 최근 일주일 동안 고객 반응의 주요 변화는 뭐야?

---

## 📈 Daily Sales Summary

**Table:** `jongseob_demo.fashion_recommendations.transactions`

**Related KPI:** Daily Sales, Revenue, Customer Count, ARPU

**Sample Query:**
```sql
SELECT t.t_dat as transaction_date
      ,a.product_type_name
      ,a.product_group_name
      ,COUNT(DISTINCT t.transaction_id) as daily_transactions
      ,SUM(t.price)::decimal(38,2) as daily_revenue
      ,try_divide(SUM(t.price), COUNT(DISTINCT t.customer_id))::decimal(38,2) as arpu
      ,try_divide(SUM(t.price), COUNT(DISTINCT t.transaction_id))::decimal(38,2) as avg_transaction_value
      ,COUNT(DISTINCT t.customer_id) as active_customers
  FROM jongseob_demo.fashion_recommendations.transactions t
       LEFT JOIN jongseob_demo.fashion_recommendations.articles a
       ON t.article_id = a.article_id
       LEFT JOIN jongseob_demo.fashion_recommendations.customer_demographics d
       ON t.customer_id = d.customer_id
       LEFT JOIN jongseob_demo.fashion_recommendations.customers c
       ON t.customer_id = c.customer_id
 GROUP BY ALL
```

---

## 📅 Weekly Sales Summary

**Table:** `jongseob_demo.fashion_recommendations.time_series_sales`

**Related KPI:** Weekly Revenue, Weekly Active Customers, Weekly ARPU

**Remark:** week_start_day 지정 필요 (월요일 시작 = 1)

**Sample Query:**
```sql
SELECT DATE_TRUNC('week', ts.date) as week_start
      ,DATE_ADD(DATE_TRUNC('week', ts.date), 6) as week_end
      ,SUM(ts.num_transactions) as weekly_transactions
      ,SUM(ts.total_revenue)::decimal(38,2) as weekly_revenue
      ,try_divide(SUM(ts.total_revenue), SUM(ts.unique_customers))::decimal(38,2) as weekly_arpu
      ,SUM(ts.unique_customers) as weekly_active_customers
  FROM jongseob_demo.fashion_recommendations.time_series_sales ts
 WHERE DAYOFWEEK(ts.date) = 2  -- Monday start
 GROUP BY ALL
```

---

## 📆 Monthly Sales Summary

**Table:** `jongseob_demo.fashion_recommendations.product_sales_summary`

**Related KPI:** Monthly Revenue, Monthly Active Customers, Monthly ARPU

**Remark:** Month To Date 집계가 가능한 형태의 테이블

**Sample Query:**
```sql
SELECT DATE_TRUNC('month', ps.last_purchase_date) as month_start
      ,LAST_DAY(ps.last_purchase_date) as month_end
      ,ps.product_type_name as category
      ,SUM(ps.num_transactions) as monthly_units_sold
      ,SUM(ps.total_revenue)::decimal(38,2) as monthly_revenue
      ,try_divide(SUM(ps.total_revenue), COUNT(DISTINCT t.customer_id))::decimal(38,2) as monthly_arpu
      ,COUNT(DISTINCT t.customer_id) as monthly_active_customers
  FROM jongseob_demo.fashion_recommendations.product_sales_summary ps
       LEFT JOIN jongseob_demo.fashion_recommendations.transactions t
       ON ps.article_id = t.article_id
 WHERE ps.last_purchase_date = LAST_DAY(ps.last_purchase_date)  -- remove this for Month To Date
 GROUP BY ALL
```

---

## 👥 Customer Retention

**Table:** `jongseob_demo.fashion_recommendations.customers`

**Related KPI:** D+N Retention (N in 7, 14, 30, 90)

**Remark:** Customer Segment 별 리텐션 집계가 가능한 형태

**Sample Query:**
```sql
WITH customer_cohorts AS (
  SELECT customer_id
        ,MIN(first_purchase_date) as cohort_date
    FROM jongseob_demo.fashion_recommendations.customer_demographics
   GROUP BY customer_id
),
retention_calc AS (
  SELECT c.cohort_date
        ,t.t_dat as transaction_date
        ,DATEDIFF(t.t_dat, c.cohort_date) as days_since_first
        ,COUNT(DISTINCT t.customer_id) as retained_customers
        ,COUNT(DISTINCT c.customer_id) as cohort_size
    FROM customer_cohorts c
         LEFT JOIN jongseob_demo.fashion_recommendations.transactions t
         ON c.customer_id = t.customer_id
   GROUP BY ALL
)
SELECT cohort_date
      ,days_since_first
      ,try_divide(retained_customers, cohort_size)::decimal(38,2) as retention_rate
      ,cohort_size
  FROM retention_calc
 WHERE days_since_first IN (7, 14, 30, 90)
 GROUP BY ALL
```

---

## 🛍️ Product Category Performance

**Table:** `jongseob_demo.fashion_recommendations.category_insights`

**Related KPI:**
- sales_volume: 카테고리별 판매량
- avg_rating: 평균 평점
- return_rate: 반품률

**Sample Query:**
```sql
SELECT ci.category
      ,ci.subcategory
      ,ps.product_name
      ,SUM(ci.sales_volume) as total_units_sold
      ,AVG(ci.avg_rating)::decimal(38,2) as average_rating
      ,try_divide(SUM(ci.return_rate), SUM(ci.sales_volume))::decimal(38,4) as return_rate_pct
  FROM jongseob_demo.fashion_recommendations.category_insights ci
       LEFT JOIN jongseob_demo.fashion_recommendations.product_sales_summary ps
       ON ci.category = ps.category
 GROUP BY ALL
 ORDER BY total_units_sold DESC
```

---

## 🗂️ 테이블 정보 (ERD)

### Core Transaction Tables

#### 주요 테이블
- `transactions`: 고객 구매 트랜잭션
- `time_series_sales`: 시계열 판매 데이터
- `customers`: 고객 기본 정보
- `customer_demographics`: 고객 인구통계
- `articles`: 제품 카탈로그
- `product_sales_summary`: 제품별 판매 요약
- `category_insights`: 카테고리별 인사이트

#### 주요 조인 관계
```
customers.customer_id = transactions.customer_id (1:N)
customers.customer_id = customer_demographics.customer_id (1:1)
articles.article_id = transactions.article_id (1:N)
product_sales_summary.product_id = articles.article_id (1:1)
category_insights.category = articles.product_category (1:N)
```

#### 주요 컬럼
- **고객 식별**: `customer_id`
- **시간 정보**: `t_dat` (DATE), `sale_date` (DATE)
- **제품 정보**: `article_id`, `product_type_name`, `product_group_name`, `colour`
- **인구통계 정보**: `age_group`, `gender`

---


## 🗃️ Meta Tables

### Customer Demographics
**Table:** `jongseob_demo.fashion_recommendations.customer_demographics`

**Join Key:** `customer_id`

**Key Columns:**
- `age_group`: 연령대 (18-24, 25-34, 35-44, 45-54, 55+)
- `gender`: 성별

---

### Product Catalog
**Table:** `jongseob_demo.fashion_recommendations.articles`

**Join Key:** `article_id`

**Key Columns:**
- `product_type_name`: 제품 타입 (Trousers, Sweater, Dress, etc.)
- `product_group_name`: 제품 그룹 (Garment Upper body, Garment Lower body, Shoes, etc.)
- `colour`: 색상
- `product_name`: 제품명

---

## 📊 Common Filters & Dimensions

### Filters
```sql
-- 날짜 필터
WHERE t_dat >= '2024-01-01'
WHERE sale_date >= CURRENT_DATE - 30

-- 제품 타입 필터
WHERE product_type_name IN ('Trousers', 'Sweater', 'Dress')

-- 제품 그룹 필터
WHERE product_group_name IN ('Garment Upper body', 'Garment Lower body', 'Shoes')
```

### Key Dimensions
- **t_dat / sale_date**: 거래/판매 일자
- **product_type_name**: 제품 타입 (상세 카테고리)
- **product_group_name**: 제품 그룹 (대분류)
- **sales_channel**: 판매 채널 (online, offline)

---

## 📋 Table Mapping for Business Questions

### KPI 수치형 질문별 테이블 매핑

| Question | Primary Table | Join Tables | Key Metrics |
|----------|--------------|-------------|-------------|
| 일일 매출은? | transactions | articles | daily_revenue, transaction_count |
| 주간 활성 고객은? | time_series_sales | - | weekly_active_customers |
| 카테고리별 성과는? | category_insights | product_sales_summary | sales_volume, avg_rating |
| 고객별 ARPU는? | transactions | customers | revenue / customer_count |
| 리텐션은? | customers | transactions | retention_rate |

---

### 내용 정리형 질문별 테이블 매핑

| Question | Primary Table | Analysis Type |
|----------|--------------|---------------|
| 인기 제품 트렌드는? | product_sales_summary | Ranking + Trend |
| 부정 리뷰 키워드는? | category_insights | Sentiment + Text |
| 제품 타입별 차이는? | articles + transactions | Category Analysis |
| 프로모션 효과는? | transactions + time_series_sales | Before/After |

---

## 🔗 Table Relationships (ERD)
```
┌─────────────────────┐
│     customers       │
│  • customer_id (PK) │
│  • first_purchase   │
└──────────┬──────────┘
           │ 1:1
           ↓
┌─────────────────────┐
│customer_demographics│
│  • customer_id (FK) │
│  • age_group        │
│  • gender           │
└─────────────────────┘

┌─────────────────────┐
│     articles        │
│  • article_id (PK)  │
│  • product_type_name│
│  • product_group    │
│  • colour           │
│  • product_name     │
└──────────┬──────────┘
           │ 1:N
           ↓
┌─────────────────────┐        ┌─────────────────────┐
│    transactions     │◄───────│  time_series_sales  │
│  • transaction_id   │  1:1   │  • sale_date        │
│  • customer_id (FK) │        │  • product_type_name│
│  • article_id (FK)  │        │  • revenue          │
│  • t_dat            │        │  • quantity_sold    │
│  • price            │        └─────────────────────┘
└─────────────────────┘

┌─────────────────────┐        ┌─────────────────────┐
│product_sales_summary│        │  category_insights  │
│  • product_id       │        │  • category         │
│  • category         │◄───────│  • subcategory      │
│  • total_revenue    │  N:1   │  • sales_volume     │
│  • total_quantity   │        │  • avg_rating       │
└─────────────────────┘        │  • return_rate      │
                               └─────────────────────┘
```

---

## 💡 Business Scenarios for Demo

### Revenue Analysis
1. **매출 급증 분석**: "지난주 매출이 급증했는데, 어떤 제품이 견인했나요?"
   - Tables: `transactions`, `articles`, `product_sales_summary`
   - Metrics: daily_revenue, product_type_name, sales_count

2. **카테고리 성과**: "어떤 카테고리가 가장 수익성이 높나요?"
   - Tables: `category_insights`, `product_sales_summary`
   - Metrics: revenue, sales_volume, return_rate

### Customer Analysis
3. **고객별 분석**: "특정 고객의 구매 패턴은?"
   - Tables: `customers`, `transactions`, `customer_demographics`
   - Metrics: purchase_frequency, ARPU

4. **리텐션 변화**: "신규 고객의 30일 리텐션이 개선됐나요?"
   - Tables: `customers`, `transactions`
   - Metrics: retention_rate, cohort_analysis

### Product Performance
5. **제품 트렌드**: "지난 분기 대비 인기 제품 변화는?"
   - Tables: `product_sales_summary`, `time_series_sales`
   - Metrics: QoQ growth, trending products

6. **부정 피드백**: "반품률이 높은 제품과 주요 이슈는?"
   - Tables: `category_insights`, `articles`
   - Metrics: return_rate, avg_rating

### Demographic Analysis
7. **인구통계별 선호도**: "연령대별로 고객들이 선호하는 제품 타입은?"
   - Tables: `customer_demographics`, `transactions`, `articles`
   - Metrics: age_group_sales, product_preference

---

## 🔍 Key Metrics Definitions

| Metric | Formula | Description |
|--------|---------|-------------|
| ARPU | Revenue / Active Customers | Average Revenue Per User |
| Retention Rate | Retained / Cohort Size | % of customers who return |
| Purchase Frequency | Transactions / Customers | Avg purchases per customer |
| Return Rate | Returns / Sales | % of products returned |
| AOV | Revenue / Transactions | Average Order Value |
