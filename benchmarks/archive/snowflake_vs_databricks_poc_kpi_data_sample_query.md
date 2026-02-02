# [PAT] Snowflake vs Databricks 경쟁 POC 대상 KPI 데이터 20251113

# 개요

| **목적** | Snowflake vs Databricks AI Agent 경쟁 POC 에 활용할 수 있는 테이블 리스트 및 샘플 쿼리 제공 |
| --- | --- |
| **작성자** | @Junghwan Chai (채정환) |
| --- | --- |
| **작성일자** | 1/12/2026 |
| --- | --- |


## Daily KPI Summary

**Table:** `main_dev.krafton_temp.poc_krafton_kpi_kad_ingame_summary_daily`

**Related KPI:** DAU, DARPU, DARPPU, DPUR, Daily Avg. Online Time (mins)

**Sample Query:**
```sql
SELECT L.event_date
      ,L.game_code
      ,R.krafton_region
      ,L.user_type
      ,SUM(L.active_user) as dau
      ,SUM(L.cash_revenue)::decimal(38,2) as daily_ingame_revenue
      ,try_divide(SUM(L.cash_revenue), SUM(L.active_user))::decimal(38,2) as darpu
      ,try_divide(SUM(L.cash_revenue), SUM(L.cash_paying_user))::decimal(38,2) as darppu
      ,try_divide(SUM(L.cash_paying_user), SUM(L.active_user))::decimal(38,2) as dpur
      ,try_divide(SUM(L.online_ts_mins), SUM(L.active_user))::decimal(38,2) as daily_avg_online_ts
  FROM main_dev.krafton_temp.poc_krafton_kpi_kad_ingame_summary_daily L
       LEFT JOIN
       main_dev.krafton_temp.poc_meta_krafton_region R
       ON L.country_code = R.country_code
 GROUP BY ALL
```

---

## Weekly KPI Summary

**Table:** `main_dev.krafton_temp.poc_krafton_kpi_kad_ingame_summary_weekly`

**Related KPI:** WAU, WARPU, WARPPU, WPUR, Weekly Avg. Online Time (mins)

**Remark:** week_start_day 지정 필요

**Sample Query:**
```sql
SELECT L.start_date
      ,L.end_date
      ,L.week_start_day
      ,L.game_code
      ,R.krafton_region
      ,L.user_type
      ,SUM(L.active_user) as wau
      ,SUM(L.cash_revenue)::decimal(38,2) as weekly_ingame_revenue
      ,try_divide(SUM(L.cash_revenue), SUM(L.active_user))::decimal(38,2) as warpu
      ,try_divide(SUM(L.cash_revenue), SUM(L.cash_paying_user))::decimal(38,2) as warppu
      ,try_divide(SUM(L.cash_paying_user), SUM(L.active_user))::decimal(38,2) as wpur
      ,try_divide(SUM(L.online_ts_mins), SUM(L.active_user))::decimal(38,2) as weekly_avg_online_ts
  FROM main_dev.krafton_temp.poc_krafton_kpi_kad_ingame_summary_weekly L
       LEFT JOIN
       main_dev.krafton_temp.poc_meta_krafton_region R
       ON L.country_code = R.country_code
 WHERE L.week_start_day = 2
 GROUP BY ALL
```

---

## Monthly KPI Summary

**Table:** `main_dev.krafton_temp.poc_krafton_kpi_kad_ingame_summary_monthly`

**Related KPI:** MAU, MARPU, MARPPU, MPUR, Monthly Avg. Online Time (mins)

**Remark:** Month To Date KPI 집계가 가능한 형태의 테이블

**Sample Query:**
```sql
SELECT L.start_date
      ,L.end_date
      ,L.game_code
      ,R.krafton_region
      ,L.user_type
      ,SUM(L.active_user) as mau
      ,SUM(L.cash_revenue)::decimal(38,2) as monthly_ingame_revenue
      ,try_divide(SUM(L.cash_revenue), SUM(L.active_user))::decimal(38,2) as marpu
      ,try_divide(SUM(L.cash_revenue), SUM(L.cash_paying_user))::decimal(38,2) as marppu
      ,try_divide(SUM(L.cash_paying_user), SUM(L.active_user))::decimal(38,2) as mpur
      ,try_divide(SUM(L.online_ts_mins), SUM(L.active_user))::decimal(38,2) as monthly_avg_online_ts
  FROM main_dev.krafton_temp.poc_krafton_kpi_kad_ingame_summary_monthly L
       LEFT JOIN
       main_dev.krafton_temp.poc_meta_krafton_region R
       ON L.country_code = R.country_code
 WHERE L.end_date = last_day(L.end_date) -- remove this for Month To Date KPI
 GROUP BY ALL
```

---

## Daily Retention

**Table:** `main_dev.krafton_temp.poc_krafton_traffic_kad_retention_daily`

**Related KPI:** D+N Retention (N in 1, 3, 7, 14, 28)

**Remark:** User Type 별 잔존율 집계가 가능한 형태

**Sample Query:**
```sql
SELECT cohort_date
      ,event_date
      ,day_plus
      ,game_code
      ,try_divide(SUM(retained_user), SUM(cohort_size))::decimal(38,2) as retention_rate
      ,SUM(cohort_size) as cohort_size
  FROM main_dev.krafton_temp.poc_krafton_traffic_kad_retention_daily
 WHERE user_type = 'New'
 GROUP BY ALL
```

---

## Daily PUBG GCoin Usage by Product

**Table:** `main_dev.krafton_temp.poc_pubg_economy_gcoin_used_by_product_with_refund_daily`

**Related KPI:**
- unit_sold: 아이템 판매량
- paid_gcoin_used: 유료 재화 사용량
- free_gcoin_used: 무료 재화 사용량

**Remark:** PUBG Only

**Sample Query:**
```sql
SELECT date
      ,L.platform
      ,Rb.category
      ,Rb.sub_category
      ,Rb.event_type
      ,Rb.event_name
      ,Rb.product_name
      ,SUM(unit_sold) as unit_sold
      ,SUM(paid_gcoin_used) as paid_gcoin_used
  FROM main_dev.krafton_temp.poc_pubg_economy_gcoin_used_by_product_with_refund_daily L
       LEFT JOIN
       main_dev.krafton_temp.poc_meta_krafton_region Ra
       ON L.country = Ra.country_code
       LEFT JOIN
       main_dev.krafton_temp.poc_meta_pubg_gcoin_items Rb
       ON L.platform = Rb.platform
       AND L.sales_id = Rb.sales_id
       AND L.product_id = Rb.product_id
 GROUP BY ALL
```

---

## Meta Tables

### KRAFTON Region Meta

**Table:** `main_dev.krafton_temp.poc_meta_krafton_region`

**Join Key:** country_code / country

---

### PUBG GCoin Item Meta

**Table:** `main_dev.krafton_temp.poc_meta_pubg_gcoin_items`

**Remark:** PUBG Only

**Join Key:** platform, sales_id, product_id

