# Snowflake 전달 질문 목록 및 테이블 정보

## Snowflake Social Chatbot PoC - 질문 목록 및 테이블 정보 정리

| 항목 | 내용 |
|------|------|
| **작성일** | 2026-01-13 |
| **프로젝트** | Snowflake Social Chatbot PoC PATT350 |
| **목적** | Snowflake 팀에 전달한 질문 목록, 테이블 정보, 쿼리 정리 |

---

## 📋 목차

1. [질문 목록 (FAQ)](#-질문-목록-faq)
2. [KPI 수치형 질문별 테이블 매핑](#-kpi-수치형-질문별-테이블-매핑)
3. [내용 정리형 질문별 테이블 매핑](#-내용-정리형-질문별-테이블-매핑)
4. [테이블 정보 (ERD)](#-테이블-정보-erd)
5. [자주 쓰는 쿼리](#-자주-쓰는-쿼리)

---

## 📊 질문 목록 (FAQ)

총 **27개 질문**이 정리되어 있으며, 다음과 같이 분류됩니다:

### 구체적인 질문 (1-20)

1. 디스코드에서 리액션이 가장 많은 메시지는 무엇인가요?
2. 스팀 리뷰에서 추천 수가 높은 리뷰는 무엇인가요?
3. 전체 소셜 플랫폼에서 반응이 가장 많은 주제는 무엇인가요?
4. 지금 디스코드에서 가장 핫한 토픽은 무엇인가요?
5. 스팀 커뮤니티에서 댓글이 많이 달린 토픽은 무엇인가요?
6. 최근 24시간 동안 가장 많이 언급된 키워드는 무엇인가요?
7. 디스코드에서 가장 활발한 채널은 어디인가요?
8. 시간대별로 언급량이 가장 많은 시간은 언제인가요?
9. 이런 긍정/부정 동향이 있었는데, 반응이 많은 상세 내용을 요약해서 추출해줘
10. 부정 동향의 주요 키워드는 무엇인가요?
11. 스팀 리뷰에서 부정 리뷰가 급증한 시점과 주요 불만 사항은 무엇인가요?
12. 디스코드와 스팀에서 긍정/부정 비율은 어떻게 다른가요?
13. 게임별로 소셜 반응을 비교해주세요
14. 디스코드와 스팀에서 동시에 언급된 주요 이슈는 무엇인가요?
15. 이벤트 전후 소셜 반응 변화는 어떻게 되나요?
16. 이 시간대에 디스코드와 스팀에서 어떤 소셜 반응이 일어났는지 시간 순서대로 보여줘
17. 이 시점에 디스코드에서 무슨 얘기가 오갔나?
18. KPI가 특정 시점에 트래픽이 많이 뛰었는데, 그때 소셜에서는 어떤 반응이 있었나?
19. 국가별로 반응 속도 차이는 어떻게 되나요?
20. UTM 캠페인별 소셜 반응은 어떻게 되나요? (optional)

### 광범위한 탐색 질문 (21-27)

21. 그래서 우리 게임의 유저들은 우리 게임에 대해서 뭐라고 말하고 있어?
22. 최근 우리 게임에 대한 유저들의 반응은 어때?
23. 디스코드와 스팀에서 우리 게임에 대해 어떤 얘기들이 오가고 있어?
24. 유저들이 우리 게임에 대해 가장 많이 언급하는 것은 뭐야?
25. 소셜에서 우리 게임에 대한 전반적인 분위기는 어떤가요?
26. 유저들이 우리 게임에 대해 좋아하는 것과 불만인 것은 뭐야?
27. 최근 일주일 동안 우리 게임에 대한 유저 반응의 주요 변화는 뭐야?

> **참고:** 모든 질문에 대한 상세한 예시 쿼리는 아래 섹션에서 확인할 수 있습니다.

---

## 📈 KPI 수치형 질문별 테이블 매핑

총 **13개 질문**에 대한 테이블 매핑 및 예시 쿼리가 정리되어 있습니다.

### 주요 질문 목록

각 질문별로 필요한 테이블, 조인 관계, 필터링 조건, 집계 방식, 그리고 완전한 예시 쿼리가 포함되어 있습니다.

1. 디스코드에서 리액션이 가장 많은 메시지는 무엇인가요?
2. 스팀 리뷰에서 추천 수가 높은 리뷰는 무엇인가요?
3. 스팀 커뮤니티에서 댓글이 많이 달린 토픽은 무엇인가요?
4. 디스코드에서 가장 활발한 채널은 어디인가요?
5. 시간대별로 언급량이 가장 많은 시간은 언제인가요?
6. 디스코드와 스팀에서 긍정/부정 비율은 어떻게 다른가요?
7. 게임별로 소셜 반응을 비교해주세요
8. 이벤트 전후 소셜 반응 변화는 어떻게 되나요?
9. 주간/월간 트렌드에서 주요 변화는 무엇인가요?
10. 최근 일주일 동안 소셜 반응의 주요 변화는 무엇인가요?
11. 국가별로 반응 속도 차이는 어떻게 되나요?
12. 트래픽 증가와 소셜 반응의 연관성은 무엇인가요?
13. 위시리스트 변화와 디스코드/스팀 반응의 관계는 어떻게 되나요?

> 각 질문에 대한 상세한 예시 쿼리는 로컬 파일 `snowflake-social-poc/snowflake-qa-summary.md`에서 확인할 수 있습니다.

---

## 📝 내용 정리형 질문별 테이블 매핑

총 **15개 질문**에 대한 테이블 매핑 및 예시 쿼리가 정리되어 있습니다.

### 주요 질문 목록

각 질문별로 필요한 테이블, 조인 관계, 필터링 조건, 집계 방식, 그리고 완전한 예시 쿼리가 포함되어 있습니다.

1. 전체 소셜 플랫폼에서 반응이 가장 많은 주제는 무엇인가요?
2. 지금 디스코드에서 가장 핫한 토픽은 무엇인가요?
3. 최근 24시간 동안 가장 많이 언급된 키워드는 무엇인가요?
4. 이런 긍정/부정 동향이 있었는데, 반응이 많은 상세 내용을 요약해서 추출해줘
5. 부정 동향의 주요 키워드는 무엇인가요?
6. 스팀 리뷰에서 부정 리뷰가 급증한 시점과 주요 불만 사항은 무엇인가요?
7. 디스코드와 스팀에서 동시에 언급된 주요 이슈는 무엇인가요?
8. 이 시간대에 디스코드와 스팀에서 어떤 소셜 반응이 일어났는지 시간 순서대로 보여줘
9. 이 시점에 디스코드에서 무슨 얘기가 오갔나?
10. KPI가 특정 시점에 트래픽이 많이 뛰었는데, 그때 소셜에서는 어떤 반응이 있었나?
11. 지역별로 소셜 반응의 차이는 무엇인가요?
12. 마케팅 캠페인 전후 소셜 반응 변화는 무엇인가요?
13. 오늘 하루 동안 소셜에서 일어난 주요 이슈를 요약해주세요
14. 이번 주 주요 소셜 반응을 플랫폼별로 요약해주세요
15. 디스코드와 스팀의 주요 반응을 통합해서 요약해주세요

---

## 🗂 테이블 정보 (ERD)

### 디스코드 데이터 테이블

#### 주요 테이블

| 테이블명 | 설명 |
|----------|------|
| `main.log_discord.channel_list` | 채널 기본 정보 |
| `main.log_discord.message` | 채널 내 메시지 |
| `main.log_discord.reaction` | 메시지에 대한 이모지 리액션 |
| `main.log_discord.thread_list` | 스레드 채널 정보 |
| `main.log_discord.member_list` | 서버 멤버 정보 |
| `main.log_discord.role_list` | 서버 역할 정보 |

#### 주요 조인 관계

| 조인 | 관계 |
|------|------|
| `channel_list.channel_id = message.channel_id` | 1:N |
| `message.message_id = reaction.message_id` | 1:N |
| `message.message_id = thread_list.parent_message_id` | 1:1 |
| `channel_list.channel_id = thread_list.channel_id` | 1:N |

#### 주요 컬럼

| 컬럼 | 설명 |
|------|------|
| `message.game_code`, `channel_list.game_code` | 게임 코드 |
| `message.created_at` (timestamp), `message.event_date` (DATE) | 시간 정보 |
| `message.content` (또는 `message.message`) | 메시지 내용 |

---

### 스팀 데이터 테이블

#### 주요 테이블

| 테이블명 | 설명 |
|----------|------|
| `main.log_steam.store_appreviews` | 게임 리뷰 데이터 |
| `main.log_steam.community_discussions_topics` | 커뮤니티 토픽 |
| `main.log_steam.community_discussions_comments` | 토픽에 대한 코멘트 |
| `main.log_steam.partner_traffic` | 상점 페이지 트래픽 |
| `main.log_steam.partner_wishlist` | 위시리스트 추가/삭제/구매 데이터 |
| `main.log_steam.steam_app_id` | 앱 ID, 게임 코드, 게임명 매핑 (디멘션 테이블) |
| `main.log_steam.partner_regions_and_countries` | 지역/국가별 위시리스트 및 판매량 |
| `main.log_steam.webapi_ccu` | 게임별 동시 접속자 수 (CCU) |

#### 주요 조인 관계

| 조인 | 관계 | 비고 |
|------|------|------|
| `steam_app_id.app_id = store_appreviews.app_id` | 1:N | 타입 변환 필요: bigint ↔ string |
| `steam_app_id.app_id = community_discussions_topics.app_id` | 1:N | 타입 변환 필요 |
| `community_discussions_topics.url = community_discussions_comments.topic_url` | 1:N | |
| `steam_app_id.app_id = partner_traffic.app_id` | 1:N | string 타입 직접 조인 |
| `steam_app_id.app_id = partner_wishlist.app_id` | 1:N | string 타입 직접 조인 |

#### 주요 컬럼

| 컬럼 | 설명 |
|------|------|
| `steam_app_id.game_code` | 게임 코드 (매핑 테이블 사용) |
| `store_appreviews.timestamp_created` | 시간 정보 (bigint → `FROM_UNIXTIME()` 변환) |
| `store_appreviews.event_date` | DATE |
| `community_discussions_topics.timestamp` | 시간 정보 (bigint → `FROM_UNIXTIME()` 변환) |
| `community_discussions_topics.event_date` | DATE |
| `store_appreviews.review` | 리뷰 내용 |
| `store_appreviews.voted_up` | 감성 정보 (boolean: true/false) |

---

### 게임 코드 매핑

#### 매핑 테이블

**`main.log_steam.steam_app_id`** : Steam App ID ↔ 게임 코드 매핑

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `app_id` | string | Steam App ID |
| `game_code` | string | 게임 코드 |
| `game_name` | string | 게임명 |

#### 사용 예시

```sql
-- 스팀 데이터 필터링
WHERE app_id IN (SELECT app_id FROM steam_app_id WHERE game_code = '게임코드')

-- 디스코드 데이터 필터링
WHERE game_code = '게임코드'
```

---

## 💻 자주 쓰는 쿼리

### 1. 감성 분석 쿼리

#### 디스코드: 긍정/부정/중립 비율 계산

```sql
WITH message_reactions AS (
    SELECT
        m.message_id,
        m.channel_id,
        m.content,
        m.created_at,
        COUNT(DISTINCT r.reaction_id) as reaction_count,
        CASE
            WHEN m.content LIKE '%좋아%' OR m.content LIKE '%최고%' OR m.content LIKE '%사랑%' THEN 'positive'
            WHEN m.content LIKE '%나쁘%' OR m.content LIKE '%별로%' OR m.content LIKE '%불만%' THEN 'negative'
            ELSE 'neutral'
        END as sentiment
    FROM main.log_discord.message m
    LEFT JOIN main.log_discord.reaction r ON m.message_id = r.message_id
    WHERE m.game_code = 'INZOI'
        AND m.event_date >= CURRENT_DATE - 7
    GROUP BY m.message_id, m.channel_id, m.content, m.created_at
)
SELECT
    sentiment,
    COUNT(*) as message_count,
    SUM(reaction_count) as total_reactions,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM message_reactions
GROUP BY sentiment
ORDER BY message_count DESC;
```

#### 스팀: 긍정/부정 리뷰 비율 계산

```sql
SELECT
    CASE
        WHEN voted_up = true THEN 'positive'
        WHEN voted_up = false THEN 'negative'
        ELSE 'unknown'
    END as sentiment,
    COUNT(*) as review_count,
    SUM(votes_up) as total_upvotes,
    AVG(weighted_vote_score) as avg_weighted_score,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM main.log_steam.store_appreviews
WHERE app_id IN (SELECT app_id FROM main.log_steam.steam_app_id WHERE game_code = 'INZOI')
    AND event_date >= CURRENT_DATE - 7
GROUP BY sentiment
ORDER BY review_count DESC;
```

---

### 2. 채널별 활동량 집계 쿼리

#### 일자별 언급량

```sql
SELECT
    DATE(m.created_at) as date,
    c.channel_name,
    COUNT(DISTINCT m.message_id) as message_count,
    COUNT(DISTINCT r.reaction_id) as reaction_count,
    COUNT(DISTINCT m.author_id) as unique_authors
FROM main.log_discord.message m
JOIN main.log_discord.channel_list c ON m.channel_id = c.channel_id
LEFT JOIN main.log_discord.reaction r ON m.message_id = r.message_id
WHERE m.game_code = 'INZOI'
    AND m.event_date >= CURRENT_DATE - 30
GROUP BY DATE(m.created_at), c.channel_name
ORDER BY date DESC, message_count DESC;
```

#### 시간대별 언급량

```sql
SELECT
    HOUR(m.created_at) as hour,
    COUNT(DISTINCT m.message_id) as message_count,
    COUNT(DISTINCT r.reaction_id) as reaction_count
FROM main.log_discord.message m
LEFT JOIN main.log_discord.reaction r ON m.message_id = r.message_id
WHERE m.game_code = 'INZOI'
    AND m.event_date >= CURRENT_DATE - 7
GROUP BY HOUR(m.created_at)
ORDER BY hour;
```

---

### 3. 스팀 리뷰 분석 쿼리

#### 부정 리뷰 급증 감지

```sql
WITH daily_reviews AS (
    SELECT
        DATE(FROM_UNIXTIME(timestamp_created)) as review_date,
        COUNT(*) as total_reviews,
        COUNT(CASE WHEN voted_up = false THEN 1 END) as negative_reviews,
        ROUND(COUNT(CASE WHEN voted_up = false THEN 1 END) * 100.0 / COUNT(*), 2) as negative_ratio
    FROM main.log_steam.store_appreviews
    WHERE app_id IN (SELECT app_id FROM main.log_steam.steam_app_id WHERE game_code = 'INZOI')
        AND event_date >= CURRENT_DATE - 30
    GROUP BY DATE(FROM_UNIXTIME(timestamp_created))
)
SELECT
    review_date,
    total_reviews,
    negative_reviews,
    negative_ratio,
    LAG(negative_ratio) OVER (ORDER BY review_date) as prev_negative_ratio,
    negative_ratio - LAG(negative_ratio) OVER (ORDER BY review_date) as ratio_change
FROM daily_reviews
WHERE negative_ratio - LAG(negative_ratio) OVER (ORDER BY review_date) > 10
ORDER BY review_date DESC;
```

---

### 4. 소셜 연계 쿼리

#### 주 단위 롤링 집계 (디스코드 + 스팀)

```sql
WITH weekly_social AS (
    SELECT
        DATE_TRUNC('week', m.created_at) as week_start,
        'discord' as platform,
        COUNT(DISTINCT m.message_id) as activity_count,
        COUNT(DISTINCT r.reaction_id) as engagement_count
    FROM main.log_discord.message m
    LEFT JOIN main.log_discord.reaction r ON m.message_id = r.message_id
    WHERE m.game_code = 'INZOI'
        AND m.event_date >= CURRENT_DATE - 56
    GROUP BY DATE_TRUNC('week', m.created_at)

    UNION ALL

    SELECT
        DATE_TRUNC('week', FROM_UNIXTIME(timestamp_created)) as week_start,
        'steam_review' as platform,
        COUNT(DISTINCT recommendationid) as activity_count,
        SUM(votes_up) as engagement_count
    FROM main.log_steam.store_appreviews
    WHERE app_id IN (SELECT app_id FROM main.log_steam.steam_app_id WHERE game_code = 'INZOI')
        AND event_date >= CURRENT_DATE - 56
    GROUP BY DATE_TRUNC('week', FROM_UNIXTIME(timestamp_created))
)
SELECT
    week_start,
    platform,
    activity_count,
    engagement_count,
    SUM(activity_count) OVER (PARTITION BY week_start) as total_activity,
    SUM(engagement_count) OVER (PARTITION BY week_start) as total_engagement
FROM weekly_social
ORDER BY week_start DESC, platform;
```

---

### 5. 시간 기준 디스코드-스팀 통합 반응 분석

#### 시간대별 통합 반응 분석

```sql
SELECT
    DATE_TRUNC('hour', event_time) as time_bucket,
    platform,
    COUNT(*) as activity_count,
    SUM(engagement) as engagement_count
FROM (
    SELECT
        m.created_at as event_time,
        'discord' as platform,
        1 as activity_count,
        COUNT(DISTINCT r.reaction_id) as engagement
    FROM main.log_discord.message m
    LEFT JOIN main.log_discord.reaction r ON m.message_id = r.message_id
    WHERE m.game_code = 'INZOI'
        AND m.event_date >= CURRENT_DATE - 1
    GROUP BY m.created_at

    UNION ALL

    SELECT
        FROM_UNIXTIME(timestamp_created) as event_time,
        'steam_review' as platform,
        1 as activity_count,
        votes_up as engagement
    FROM main.log_steam.store_appreviews
    WHERE app_id IN (SELECT app_id FROM main.log_steam.steam_app_id WHERE game_code = 'INZOI')
        AND event_date >= CURRENT_DATE - 1
)
GROUP BY DATE_TRUNC('hour', event_time), platform
ORDER BY time_bucket DESC, platform;
```

---

## 📎 참고 파일

질문별 상세 예시 쿼리 및 결과 예시:
- `question-table-mapping-kpi-delivery.md`
- `question-table-mapping-content-delivery.md`
