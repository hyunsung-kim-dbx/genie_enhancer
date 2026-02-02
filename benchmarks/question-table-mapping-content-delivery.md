# 내용 정리형 질문별 테이블 및 데이터 매핑

## 📊 지표 관련 질문

### 3. 전체 소셜 플랫폼에서 반응이 가장 많은 주제는 무엇인가요?

**필요한 테이블:**
- `main.log_discord.message`
- `main.log_discord.reaction`
- `main.log_steam.store_appreviews`
- `main.log_steam.community_discussions_topics`
- `main.log_steam.community_discussions_comments`
- `main.log_steam.steam_app_id`

**필요한 컬럼:**
- 디스코드: `message.message_id`, `message.message`, `message.created_at`, `reaction.count`, `reaction.message_id`
- 스팀: `store_appreviews.recommendationid`, `store_appreviews.review`, `store_appreviews.votes_up`
- 스팀 커뮤니티: `community_discussions_topics.topic_id`, `community_discussions_topics.title`, `community_discussions_topics.content`
- 스팀 코멘트: `community_discussions_comments.comment_id`, `community_discussions_comments.content`

**조인 관계:**
```sql
-- 디스코드
message LEFT JOIN reaction ON message.message_id = reaction.message_id

-- 스팀
store_appreviews WHERE app_id IN (SELECT app_id FROM steam_app_id WHERE game_code = '게임코드')
community_discussions_topics WHERE app_id IN (SELECT app_id FROM steam_app_id WHERE game_code = '게임코드')
community_discussions_comments JOIN community_discussions_topics ON comments.topic_url = topics.url
```

**필터링 조건:**
- `message.game_code` = '게임코드' (디스코드)
- `steam_app_id.game_code` = '게임코드' (스팀)
- `event_date` 기준으로 시간 범위 필터링 (디스코드: `message.event_date`, 스팀: `store_appreviews.event_date`, `community_discussions_topics.event_date`)

**집계 방식:**
- UNION ALL로 플랫폼별 데이터 통합
- 반응 지표 통합

**예시 쿼리:**
```sql
WITH platform_data AS (
  SELECT 
    'discord' as platform,
    m.message_id as content_id,
    m.message as content_text,
    m.created_at as event_time,
    COALESCE(SUM(r.count), 0) as reaction_count
  FROM main.log_discord.message m
  LEFT JOIN main.log_discord.reaction r ON m.message_id = r.message_id
  WHERE m.game_code = 'inzoi'
    AND m.event_date >= DATE '2025-08-18'
    AND m.event_date <= DATE '2025-08-25'
  GROUP BY m.message_id, m.message, m.created_at
  
  UNION ALL
  
  SELECT 
    'steam_review' as platform,
    CAST(sa.recommendationid AS STRING) as content_id,
    sa.review as content_text,
    FROM_UNIXTIME(sa.timestamp_created) as event_time,
    sa.votes_up as reaction_count
  FROM main.log_steam.store_appreviews sa
  WHERE sa.app_id = 2456740
    AND sa.event_date >= DATE '2025-08-18'
    AND sa.event_date <= DATE '2025-08-25'
    AND sa.review IS NOT NULL
  
  UNION ALL
  
  SELECT 
    'steam_topic' as platform,
    ct.topic_id as content_id,
    ct.content as content_text,
    FROM_UNIXTIME(ct.timestamp) as event_time,
    (SELECT COUNT(DISTINCT cc.comment_id) 
     FROM main.log_steam.community_discussions_comments cc 
     WHERE cc.topic_url = ct.url) as reaction_count
  FROM main.log_steam.community_discussions_topics ct
  WHERE ct.app_id = 2456740
    AND ct.event_date >= DATE '2025-08-18'
    AND ct.event_date <= DATE '2025-08-25'
    AND ct.content IS NOT NULL
)
SELECT 
  platform,
  COUNT(*) as content_count,
  SUM(reaction_count) as total_reactions,
  MAX(reaction_count) as max_reactions,
  MAX(content_text) as sample_content
FROM platform_data
WHERE reaction_count > 0
GROUP BY platform
ORDER BY total_reactions DESC
LIMIT 10;
```

**쿼리 결과 (2025-08-18 ~ 2025-08-25, app_id: 2456740):**

| platform | content_count | total_reactions | max_reactions | sample_content |
|----------|---------------|-----------------|---------------|----------------|
| discord | 9295 | 5634327 | 234213 | 🫠 |
| steam_review | 123646 | 956148 | 2112 | 👎 |
| steam_topic | 9898 | 219795 | 1116 | 게임 불러오기 하니까 스팀화면으로 튕기고 스팀에서는 실행중이라 뜨네요. 실행 오류인 듯 한데 빨리 고쳐주세요. |

---

## 📈 트렌드 관련 질문

### 4. 지금 디스코드에서 가장 핫한 토픽은 무엇인가요?

**필요한 테이블:**
- `main.log_discord.message`
- `main.log_discord.reaction`
- `main.log_discord.channel_list` (선택적)
- `main.log_discord.thread_list` (선택적)

**필요한 컬럼:**
- `message.message_id`, `message.content`, `message.created_at`, `message.channel_id`, `message.thread_id`
- `reaction.reaction_id`, `reaction.message_id`
- `channel_list.channel_name` (선택적)
- `thread_list.thread_name` (선택적)

**조인 관계:**
```sql
message 
LEFT JOIN reaction ON message.message_id = reaction.message_id
(선택적) JOIN channel_list ON message.channel_id = channel_list.channel_id
(선택적) JOIN thread_list ON message.thread_id = thread_list.thread_id
```

**필터링 조건:**
- `message.game_code` = '게임코드'
- `message.event_date` 기준으로 필터링 (예: 최근 24시간 = `event_date = CURRENT_DATE`)
- `message.created_at`은 시간대별 그룹핑에만 사용

**집계 방식:**
- 시간대별 그룹핑: `DATE_TRUNC('hour', message.created_at)`
- 리액션 수 기준 정렬

**예시 쿼리:**
```sql
WITH hot_messages AS (
  SELECT 
    m.message_id,
    m.created_at,
    m.channel_id,
    c.channel_name,
    COALESCE(SUM(r.count), 0) as reaction_count,
    DATE_TRUNC('hour', m.created_at) as hour_bucket
  FROM main.log_discord.message m
  LEFT JOIN main.log_discord.reaction r ON m.message_id = r.message_id
  LEFT JOIN main.log_discord.channel_list c ON m.channel_id = c.channel_id
  WHERE m.game_code = 'inzoi'
    AND m.event_date = DATE '2025-08-25'
  GROUP BY m.message_id, m.created_at, m.channel_id, c.channel_name
),
channel_hourly_stats AS (
  SELECT 
    hour_bucket,
    channel_name,
    COUNT(*) as message_count,
    SUM(reaction_count) as total_reactions,
    AVG(reaction_count) as avg_reactions,
    MAX(reaction_count) as max_reactions
  FROM hot_messages
  GROUP BY hour_bucket, channel_name
)
SELECT 
  hour_bucket,
  channel_name,
  message_count,
  total_reactions,
  ROUND(avg_reactions, 2) as avg_reactions,
  max_reactions
FROM channel_hourly_stats
ORDER BY total_reactions DESC
LIMIT 10;
```

**쿼리 결과 (2025-08-25 24시간, app_id: 2456740):**

| hour_bucket | channel_name | message_count | total_reactions | avg_reactions | max_reactions |
|-------------|--------------|---------------|-----------------|---------------|---------------|
| 2025-08-25T06:00:00.000Z | service-notice | 1 | 102162 | 102162.0 | 102162 |
| 2025-08-25T19:00:00.000Z | cahaya-treasure-hunt-event | 2 | 96997 | 48498.5 | 72216 |
| 2025-08-25T20:00:00.000Z | 📢│ptbr-anuncios | 3 | 17380 | 5793.33 | 9360 |
| 2025-08-25T14:00:00.000Z | mod-chat | 132 | 13103 | 99.27 | 1008 |
| 2025-08-25T15:00:00.000Z | mod-chat | 168 | 12094 | 71.99 | 1176 |
| 2025-08-25T22:00:00.000Z | mod-chat | 271 | 10907 | 40.25 | 672 |
| 2025-08-25T05:00:00.000Z | inzoi-chat | 154 | 10232 | 66.44 | 504 |
| 2025-08-25T20:00:00.000Z | mod-chat | 142 | 8904 | 62.7 | 1008 |
| 2025-08-25T21:00:00.000Z | 📢│es-anuncios | 1 | 8016 | 8016.0 | 8016 |
| 2025-08-25T06:00:00.000Z | inzoi-chat | 186 | 7560 | 40.65 | 672 |

---

### 6. 최근 24시간 동안 가장 많이 언급된 키워드는 무엇인가요?

**필요한 테이블:**
- `main.log_discord.message`
- `main.log_steam.store_appreviews`
- `main.log_steam.community_discussions_topics`
- `main.log_steam.community_discussions_comments`
- `main.log_steam.steam_app_id`

**필요한 컬럼:**
- 디스코드: `message.content`, `message.created_at`
- 스팀: `store_appreviews.review`, `community_discussions_topics.content`, `community_discussions_comments.content`

**조인 관계:**
- 각 플랫폼별로 독립적으로 키워드 추출 후 통합

**필터링 조건:**
- `message.game_code` = '게임코드' (디스코드)
- `steam_app_id.game_code` = '게임코드' (스팀)
- `message.event_date` = CURRENT_DATE (디스코드, 최근 24시간)
- `store_appreviews.event_date` = CURRENT_DATE (스팀 리뷰, 최근 24시간)
- `community_discussions_topics.event_date` = CURRENT_DATE (스팀 토픽, 최근 24시간)
- `created_at`, `timestamp_created`, `timestamp`는 시간대별 분석에만 사용

**집계 방식:**
- AI 기반 키워드 추출 또는 텍스트 분석
- 키워드별 언급 횟수 집계
- 플랫폼별 통합 또는 분리 집계

**예시 쿼리:**
```sql
WITH content_stats AS (
  SELECT 
    'discord' as platform,
    COUNT(DISTINCT m.message_id) as content_count,
    COALESCE(SUM(r.count), 0) as total_reactions,
    AVG(LENGTH(m.message)) as avg_message_length
  FROM main.log_discord.message m
  LEFT JOIN main.log_discord.reaction r ON m.message_id = r.message_id
  WHERE m.game_code = 'inzoi'
    AND m.event_date = DATE '2025-08-25'
    AND m.message IS NOT NULL
    AND LENGTH(m.message) > 10
  
  UNION ALL
  
  SELECT 
    'steam_review' as platform,
    COUNT(DISTINCT sa.recommendationid) as content_count,
    SUM(sa.votes_up) as total_reactions,
    AVG(LENGTH(sa.review)) as avg_message_length
  FROM main.log_steam.store_appreviews sa
  WHERE sa.app_id = 2456740
    AND sa.event_date = DATE '2025-08-25'
    AND sa.review IS NOT NULL
  
  UNION ALL
  
  SELECT 
    'steam_topic' as platform,
    COUNT(DISTINCT ct.topic_id) as content_count,
    (SELECT COUNT(DISTINCT cc.comment_id) 
     FROM main.log_steam.community_discussions_comments cc 
     WHERE cc.topic_url IN (SELECT url FROM main.log_steam.community_discussions_topics 
                             WHERE app_id = 2456740 
                             AND event_date = DATE '2025-08-25')) as total_reactions,
    AVG(LENGTH(ct.content)) as avg_message_length
  FROM main.log_steam.community_discussions_topics ct
  WHERE ct.app_id = 2456740
    AND ct.event_date = DATE '2025-08-25'
    AND ct.content IS NOT NULL
  
  UNION ALL
  
  SELECT 
    'steam_comment' as platform,
    COUNT(DISTINCT cc.comment_id) as content_count,
    0 as total_reactions,
    AVG(LENGTH(cc.content)) as avg_message_length
  FROM main.log_steam.community_discussions_comments cc
  WHERE cc.app_id = 2456740
    AND cc.event_date = DATE '2025-08-25'
    AND cc.content IS NOT NULL
)
SELECT 
  platform,
  content_count,
  total_reactions,
  ROUND(avg_message_length, 2) as avg_content_length
FROM content_stats
ORDER BY content_count DESC;
```

*참고: 키워드 추출은 AI 기반 텍스트 분석이 필요하므로, 현재는 키워드 분석을 위한 기초 데이터(플랫폼별 콘텐츠 수, 반응 수, 평균 길이)만 제공합니다. 실제 키워드 추출은 별도의 NLP 분석 도구나 LLM을 활용하여 `message.message`, `store_appreviews.review`, `community_discussions_topics.content` 등의 텍스트 컬럼을 분석해야 합니다.*

**쿼리 결과 (2025-08-25 24시간, app_id: 2456740):**

| platform | content_count | total_reactions | avg_content_length |
|----------|---------------|-----------------|--------------------| 
| discord | 4722 | 444100 | 223.44 |
| steam_review | 1125 | 108472 | 258.75 |
| steam_comment | 590 | 0 | 282.89 |
| steam_topic | 83 | 640 | 468.55 |

---

## 😊😢 감성 분석 질문

### 9. 이런 긍정/부정 동향이 있었는데, 반응이 많은 상세 내용을 요약해서 추출해줘

**필요한 테이블:**
- `main.log_discord.message`
- `main.log_discord.reaction`
- `main.log_steam.store_appreviews`
- `main.log_steam.community_discussions_topics`
- `main.log_steam.community_discussions_comments`
- `main.log_steam.steam_app_id`

**필요한 컬럼:**
- 디스코드: `message.content`, `message.message_id`, `reaction.reaction_id`
- 스팀: `store_appreviews.review`, `store_appreviews.votes_up`, `store_appreviews.voted_up`
- 스팀 커뮤니티: `community_discussions_topics.content`, `community_discussions_comments.content`

**조인 관계:**
```sql
-- 디스코드
message LEFT JOIN reaction ON message.message_id = reaction.message_id

-- 스팀
store_appreviews WHERE app_id IN (SELECT app_id FROM steam_app_id WHERE game_code = '게임코드')
community_discussions_topics WHERE app_id IN (SELECT app_id FROM steam_app_id WHERE game_code = '게임코드')
```

**필터링 조건:**
- `message.game_code` = '게임코드'
- `steam_app_id.game_code` = '게임코드'
- 감성 필터: `voted_up = true/false` (스팀), AI 기반 감성 분류 (디스코드)
- 반응 수 기준: `COUNT(DISTINCT reaction_id) > N` 또는 `votes_up > N`

**집계 방식:**
- 반응 수가 많은 메시지/리뷰 추출
- AI 기반 요약
- 원본 메시지 출력

**예시 쿼리:**
```sql
WITH sentiment_data AS (
  SELECT 
    'discord' as platform,
    m.message_id as content_id,
    m.created_at as event_time,
    COALESCE(SUM(r.count), 0) as reaction_count,
    'high_engagement' as sentiment_type
  FROM main.log_discord.message m
  LEFT JOIN main.log_discord.reaction r ON m.message_id = r.message_id
  WHERE m.game_code = 'inzoi'
    AND m.event_date >= DATE '2025-08-18'
    AND m.event_date <= DATE '2025-08-25'
  GROUP BY m.message_id, m.created_at
  HAVING COALESCE(SUM(r.count), 0) >= 5
  
  UNION ALL
  
  SELECT 
    'steam_review' as platform,
    CAST(sa.recommendationid AS STRING) as content_id,
    FROM_UNIXTIME(sa.timestamp_created) as event_time,
    sa.votes_up as reaction_count,
    'positive' as sentiment_type
  FROM main.log_steam.store_appreviews sa
  WHERE sa.app_id = 2456740
    AND sa.event_date >= DATE '2025-08-18'
    AND sa.event_date <= DATE '2025-08-25'
    AND sa.voted_up = true
    AND sa.votes_up >= 10
  
  UNION ALL
  
  SELECT 
    'steam_review' as platform,
    CAST(sa.recommendationid AS STRING) as content_id,
    FROM_UNIXTIME(sa.timestamp_created) as event_time,
    sa.votes_up as reaction_count,
    'negative' as sentiment_type
  FROM main.log_steam.store_appreviews sa
  WHERE sa.app_id = 2456740
    AND sa.event_date >= DATE '2025-08-18'
    AND sa.event_date <= DATE '2025-08-25'
    AND sa.voted_up = false
    AND sa.votes_up >= 10
)
SELECT 
  sentiment_type,
  platform,
  COUNT(*) as content_count,
  SUM(reaction_count) as total_reactions,
  AVG(reaction_count) as avg_reactions,
  MAX(reaction_count) as max_reactions,
  MIN(event_time) as earliest_time,
  MAX(event_time) as latest_time
FROM sentiment_data
GROUP BY sentiment_type, platform
ORDER BY sentiment_type, total_reactions DESC;
```

*참고: 상세 내용 요약은 AI 기반 텍스트 분석이 필요하므로, 현재는 감성별 콘텐츠의 통계 정보(수량, 반응 수, 시간 범위)만 제공합니다. 실제 상세 요약을 위해서는 `content_id`를 기반으로 원본 텍스트(`message.message`, `store_appreviews.review`)를 조회한 후, LLM이나 요약 알고리즘으로 "주요 불만사항", "긍정적 피드백" 등의 요약 정보를 추출해야 합니다.*

**쿼리 결과 (2025-08-18 ~ 2025-08-25, app_id: 2456740):**

| sentiment_type | platform | content_count | total_reactions | avg_reactions | max_reactions | earliest_time | latest_time |
|----------------|----------|---------------|-----------------|---------------|---------------|---------------|---------------|-------------|
| high_engagement | discord | 8483 | 5634281 | 664.18 | 317415 | 2025-08-11T18:26:22.744Z | 2025-08-25T23:59:38.329Z |
| negative | steam_review | 12798 | 462059 | 36.10 | 2112 | 2025-07-09T18:15:22.000Z | 2025-08-25T00:52:54.000Z |
| positive | steam_review | 3390 | 177105 | 52.24 | 851 | 2025-07-09T15:46:10.000Z | 2025-08-22T08:52:38.000Z |

---

### 10. 부정 동향의 주요 키워드는 무엇인가요?

**필요한 테이블:**
- `main.log_discord.message`
- `main.log_steam.store_appreviews`
- `main.log_steam.community_discussions_topics` (선택적)

**필요한 컬럼:**
- `message.content` (디스코드)
- `store_appreviews.review` (스팀)
- `store_appreviews.voted_up` (감성 필터링용)

**조인 관계:**
- 각 플랫폼별로 독립적으로 분석

**필터링 조건:**
- `message.game_code` = '게임코드'
- `steam_app_id.game_code` = '게임코드'
- 감성 필터: `voted_up = false` (스팀), AI 기반 부정 감성 분류 (디스코드)
- `event_date` 기준으로 시간 범위 필터링 (각 테이블의 `event_date` 컬럼 사용)

**집계 방식:**
- AI 기반 키워드 추출
- 키워드 빈도 분석
- 키워드별 언급 횟수 집계

**예시 쿼리:**
```sql
WITH negative_content AS (
  SELECT 
    'discord' as platform,
    m.message_id as content_id,
    m.created_at as event_time,
    COALESCE(SUM(r.count), 0) as reaction_count
  FROM main.log_discord.message m
  LEFT JOIN main.log_discord.reaction r ON m.message_id = r.message_id
  WHERE m.game_code = 'inzoi'
    AND m.event_date >= DATE '2025-08-18'
    AND m.event_date <= DATE '2025-08-25'
    AND m.message IS NOT NULL
  GROUP BY m.message_id, m.created_at
  HAVING COALESCE(SUM(r.count), 0) >= 5
  
  UNION ALL
  
  SELECT 
    'steam_review' as platform,
    CAST(sa.recommendationid AS STRING) as content_id,
    FROM_UNIXTIME(sa.timestamp_created) as event_time,
    sa.votes_up as reaction_count
  FROM main.log_steam.store_appreviews sa
  WHERE sa.app_id = 2456740
    AND sa.event_date >= DATE '2025-08-18'
    AND sa.event_date <= DATE '2025-08-25'
    AND sa.voted_up = false
    AND sa.review IS NOT NULL
  
  UNION ALL
  
  SELECT 
    'steam_topic' as platform,
    ct.topic_id as content_id,
    FROM_UNIXTIME(ct.timestamp) as event_time,
    (SELECT COUNT(DISTINCT cc.comment_id) 
     FROM main.log_steam.community_discussions_comments cc 
     WHERE cc.topic_url = ct.url) as reaction_count
  FROM main.log_steam.community_discussions_topics ct
  WHERE ct.app_id = 2456740
    AND ct.event_date >= DATE '2025-08-18'
    AND ct.event_date <= DATE '2025-08-25'
    AND ct.content IS NOT NULL
)
SELECT 
  platform,
  COUNT(*) as content_count,
  SUM(reaction_count) as total_reactions,
  AVG(reaction_count) as avg_reactions,
  MAX(reaction_count) as max_reactions,
  MIN(event_time) as earliest_time,
  MAX(event_time) as latest_time
FROM negative_content
GROUP BY platform
ORDER BY total_reactions DESC;
```

*참고: 부정 키워드 추출은 AI 기반 감성 분석 및 텍스트 분석이 필요하므로, 현재는 부정적 콘텐츠의 기초 데이터(플랫폼별 수량, 반응 추이)만 제공합니다. 실제 키워드 추출을 위해서는 부정 리뷰(`voted_up = false`)와 고반응 디스코드 메시지의 텍스트를 별도의 NLP 분석 도구나 LLM으로 분석하여 "버그", "렉", "크래시" 등의 주요 불만 키워드를 도출해야 합니다.*

**쿼리 결과 (2025-08-18 ~ 2025-08-25, app_id: 2456740):**

| platform | content_count | total_reactions | avg_reactions | max_reactions | earliest_time | latest_time |
|----------|---------------|-----------------|---------------|---------------|---------------|-------------|
| discord | 8483 | 5634281 | 664.18 | 317415 | 2025-08-11T18:26:22.744Z | 2025-08-25T23:59:38.329Z |
| steam_review | 79606 | 674016 | 8.47 | 2112 | 2025-07-08T15:16:23.000Z | 2025-08-25T21:50:36.000Z |
| steam_topic | 11506 | 219795 | 19.10 | 1116 | 2024-08-21T04:51:24.000Z | 2025-08-25T21:19:36.000Z |

---

### 11. 스팀 리뷰에서 부정 리뷰가 급증한 시점과 주요 불만 사항은 무엇인가요?

**필요한 테이블:**
- `main.log_steam.store_appreviews`
- `main.log_steam.steam_app_id`

**필요한 컬럼:**
- `store_appreviews.recommendationid`, `store_appreviews.review`, `store_appreviews.voted_up`, `store_appreviews.timestamp_created`, `store_appreviews.app_id`

**조인 관계:**
```sql
store_appreviews 
WHERE app_id IN (SELECT app_id FROM steam_app_id WHERE game_code = '게임코드')
```

**필터링 조건:**
- `steam_app_id.game_code` = '게임코드'
- `store_appreviews.event_date` 기준으로 기간 필터링 (예: `event_date >= '2025-08-18'`)
- `voted_up = false` (부정 리뷰만)
- `FROM_UNIXTIME(timestamp_created)`는 일자별 그룹핑 및 정렬에만 사용

**집계 방식:**
- 일자별 그룹핑: `DATE(FROM_UNIXTIME(timestamp_created))`
- 일자별 부정 리뷰 수 집계
- 부정 리뷰 비율 계산
- 전일 대비 급증 감지: `LAG()` 함수로 전일 대비 변화율 계산
- AI 기반 불만 사항 추출
- 원본 리뷰 출력

**예시 쿼리:**
```sql
-- event_date 기준으로 일자별 그룹핑
WITH daily_reviews AS (
  SELECT 
    sa.event_date as review_date,
    COUNT(*) as total_reviews,
    COUNT(CASE WHEN voted_up = false THEN 1 END) as negative_reviews,
    COUNT(CASE WHEN voted_up = true THEN 1 END) as positive_reviews,
    ROUND(COUNT(CASE WHEN voted_up = false THEN 1 END) * 100.0 / COUNT(*), 2) as negative_ratio
  FROM main.log_steam.store_appreviews sa
  WHERE sa.app_id = 2456740
    AND sa.event_date >= DATE '2025-07-26'
    AND sa.event_date <= DATE '2025-08-25'
  GROUP BY sa.event_date
),
spike_detection AS (
  SELECT 
    review_date,
    total_reviews,
    negative_reviews,
    positive_reviews,
    negative_ratio,
    CASE 
      WHEN LAG(negative_reviews) OVER (ORDER BY review_date) > 0 
      THEN ROUND((negative_reviews - LAG(negative_reviews) OVER (ORDER BY review_date)) * 100.0 
                 / LAG(negative_reviews) OVER (ORDER BY review_date), 2)
      ELSE NULL
    END as negative_growth_rate
  FROM daily_reviews
),
spike_dates AS (
  SELECT review_date
  FROM spike_detection
  WHERE negative_growth_rate >= 50
     OR (negative_reviews >= 20 AND negative_ratio >= 40)
),
negative_reviews_detail AS (
  SELECT 
    sa.event_date as review_date,
    COUNT(*) as spike_day_negative_count,
    AVG(sa.votes_up) as avg_votes_up,
    MAX(sa.votes_up) as max_votes_up
  FROM main.log_steam.store_appreviews sa
  WHERE sa.app_id = 2456740
    AND sa.voted_up = false
    AND sa.event_date IN (SELECT review_date FROM spike_dates)
    AND sa.review IS NOT NULL
  GROUP BY sa.event_date
)
SELECT 
  sd.review_date,
  sd.total_reviews,
  sd.negative_reviews,
  sd.positive_reviews,
  sd.negative_ratio,
  sd.negative_growth_rate,
  nrd.spike_day_negative_count,
  ROUND(nrd.avg_votes_up, 2) as avg_votes_up,
  nrd.max_votes_up
FROM spike_detection sd
LEFT JOIN negative_reviews_detail nrd ON sd.review_date = nrd.review_date
WHERE sd.review_date IN (SELECT review_date FROM spike_dates)
ORDER BY sd.review_date DESC;
```

*참고: 주요 불만 사항 추출은 AI 기반 텍스트 분석이 필요하므로, 현재는 부정 리뷰 급증 시점과 통계 정보만 제공합니다. 실제 불만 사항을 파악하려면 급증 시점의 부정 리뷰 텍스트(`store_appreviews.review` WHERE `voted_up = false`)를 별도로 조회한 후, LLM이나 토픽 모델링으로 "최적화 부족", "버그", "서버 불안정" 등의 주요 불만 주제를 추출해야 합니다.*

**쿼리 결과 (2025-07-26 ~ 2025-08-25, app_id: 2456740):**

| review_date | total_reviews | negative_reviews | positive_reviews | negative_ratio | negative_growth_rate | spike_day_negative_count | avg_votes_up | max_votes_up |
|-------------|---------------|------------------|------------------|----------------|----------------------|--------------------------|--------------|--------------|
| 2025-08-22 | 23995 | 9682 | 14313 | 40.35 | -8.64 | 9682 | 8.36 | 2112 |
| 2025-08-21 | 23998 | 10598 | 13400 | 44.16 | -7.81 | 10598 | 10.31 | 1977 |
| 2025-08-20 | 23999 | 11496 | 12503 | 47.90 | -4.29 | 11496 | 9.46 | 1527 |
| 2025-08-19 | 23996 | 12011 | 11985 | 50.05 | -1.61 | 12011 | 8.32 | 1032 |
| 2025-08-18 | 23998 | 12207 | 11791 | 50.87 | -0.14 | 12207 | 7.87 | 748 |
| 2025-08-17 | 24000 | 12224 | 11776 | 50.93 | -0.02 | 12224 | 7.56 | 693 |
| 2025-08-16 | 24000 | 12226 | 11774 | 50.94 | -0.01 | 12226 | 7.69 | 662 |
| 2025-08-15 | 23998 | 12227 | 11771 | 50.95 | 0.21 | 12227 | 7.32 | 628 |
| 2025-08-14 | 23981 | 12201 | 11780 | 50.88 | -0.08 | 12201 | 7.23 | 590 |
| 2025-08-13 | 23999 | 12211 | 11788 | 50.88 | 4.72 | 12211 | 7.63 | 548 |

---

## 🔄 비교 분석 질문

### 14. 디스코드와 스팀에서 동시에 언급된 주요 이슈는 무엇인가요?

**필요한 테이블:**
- `main.log_discord.message`
- `main.log_steam.store_appreviews`
- `main.log_steam.community_discussions_topics`
- `main.log_steam.steam_app_id`

**필요한 컬럼:**
- `message.content` (디스코드)
- `store_appreviews.review` (스팀)
- `community_discussions_topics.content` (스팀 토픽)

**조인 관계:**
- 게임 코드 기준으로 통합
- 키워드 매칭 또는 AI 기반 주제 매칭

**필터링 조건:**
- `message.game_code` = '게임코드' (디스코드)
- `steam_app_id.game_code` = '게임코드' (스팀)
- 동일한 `event_date` 기준 시간 범위 적용 (각 테이블의 `event_date` 컬럼 사용)

**집계 방식:**
- AI 기반 주제 추출
- 주제별 매칭: 동일하거나 유사한 주제를 플랫폼 간 매칭
- 각 플랫폼별 반응 강도 비교
- 원본 메시지 출력

**예시 쿼리:**
```sql
WITH discord_stats AS (
  SELECT 
    'discord' as platform,
    COUNT(DISTINCT m.message_id) as content_count,
    COALESCE(SUM(r.count), 0) as total_reactions,
    AVG(LENGTH(m.message)) as avg_message_length
  FROM main.log_discord.message m
  LEFT JOIN main.log_discord.reaction r ON m.message_id = r.message_id
  WHERE m.game_code = 'inzoi'
    AND m.event_date >= DATE '2025-08-18'
    AND m.event_date <= DATE '2025-08-25'
),
steam_stats AS (
  SELECT 
    'steam_review' as platform,
    COUNT(DISTINCT sa.recommendationid) as content_count,
    SUM(sa.votes_up) as total_reactions,
    AVG(LENGTH(sa.review)) as avg_message_length
  FROM main.log_steam.store_appreviews sa
  WHERE sa.app_id = 2456740
    AND sa.event_date >= DATE '2025-08-18'
    AND sa.event_date <= DATE '2025-08-25'
    AND sa.review IS NOT NULL
  
  UNION ALL
  
  SELECT 
    'steam_topic' as platform,
    COUNT(DISTINCT ct.topic_id) as content_count,
    (SELECT COUNT(DISTINCT cc.comment_id) 
     FROM main.log_steam.community_discussions_comments cc 
     WHERE cc.topic_url IN (SELECT url FROM main.log_steam.community_discussions_topics 
                             WHERE app_id = 2456740 
                             AND event_date >= DATE '2025-08-18'
                             AND event_date <= DATE '2025-08-25')) as total_reactions,
    AVG(LENGTH(ct.content)) as avg_message_length
  FROM main.log_steam.community_discussions_topics ct
  WHERE ct.app_id = 2456740
    AND ct.event_date >= DATE '2025-08-18'
    AND ct.event_date <= DATE '2025-08-25'
    AND ct.content IS NOT NULL
)
SELECT 
  platform,
  content_count,
  total_reactions,
  ROUND(avg_message_length, 2) as avg_content_length,
  ROUND(total_reactions * 100.0 / SUM(total_reactions) OVER (), 2) as reaction_percentage
FROM (
  SELECT * FROM discord_stats
  UNION ALL
  SELECT * FROM steam_stats
) combined_stats
ORDER BY total_reactions DESC;
```

*참고: 주요 이슈 추출 및 플랫폼 간 매칭은 AI 기반 주제 모델링이 필요하므로, 현재는 플랫폼별 활동 통계만 제공합니다. 실제 공통 이슈를 파악하려면 디스코드 메시지와 스팀 리뷰/토픽의 텍스트를 벡터화하거나 LLM으로 분석하여 "성능 최적화", "UI 개선 요청" 등 양쪽에서 동시에 언급되는 주제를 찾아야 합니다.*

**쿼리 결과 (2025-08-18 ~ 2025-08-25, app_id: 2456740):**

| platform | content_count | total_reactions | avg_content_length | reaction_percentage |
|----------|---------------|-----------------|--------------------|--------------------|
| discord | 115454 | 5634327 | 184.86 | 85.45 |
| steam_review | 1913 | 956148 | 265.29 | 14.50 |
| steam_topic | 352 | 3185 | 525.82 | 0.05 |

---

### 16. 이 시간대에 디스코드와 스팀에서 어떤 소셜 반응이 일어났는지 시간 순서대로 보여줘

**필요한 테이블:**
- `main.log_discord.message`
- `main.log_discord.reaction`
- `main.log_steam.store_appreviews`
- `main.log_steam.community_discussions_topics`
- `main.log_steam.community_discussions_comments`
- `main.log_steam.steam_app_id`

**필요한 컬럼:**
- 디스코드: `message.created_at` (timestamp)
- 스팀: `store_appreviews.timestamp_created` (bigint), `community_discussions_topics.timestamp` (bigint)

**조인 관계:**
```sql
-- UNION ALL로 시간 기준 통합
SELECT 'discord' as platform, created_at as event_time, ...
UNION ALL
SELECT 'steam_review' as platform, FROM_UNIXTIME(timestamp_created) as event_time, ...
UNION ALL
SELECT 'steam_topic' as platform, FROM_UNIXTIME(timestamp) as event_time, ...
```

**필터링 조건:**
- `message.game_code` = '게임코드'
- `steam_app_id.game_code` = '게임코드'
- `event_date` 기준으로 시간 범위 필터링 (예: `event_date = DATE '2025-08-25'`)
- `created_at`, `timestamp_created`, `timestamp`는 시간대별 정렬 및 그룹핑에만 사용

**집계 방식:**
- 시간 순서대로 정렬: `ORDER BY event_time`
- 시간대별 그룹핑: `DATE_TRUNC('hour', event_time)`
- 플랫폼별 반응 지표 집계
- AI 기반 시간대별 요약
- 원본 메시지 출력

**예시 쿼리:**
```sql
WITH all_events AS (
  SELECT 
    'discord' as platform,
    'message' as event_type,
    m.message_id as event_id,
    m.message as content_text,
    m.created_at as event_time,
    COALESCE(SUM(r.count), 0) as reaction_count
  FROM main.log_discord.message m
  LEFT JOIN main.log_discord.reaction r ON m.message_id = r.message_id
  WHERE m.game_code = 'inzoi'
    AND m.event_date = DATE '2025-08-25'
  GROUP BY m.message_id, m.message, m.created_at
  
  UNION ALL
  
  SELECT 
    'steam' as platform,
    'review' as event_type,
    CAST(sa.recommendationid AS STRING) as event_id,
    sa.review as content_text,
    FROM_UNIXTIME(sa.timestamp_created) as event_time,
    sa.votes_up as reaction_count
  FROM main.log_steam.store_appreviews sa
  WHERE sa.app_id = 2456740
    AND sa.event_date = DATE '2025-08-25'
    AND sa.review IS NOT NULL
  
  UNION ALL
  
  SELECT 
    'steam' as platform,
    'topic' as event_type,
    ct.topic_id as event_id,
    ct.content as content_text,
    FROM_UNIXTIME(ct.timestamp) as event_time,
    (SELECT COUNT(DISTINCT cc.comment_id) 
     FROM main.log_steam.community_discussions_comments cc 
     WHERE cc.topic_url = ct.url) as reaction_count
  FROM main.log_steam.community_discussions_topics ct
  WHERE ct.app_id = 2456740
    AND ct.event_date = DATE '2025-08-25'
    AND ct.content IS NOT NULL
),
hourly_summary AS (
  SELECT 
    DATE_TRUNC('hour', event_time) as hour_bucket,
    platform,
    event_type,
    COUNT(*) as event_count,
    SUM(reaction_count) as total_reactions,
    MAX(reaction_count) as max_reactions,
    MAX(content_text) as top_content
  FROM all_events
  GROUP BY DATE_TRUNC('hour', event_time), platform, event_type
)
SELECT 
  hour_bucket,
  platform,
  event_type,
  event_count,
  total_reactions,
  max_reactions,
  top_content as sample_content
FROM hourly_summary
ORDER BY hour_bucket DESC, platform, event_type;
```

**쿼리 결과 (2025-08-25, app_id: 2456740):**

| hour_bucket | platform | event_type | event_count | total_reactions | max_reactions | sample_content |
|-------------|----------|------------|-------------|-----------------|---------------|----------------|
| 2025-08-25T23:00:00.000Z | discord | message | 257 | 9063 | 838 | 💀 bad idea to learn here ngl...we have me who cant spell, dath with the big words and mcai who speaks in tea |
| 2025-08-25T22:00:00.000Z | discord | message | 487 | 18265 | 1167 | 🤣 |
| 2025-08-25T22:00:00.000Z | steam | review | 2 | 0 | 0 | love it so much |
| 2025-08-25T21:00:00.000Z | discord | message | 216 | 25615 | 8016 | 😂 |
| 2025-08-25T21:00:00.000Z | steam | review | 11 | 0 | 0 | mason |
| 2025-08-25T21:00:00.000Z | steam | topic | 6 | 28 | 8 | hi, someone knows if is a mod like mccc but for inzoi? |
| 2025-08-25T20:00:00.000Z | discord | message | 388 | 35517 | 4680 | 🤮🤮🤮🤮--I mean, yum 😋 🤮 |
| 2025-08-25T20:00:00.000Z | steam | review | 15 | 0 | 0 | 后期无聊，前期还可以 |
| 2025-08-25T19:00:00.000Z | discord | message | 140 | 104702 | 72216 | 😡 |
| 2025-08-25T19:00:00.000Z | steam | review | 37 | 26 | 4 | this game is great. but the character's interaction is still looks not smooth enough... |

---

## ⏰ 기간별 분석 질문

### 17. 이 시점에 디스코드에서 무슨 얘기가 오갔나?

**필요한 테이블:**
- `main.log_discord.message`
- `main.log_discord.reaction`
- `main.log_discord.channel_list`
- `main.log_discord.thread_list` (선택적)

**필요한 컬럼:**
- `message.message_id`, `message.content`, `message.created_at`, `message.channel_id`, `message.thread_id`
- `reaction.reaction_id`
- `channel_list.channel_name`

**조인 관계:**
```sql
message 
LEFT JOIN reaction ON message.message_id = reaction.message_id
JOIN channel_list ON message.channel_id = channel_list.channel_id
```

**필터링 조건:**
- `message.game_code` = '게임코드'
- `message.event_date` 기준으로 먼저 필터링 (예: `event_date = DATE '2025-08-25'`)
- `message.created_at` BETWEEN 특정_시점 - INTERVAL 1 HOUR AND 특정_시점 + INTERVAL 1 HOUR (세밀한 시간 필터링)

**집계 방식:**
- 특정 시점 기준 시간대 필터링
- 리액션 수 기준으로 핫한 토픽 식별
- AI 기반 요약
- 원본 메시지 출력

**예시 쿼리:**
```sql
WITH discord_conversations AS (
  SELECT 
    m.message_id,
    m.created_at,
    m.channel_id,
    c.channel_name,
    m.thread_id,
    t.thread_title,
    COALESCE(SUM(r.count), 0) as reaction_count
  FROM main.log_discord.message m
  LEFT JOIN main.log_discord.reaction r ON m.message_id = r.message_id
  LEFT JOIN main.log_discord.channel_list c ON m.channel_id = c.channel_id
  LEFT JOIN main.log_discord.thread_list t ON m.thread_id = t.thread_id
  WHERE m.game_code = 'inzoi'
    AND m.event_date = DATE '2025-08-25'
    AND m.created_at >= TIMESTAMP '2025-08-25 14:00:00' - INTERVAL 1 HOUR
    AND m.created_at <= TIMESTAMP '2025-08-25 14:00:00' + INTERVAL 1 HOUR
  GROUP BY m.message_id, m.created_at, m.channel_id, c.channel_name, 
           m.thread_id, t.thread_title
),
channel_stats AS (
  SELECT 
    channel_name,
    COUNT(*) as message_count,
    SUM(reaction_count) as total_reactions,
    AVG(reaction_count) as avg_reactions,
    MAX(reaction_count) as max_reactions,
    MIN(created_at) as first_message_time,
    MAX(created_at) as last_message_time
  FROM discord_conversations
  GROUP BY channel_name
)
SELECT 
  channel_name,
  message_count,
  total_reactions,
  ROUND(avg_reactions, 2) as avg_reactions,
  max_reactions,
  first_message_time,
  last_message_time
FROM channel_stats
ORDER BY total_reactions DESC
LIMIT 10;
```

*참고: 대화 내용 요약은 AI 기반 텍스트 분석이 필요하므로, 현재는 채널별 활동 통계(메시지 수, 반응 수)만 제공합니다. 실제 대화 내용을 파악하려면 해당 시간대의 메시지 텍스트(`message.message`)를 조회한 후, LLM으로 "주요 논의 주제", "주요 질문/답변" 등을 요약해야 합니다.*

**쿼리 결과 (2025-08-25 14:00 전후 1시간, app_id: 2456740):**

| channel_name | message_count | total_reactions | avg_reactions | max_reactions | first_message_time | last_message_time |
|--------------|---------------|-----------------|---------------|---------------|-------------------|-------------------|
| mod-chat | 166 | 15786 | 95.1 | 1008 | 2025-08-25T13:08:42.398Z | 2025-08-25T14:59:40.827Z |
| share-your-zoi | 6 | 5867 | 977.83 | 1507 | 2025-08-25T13:16:10.754Z | 2025-08-25T14:34:47.759Z |
| off-topic-chat | 271 | 4701 | 17.35 | 336 | 2025-08-25T13:00:21.492Z | 2025-08-25T14:59:58.912Z |
| inzoi-chat | 181 | 4030 | 22.27 | 336 | 2025-08-25T13:00:19.683Z | 2025-08-25T14:59:30.767Z |
| mod-announcements | 1 | 2350 | 2350.0 | 2350 | 2025-08-25T13:24:57.885Z | 2025-08-25T13:24:57.885Z |
| share-your-builds | 2 | 2016 | 1008.0 | 1008 | 2025-08-25T13:00:51.747Z | 2025-08-25T13:11:52.424Z |
| community-tech-help | 2 | 336 | 168.0 | 336 | 2025-08-25T14:56:33.066Z | 2025-08-25T14:57:55.999Z |
| gameplay-questions | 33 | 336 | 10.18 | 168 | 2025-08-25T13:10:31.077Z | 2025-08-25T14:50:14.744Z |
| inzoi-feedback | 16 | 335 | 20.94 | 168 | 2025-08-25T13:44:41.256Z | 2025-08-25T14:52:35.967Z |
| safety-test | 1 | 166 | 166.0 | 166 | 2025-08-25T13:07:14.411Z | 2025-08-25T13:07:14.411Z |

---

### 18. KPI가 특정 시점에 트래픽이 많이 뛰었는데, 그때 소셜에서는 어떤 반응이 있었나?

**필요한 테이블:**
- `main.log_steam.partner_traffic`
- `main.log_discord.message`
- `main.log_discord.reaction`
- `main.log_steam.store_appreviews`
- `main.log_steam.community_discussions_topics`
- `main.log_steam.steam_app_id`

**필요한 컬럼:**
- `partner_traffic.visits`, `partner_traffic.event_date`
- `message.created_at`
- `store_appreviews.timestamp_created`

**조인 관계:**
```sql
partner_traffic 
LEFT JOIN message ON message.game_code = (SELECT game_code FROM steam_app_id WHERE app_id = partner_traffic.app_id)
  AND DATE(message.created_at) = partner_traffic.event_date
LEFT JOIN store_appreviews ON CAST(partner_traffic.app_id AS BIGINT) = store_appreviews.app_id
  AND store_appreviews.event_date = partner_traffic.event_date
```

**필터링 조건:**
- `partner_traffic.app_id` IN (SELECT app_id FROM steam_app_id WHERE game_code = '게임코드')
- 트래픽 급증 시점 식별: `visits` 급증 감지
- 해당 시점 전후 소셜 반응 분석

**집계 방식:**
- 트래픽 급증 시점 식별
- 해당 시점 전후 디스코드/스팀 반응 집계
- AI 기반 연계 분석
- 원본 메시지 출력

**예시 쿼리:**
```sql
WITH traffic_data AS (
  SELECT 
    pt.event_date,
    pt.app_id,
    pt.visits,
    CASE 
      WHEN LAG(pt.visits) OVER (PARTITION BY pt.app_id ORDER BY pt.event_date) > 0 
      THEN ROUND((pt.visits - LAG(pt.visits) OVER (PARTITION BY pt.app_id ORDER BY pt.event_date)) * 100.0 
                 / LAG(pt.visits) OVER (PARTITION BY pt.app_id ORDER BY pt.event_date), 2)
      ELSE NULL
    END as growth_rate
  FROM main.log_steam.partner_traffic pt
  WHERE pt.app_id = 2456740
    AND pt.event_date >= DATE '2025-07-26'
    AND pt.event_date <= DATE '2025-08-25'
),
traffic_spikes AS (
  SELECT 
    event_date,
    app_id,
    visits,
    growth_rate
  FROM traffic_data
  WHERE growth_rate >= 30  -- 급증 기준: 전일 대비 30% 이상 증가
     OR visits >= (SELECT AVG(visits) * 1.8 FROM traffic_data)  -- 또는 평균의 1.8배 이상
),
-- Discord 반응 데이터 (트래픽 스파이크 날짜 범위 내, event_date 기준)
discord_reactions AS (
  SELECT 
    m.event_date,
    COUNT(DISTINCT m.message_id) as content_count,
    COALESCE(SUM(r.count), 0) as total_reactions
  FROM main.log_discord.message m
  LEFT JOIN main.log_discord.reaction r ON m.message_id = r.message_id
  WHERE m.game_code = 'inzoi'
    AND m.event_date >= (SELECT MIN(event_date) - INTERVAL 1 DAY FROM traffic_spikes)
    AND m.event_date <= (SELECT MAX(event_date) + INTERVAL 1 DAY FROM traffic_spikes)
  GROUP BY m.event_date
),
-- Steam 리뷰 반응 데이터 (event_date 기준)
steam_review_reactions AS (
  SELECT 
    sa.event_date,
    COUNT(DISTINCT sa.recommendationid) as content_count,
    SUM(sa.votes_up) as total_reactions
  FROM main.log_steam.store_appreviews sa
  WHERE sa.app_id = 2456740
    AND sa.event_date >= (SELECT MIN(event_date) - INTERVAL 1 DAY FROM traffic_spikes)
    AND sa.event_date <= (SELECT MAX(event_date) + INTERVAL 1 DAY FROM traffic_spikes)
    AND sa.review IS NOT NULL
  GROUP BY sa.event_date
),
-- Steam 토픽 코멘트 수 계산 (event_date 기준)
steam_topic_comments AS (
  SELECT 
    ct.event_date,
    COUNT(DISTINCT cc.comment_id) as total_reactions
  FROM main.log_steam.community_discussions_topics ct
  INNER JOIN main.log_steam.community_discussions_comments cc 
    ON cc.topic_url = ct.url
  WHERE ct.app_id = 2456740
    AND ct.event_date >= (SELECT MIN(event_date) - INTERVAL 1 DAY FROM traffic_spikes)
    AND ct.event_date <= (SELECT MAX(event_date) + INTERVAL 1 DAY FROM traffic_spikes)
  GROUP BY ct.event_date
),
-- Steam 토픽 반응 데이터 (event_date 기준)
steam_topic_reactions AS (
  SELECT 
    ct.event_date,
    COUNT(DISTINCT ct.topic_id) as content_count,
    COALESCE(stc.total_reactions, 0) as total_reactions
  FROM main.log_steam.community_discussions_topics ct
  LEFT JOIN steam_topic_comments stc 
    ON ct.event_date = stc.event_date
  WHERE ct.app_id = 2456740
    AND ct.event_date >= (SELECT MIN(event_date) - INTERVAL 1 DAY FROM traffic_spikes)
    AND ct.event_date <= (SELECT MAX(event_date) + INTERVAL 1 DAY FROM traffic_spikes)
    AND ct.content IS NOT NULL
  GROUP BY ct.event_date, stc.total_reactions
),
-- 플랫폼별 소셜 반응 통합
social_reactions AS (
  SELECT 
    'discord' as platform,
    event_date,
    content_count,
    total_reactions
  FROM discord_reactions
  
  UNION ALL
  
  SELECT 
    'steam_review' as platform,
    event_date,
    content_count,
    total_reactions
  FROM steam_review_reactions
  
  UNION ALL
  
  SELECT 
    'steam_topic' as platform,
    event_date,
    content_count,
    total_reactions
  FROM steam_topic_reactions
)
-- 트래픽 스파이크와 소셜 반응 매칭 (날짜 범위 조인)
SELECT 
  ts.event_date as traffic_spike_date,
  ts.visits as traffic_visits,
  ts.growth_rate as traffic_growth_rate,
  sr.platform,
  SUM(sr.content_count) as total_content,
  SUM(sr.total_reactions) as total_engagement
FROM traffic_spikes ts
LEFT JOIN social_reactions sr 
  ON sr.event_date BETWEEN ts.event_date - INTERVAL 1 DAY 
                       AND ts.event_date + INTERVAL 1 DAY
GROUP BY ts.event_date, ts.visits, ts.growth_rate, sr.platform
ORDER BY ts.event_date DESC, sr.platform;
```

**쿼리 결과 (2025-08-25, app_id: 2456740, 트래픽 급증 기준: 30% 이상 또는 평균의 1.8배 이상):**

| traffic_spike_date | traffic_visits | traffic_growth_rate | platform | total_content | total_engagement |
|--------------------|----------------|---------------------|----------|---------------|------------------|
| 2025-08-25 | 5847 | 194800.00 | discord | 12591 | 839706 |
| 2025-08-25 | 4769 | 537.57 | discord | 12591 | 839706 |
| 2025-08-25 | 3937 | 590.70 | discord | 12591 | 839706 |
| 2025-08-25 | 4769 | 537.57 | steam_review | 1686 | 122088 |
| 2025-08-25 | 3937 | 590.70 | steam_review | 1686 | 122088 |
| 2025-08-25 | 5847 | 194800.00 | steam_review | 1686 | 122088 |
| 2025-08-25 | 4769 | 537.57 | steam_topic | 162 | 2268 |
| 2025-08-25 | 3937 | 590.70 | steam_topic | 162 | 2268 |
| 2025-08-25 | 5847 | 194800.00 | steam_topic | 162 | 2268 |

*참고: 2025-08-25에 여러 트래픽 스파이크가 발생했으며, 각 스파이크 전후 1일간의 소셜 반응 데이터를 집계했습니다.*

---

## 🌍 지역별 분석 질문

### 22. 지역별로 소셜 반응의 차이는 무엇인가요?

**필요한 테이블:**
- `main.log_steam.partner_regions_and_countries`
- `main.log_steam.store_appreviews`
- `main.log_steam.community_discussions_topics` (선택적)
- `main.log_steam.steam_app_id`

**필요한 컬럼:**
- `partner_regions_and_countries.scope`, `partner_regions_and_countries.name`
- `store_appreviews.review`, `store_appreviews.voted_up`

**조인 관계:**
```sql
partner_regions_and_countries 
LEFT JOIN store_appreviews ON CAST(partner_regions_and_countries.app_id AS BIGINT) = store_appreviews.app_id
WHERE partner_regions_and_countries.app_id IN (SELECT app_id FROM steam_app_id WHERE game_code = '게임코드')
```

**필터링 조건:**
- `steam_app_id.game_code` = '게임코드'
- `partner_regions_and_countries.scope` = 'region' 또는 'country'
- `event_date` 기준으로 시간 범위 필터링 (`partner_regions_and_countries.event_date`, `store_appreviews.event_date`)

**집계 방식:**
- 지역별 그룹핑 (`partner_regions_and_countries.name`)
- 지역별 위시리스트 및 판매량 분석
- **참고**: 리뷰 데이터(`store_appreviews`)에는 지역 정보가 없어 직접 연결 불가
  - 대안 1: `store_appreviews.language` 컬럼으로 언어별 리뷰 분석
  - 대안 2: 별도의 사용자-지역 매핑 테이블 필요
- AI 기반 지역별 주요 이슈 추출

**예시 쿼리:**
```sql
-- 지역별 위시리스트 및 판매량 데이터 (리뷰 데이터는 성능상 별도 쿼리 권장)
SELECT 
  prc.scope,
  prc.name as region_name,
  COUNT(DISTINCT prc.event_date) as days_tracked,
  SUM(prc.wishlists) as total_wishlists,
  SUM(prc.units) as total_sales,
  ROUND(AVG(prc.wishlists), 2) as avg_daily_wishlists,
  ROUND(AVG(prc.units), 2) as avg_daily_sales,
  MIN(prc.event_date) as period_start,
  MAX(prc.event_date) as period_end
FROM main.log_steam.partner_regions_and_countries prc
WHERE prc.app_id = 2456740
  AND prc.scope = 'region'
  AND prc.event_date >= DATE '2025-07-26'
  AND prc.event_date <= DATE '2025-08-25'
GROUP BY prc.scope, prc.name
ORDER BY total_sales DESC
LIMIT 10;
```

**쿼리 결과 (2025-07-26 ~ 2025-08-25, 실제 데이터는 08-08부터, app_id: 2456740):**

| region_name | days_tracked | total_wishlists | total_sales | avg_daily_wishlists | avg_daily_sales | period_start | period_end |
|-------------|--------------|-----------------|-------------|---------------------|-----------------|--------------|------------|
| Western Europe | 18 | 7078 | 14576 | 393.22 | 809.78 | 2025-08-08 | 2025-08-25 |
| Asia | 18 | 8007 | 12853 | 444.83 | 714.06 | 2025-08-08 | 2025-08-25 |
| North America | 18 | 6658 | 12182 | 369.89 | 676.78 | 2025-08-08 | 2025-08-25 |
| Central Asia | 18 | 4681 | 3411 | 260.06 | 189.50 | 2025-08-08 | 2025-08-25 |
| Latin America | 18 | 3006 | 2378 | 167.00 | 132.11 | 2025-08-08 | 2025-08-25 |
| Eastern Europe | 18 | 1538 | 2191 | 85.44 | 121.72 | 2025-08-08 | 2025-08-25 |
| South East Asia | 18 | 1883 | 1954 | 104.61 | 108.56 | 2025-08-08 | 2025-08-25 |
| Middle East | 18 | 927 | 1185 | 51.50 | 65.83 | 2025-08-08 | 2025-08-25 |
| Oceania | 18 | 605 | 823 | 33.61 | 45.72 | 2025-08-08 | 2025-08-25 |
| South Asia | 18 | 232 | 171 | 12.89 | 9.50 | 2025-08-08 | 2025-08-25 |

*참고: `partner_regions_and_countries` 테이블은 지역별 집계 데이터이고, `store_appreviews` 테이블에는 지역 정보가 없어서 직접 조인이 불가능합니다. 지역별 리뷰 분석이 필요한 경우, `store_appreviews.language` 컬럼을 활용한 간접 분석이나 별도의 사용자 지역 정보 테이블이 필요합니다.*

---

## 🎯 캠페인 및 이벤트 분석 질문

### 24. 마케팅 캠페인 전후 소셜 반응 변화는 무엇인가요?

**필요한 테이블:**
- `main.log_discord.message`
- `main.log_discord.reaction`
- `main.log_steam.store_appreviews`
- `main.log_steam.partner_wishlist` (선택적)
- `main.log_steam.steam_app_id`

**필요한 컬럼:**
- 각 플랫폼별 활동 지표 및 시간 정보
- 캠페인 시작/종료 날짜 (파라미터로 입력)

**조인 관계:**
- 각 플랫폼별로 독립적으로 집계

**필터링 조건:**
- `message.game_code` = '게임코드'
- `steam_app_id.game_code` = '게임코드'
- `event_date` 기준으로 캠페인 전후 기간 필터링 (예: before/during/after)

**집계 방식:**
- 캠페인 전후 구분: `CASE WHEN event_date < campaign_start_date THEN 'before' ELSE 'after' END`
- 기간별 활동 지표 집계
- 전후 비교: 증감율 계산
- AI 기반 비교 요약

**예시 쿼리:**
```sql
WITH discord_activity AS (
  SELECT 
    CASE 
      WHEN m.event_date < DATE '2025-08-25' THEN 'before'
      WHEN m.event_date BETWEEN DATE '2025-08-25' AND DATE '2025-09-01' THEN 'during'
      ELSE 'after'
    END as period,
    COUNT(DISTINCT m.message_id) as message_count,
    COALESCE(SUM(r.count), 0) as reaction_count
  FROM main.log_discord.message m
  LEFT JOIN main.log_discord.reaction r ON m.message_id = r.message_id
  WHERE m.game_code = 'inzoi'
    AND m.event_date BETWEEN DATE '2025-08-18'
                          AND DATE '2025-09-08'
  GROUP BY 
    CASE 
      WHEN m.event_date < DATE '2025-08-25' THEN 'before'
      WHEN m.event_date BETWEEN DATE '2025-08-25' AND DATE '2025-09-01' THEN 'during'
      ELSE 'after'
    END
),
steam_activity AS (
  SELECT 
    CASE 
      WHEN sa.event_date < DATE '2025-08-25' THEN 'before'
      WHEN sa.event_date BETWEEN DATE '2025-08-25' AND DATE '2025-09-01' THEN 'during'
      ELSE 'after'
    END as period,
    COUNT(DISTINCT sa.recommendationid) as review_count,
    SUM(sa.votes_up) as total_votes_up
  FROM main.log_steam.store_appreviews sa
  WHERE sa.app_id = 2456740
    AND sa.event_date BETWEEN DATE '2025-08-18'
                           AND DATE '2025-09-08'
    AND sa.review IS NOT NULL
  GROUP BY 
    CASE 
      WHEN sa.event_date < DATE '2025-08-25' THEN 'before'
      WHEN sa.event_date BETWEEN DATE '2025-08-25' AND DATE '2025-09-01' THEN 'during'
      ELSE 'after'
    END
),
comparison_summary AS (
  SELECT 
    'discord' as platform,
    period,
    SUM(message_count) as activity_count,
    SUM(reaction_count) as engagement_count
  FROM discord_activity
  GROUP BY period
  
  UNION ALL
  
  SELECT 
    'steam' as platform,
    period,
    SUM(review_count) as activity_count,
    SUM(total_votes_up) as engagement_count
  FROM steam_activity
  GROUP BY period
)
SELECT 
  platform,
  period,
  activity_count,
  engagement_count
FROM comparison_summary
ORDER BY platform, 
  CASE period WHEN 'before' THEN 1 WHEN 'during' THEN 2 ELSE 3 END;
```

**쿼리 결과 (2025-08-18 ~ 2025-09-08, 이벤트 기간: 2025-08-25 ~ 2025-09-01, app_id: 2456740):**

| platform | period | activity_count | engagement_count |
|----------|--------|----------------|------------------|
| discord | before | 110001 | 5171119 |
| discord | during | 24489 | 2382323 |
| discord | after | 13560 | 1448646 |
| steam | before | 1787 | 847676 |
| steam | during | 1701 | 535890 |
| steam | after | 1447 | 140437 |

---

## 📝 요약 및 인사이트 질문

### 27. 오늘 하루 동안 소셜에서 일어난 주요 이슈를 요약해주세요

**필요한 테이블:**
- `main.log_discord.message`
- `main.log_discord.reaction`
- `main.log_steam.store_appreviews`
- `main.log_steam.community_discussions_topics`
- `main.log_steam.community_discussions_comments`
- `main.log_steam.steam_app_id`

**필요한 컬럼:**
- 각 플랫폼별 활동 지표 및 내용

**조인 관계:**
- 각 플랫폼별로 독립적으로 집계 후 통합

**필터링 조건:**
- `message.game_code` = '게임코드'
- `steam_app_id.game_code` = '게임코드'
- `message.event_date` = CURRENT_DATE (디스코드, 오늘 하루)
- `store_appreviews.event_date` = CURRENT_DATE (스팀 리뷰, 오늘 하루)
- `community_discussions_topics.event_date` = CURRENT_DATE (스팀 토픽, 오늘 하루)

**집계 방식:**
- 플랫폼별 주요 활동 지표 집계
- AI 기반 종합 요약
- 주요 이슈별 상세 요약
- 원본 메시지 출력

**예시 쿼리:**
```sql
WITH today_events AS (
  SELECT 
    'discord' as platform,
    m.message_id as content_id,
    m.created_at as event_time,
    COALESCE(SUM(r.count), 0) as reaction_count
  FROM main.log_discord.message m
  LEFT JOIN main.log_discord.reaction r ON m.message_id = r.message_id
  WHERE m.game_code = 'inzoi'
    AND m.event_date = DATE '2025-08-25'
  GROUP BY m.message_id, m.created_at
  
  UNION ALL
  
  SELECT 
    'steam_review' as platform,
    CAST(sa.recommendationid AS STRING) as content_id,
    FROM_UNIXTIME(sa.timestamp_created) as event_time,
    sa.votes_up as reaction_count
  FROM main.log_steam.store_appreviews sa
  WHERE sa.app_id = 2456740
    AND sa.event_date = DATE '2025-08-25'
    AND sa.review IS NOT NULL
  
  UNION ALL
  
  SELECT 
    'steam_topic' as platform,
    ct.topic_id as content_id,
    FROM_UNIXTIME(ct.timestamp) as event_time,
    (SELECT COUNT(DISTINCT cc.comment_id) 
     FROM main.log_steam.community_discussions_comments cc 
     WHERE cc.topic_url = ct.url) as reaction_count
  FROM main.log_steam.community_discussions_topics ct
  WHERE ct.app_id = 2456740
    AND ct.event_date = DATE '2025-08-25'
    AND ct.content IS NOT NULL
),
platform_summary AS (
  SELECT 
    platform,
    COUNT(DISTINCT content_id) as total_content,
    SUM(reaction_count) as total_reactions,
    AVG(reaction_count) as avg_reactions,
    MAX(reaction_count) as max_reactions,
    MIN(event_time) as earliest_time,
    MAX(event_time) as latest_time
  FROM today_events
  GROUP BY platform
)
SELECT 
  platform,
  total_content,
  total_reactions,
  ROUND(avg_reactions, 2) as avg_reactions,
  max_reactions,
  earliest_time,
  latest_time
FROM platform_summary
ORDER BY total_reactions DESC;
```

*참고: 주요 이슈 요약은 AI 기반 텍스트 분석 및 토픽 모델링이 필요하므로, 현재는 플랫폼별 활동 통계만 제공합니다. 실제 이슈 요약을 위해서는 해당 날짜의 고반응 메시지/리뷰 텍스트를 LLM으로 분석하여 "주요 이슈", "핫한 토픽", "주요 피드백" 등을 추출하고 요약해야 합니다.*

**쿼리 결과 (2025-08-25, app_id: 2456740):**

| platform | total_content | total_reactions | avg_reactions | max_reactions | earliest_time | latest_time |
|----------|---------------|-----------------|---------------|---------------|---------------|-------------|
| discord | 5453 | 463208 | 84.95 | 102162 | 2025-08-25T00:00:04.730Z | 2025-08-25T23:59:45.996Z |
| steam_review | 1125 | 108472 | 4.52 | 851 | 2025-08-09T19:26:39.000Z | 2025-08-25T22:31:04.000Z |
| steam_topic | 83 | 13024 | 9.05 | 20 | 2025-03-20T13:55:06.000Z | 2025-08-25T21:19:36.000Z |

---

### 28. 이번 주 주요 소셜 반응을 플랫폼별로 요약해주세요

**필요한 테이블:**
- `main.log_discord.message`
- `main.log_discord.reaction`
- `main.log_steam.store_appreviews`
- `main.log_steam.community_discussions_topics`
- `main.log_steam.steam_app_id`

**필요한 컬럼:**
- 각 플랫폼별 활동 지표 및 내용

**조인 관계:**
- 각 플랫폼별로 독립적으로 집계

**필터링 조건:**
- `message.game_code` = '게임코드'
- `steam_app_id.game_code` = '게임코드'
- `event_date` 기준으로 주간 필터링 (예: `event_date >= DATE '2025-08-18' AND event_date <= DATE '2025-08-25'`)
- `created_at`, `timestamp_created`는 정렬 및 시간대 분석에만 사용

**집계 방식:**
- 플랫폼별 그룹핑
- 플랫폼별 주요 활동 지표 집계
- AI 기반 플랫폼별 요약

**예시 쿼리:**
```sql
WITH discord_weekly AS (
  SELECT 
    'discord' as platform,
    COUNT(DISTINCT m.message_id) as total_messages,
    COALESCE(SUM(r.count), 0) as total_reactions
  FROM main.log_discord.message m
  LEFT JOIN main.log_discord.reaction r ON m.message_id = r.message_id
  WHERE m.game_code = 'inzoi'
    AND m.event_date >= DATE '2025-08-18'
    AND m.event_date <= DATE '2025-08-25'
),
steam_weekly AS (
  SELECT 
    'steam' as platform,
    COUNT(DISTINCT sa.recommendationid) as total_reviews,
    SUM(sa.votes_up) as total_votes_up
  FROM main.log_steam.store_appreviews sa
  WHERE sa.app_id = 2456740
    AND sa.event_date >= DATE '2025-08-18'
    AND sa.event_date <= DATE '2025-08-25'
    AND sa.review IS NOT NULL
)
SELECT 
  platform,
  total_messages as activity_count,
  total_reactions as engagement_count
FROM discord_weekly

UNION ALL

SELECT 
  platform,
  total_reviews as activity_count,
  total_votes_up as engagement_count
FROM steam_weekly
ORDER BY platform;
```

*참고: 플랫폼별 요약은 AI 기반 텍스트 분석이 필요하므로, 현재는 플랫폼별 활동 통계만 제공합니다. 실제 플랫폼별 주요 반응 요약을 위해서는 각 플랫폼의 고반응 콘텐츠 텍스트를 LLM으로 분석하여 "디스코드 주요 논의", "스팀 주요 리뷰 내용" 등을 별도로 요약해야 합니다.*

**쿼리 결과 (2025-08-18 ~ 2025-08-25, app_id: 2456740):**

| platform | activity_count | engagement_count |
|----------|----------------|------------------|
| discord | 115454 | 5634327 |
| steam | 1913 | 956148 |

---

### 29. 디스코드와 스팀의 주요 반응을 통합해서 요약해주세요

**필요한 테이블:**
- `main.log_discord.message`
- `main.log_discord.reaction`
- `main.log_steam.store_appreviews`
- `main.log_steam.community_discussions_topics`
- `main.log_steam.steam_app_id`

**필요한 컬럼:**
- 각 플랫폼별 활동 지표 및 내용

**조인 관계:**
- 게임 코드 기준으로 통합

**필터링 조건:**
- `message.game_code` = '게임코드'
- `steam_app_id.game_code` = '게임코드'
- `event_date` 기준으로 시간 범위 필터링 (각 테이블의 `event_date` 컬럼 사용)

**집계 방식:**
- 플랫폼별 데이터 통합 (UNION ALL)
- 통합 반응 지표 집계
- AI 기반 통합 요약
- 주요 이슈별 상세 요약

**예시 쿼리:**
```sql
WITH integrated_data AS (
  SELECT 
    'discord' as platform,
    m.message_id as content_id,
    m.created_at as event_time,
    COALESCE(SUM(r.count), 0) as reaction_count,
    NULL as sentiment
  FROM main.log_discord.message m
  LEFT JOIN main.log_discord.reaction r ON m.message_id = r.message_id
  WHERE m.game_code = 'inzoi'
    AND m.event_date >= DATE '2025-08-18'
    AND m.event_date <= DATE '2025-08-25'
  GROUP BY m.message_id, m.created_at
  
  UNION ALL
  
  SELECT 
    'steam_review' as platform,
    CAST(sa.recommendationid AS STRING) as content_id,
    FROM_UNIXTIME(sa.timestamp_created) as event_time,
    sa.votes_up as reaction_count,
    CASE WHEN sa.voted_up = true THEN 'positive' ELSE 'negative' END as sentiment
  FROM main.log_steam.store_appreviews sa
  WHERE sa.app_id = 2456740
    AND sa.event_date >= DATE '2025-08-18'
    AND sa.event_date <= DATE '2025-08-25'
    AND sa.review IS NOT NULL
  
  UNION ALL
  
  SELECT 
    'steam_topic' as platform,
    ct.topic_id as content_id,
    FROM_UNIXTIME(ct.timestamp) as event_time,
    (SELECT COUNT(DISTINCT cc.comment_id) 
     FROM main.log_steam.community_discussions_comments cc 
     WHERE cc.topic_url = ct.url) as reaction_count,
    NULL as sentiment
  FROM main.log_steam.community_discussions_topics ct
  WHERE ct.app_id = 2456740
    AND ct.event_date >= DATE '2025-08-18'
    AND ct.event_date <= DATE '2025-08-25'
    AND ct.content IS NOT NULL
),
platform_stats AS (
  SELECT 
    platform,
    COUNT(DISTINCT content_id) as total_content,
    SUM(reaction_count) as total_reactions,
    AVG(reaction_count) as avg_reactions,
    MAX(reaction_count) as max_reactions,
    COUNT(CASE WHEN sentiment = 'positive' THEN 1 END) as positive_count,
    COUNT(CASE WHEN sentiment = 'negative' THEN 1 END) as negative_count
  FROM integrated_data
  GROUP BY platform
),
overall_stats AS (
  SELECT 
    COUNT(DISTINCT content_id) as total_content_all,
    SUM(reaction_count) as total_reactions_all,
    COUNT(CASE WHEN sentiment = 'positive' THEN 1 END) as total_positive,
    COUNT(CASE WHEN sentiment = 'negative' THEN 1 END) as total_negative,
    ROUND(COUNT(CASE WHEN sentiment = 'positive' THEN 1 END) * 100.0 / 
          NULLIF(COUNT(CASE WHEN sentiment IN ('positive', 'negative') THEN 1 END), 0), 2) as positive_ratio
  FROM integrated_data
)
SELECT 
  '=== 통합 소셜 반응 통계 ===' as section,
  CAST(total_content_all AS STRING) || '개 콘텐츠, ' || 
  CAST(total_reactions_all AS STRING) || '개 반응, ' ||
  CAST(COALESCE(positive_ratio, 0) AS STRING) || '% 긍정 (스팀 리뷰 기준)' as detail
FROM overall_stats

UNION ALL

SELECT 
  '플랫폼별 통계' as section,
  platform || ': ' || total_content || '개 콘텐츠, ' || total_reactions || '개 반응, ' ||
  COALESCE(CAST(positive_count AS STRING), 'N/A') || '개 긍정, ' ||
  COALESCE(CAST(negative_count AS STRING), 'N/A') || '개 부정' as detail
FROM platform_stats
ORDER BY total_reactions DESC;
```

*참고: 통합 요약은 AI 기반 크로스 플랫폼 분석이 필요하므로, 현재는 통합 통계(전체 콘텐츠 수, 반응 수, 긍정 비율)만 제공합니다. 실제 주요 반응 요약을 위해서는 디스코드 메시지와 스팀 리뷰/토픽을 함께 분석하여 플랫폼 간 공통 주제, 차별화된 반응, 전체적인 감성 트렌드 등을 LLM으로 종합 요약해야 합니다.*

**쿼리 결과 (2025-08-18 ~ 2025-08-25, app_id: 2456740):**

| section | detail |
|---------|--------|
| === 통합 소셜 반응 통계 === | 117719개 콘텐츠, 6810270개 반응, 58.53% 긍정 (스팀 리뷰 기준) |
| 플랫폼별 통계 | steam_topic: 352개 콘텐츠, 219795개 반응, 0개 긍정, 0개 부정 |
| 플랫폼별 통계 | discord: 115454개 콘텐츠, 5634327개 반응, 0개 긍정, 0개 부정 |
| 플랫폼별 통계 | steam_review: 1913개 콘텐츠, 956148개 반응, 112377개 긍정, 79606개 부정 |

---

## 💬 광범위한 탐색 질문

### 30-36. 모호하지만 광범위한 질문들

**필요한 테이블:**
- 모든 소셜 플랫폼 테이블 (디스코드, 스팀)
- `main.log_steam.steam_app_id`

**필요한 컬럼:**
- 각 플랫폼별 활동 지표 및 내용

**조인 관계:**
- 게임 코드 기준으로 통합

**필터링 조건:**
- `message.game_code` = '게임코드'
- `steam_app_id.game_code` = '게임코드'
- `event_date` 기준으로 시간 범위 필터링 (질문에 따라 다름, 각 테이블의 `event_date` 컬럼 사용)

**집계 방식:**
- AI 기반 광범위한 탐색
- 플랫폼별 주요 활동 지표 집계
- AI 기반 종합 요약
- 주요 이슈별 상세 요약
- 원본 메시지 출력

---

## 📋 공통 참고사항

### 게임 코드 매핑
- 디스코드: `message.game_code` 또는 `channel_list.game_code` 직접 사용
- 스팀: `steam_app_id.game_code`를 통해 매핑
  ```sql
  WHERE app_id IN (SELECT app_id FROM steam_app_id WHERE game_code = '게임코드')
  ```

**KRAFTON 게임 매핑 (예시 쿼리에서 사용):**

| Steam App ID | 게임명 (Game Name) | Discord game_code | 비고 |
|--------------|--------------------|-------------------|------|
| 2456740 | inZOI | inzoi | 기본 게임 |
| 1062520 | Dinkum | dko | 게임 비교용 |

*참고: 
- 기본적으로 모든 단일 게임 분석 쿼리는 **inZOI (app_id: 2456740, game_code: inzoi)**를 기준으로 작성되어 있습니다.
- 게임 비교가 필요한 경우 **inZOI, Dinkum** 두 게임을 비교 예시로 사용할 수 있습니다.
- 일부 게임은 Discord 전용 또는 Steam 전용 커뮤니티를 운영할 수 있으므로, 쿼리 작성 시 `LEFT JOIN`이나 `FULL OUTER JOIN`을 사용하여 누락 없이 데이터를 조회해야 합니다.*

### 시간 필터링
- **기본 필터링 (필수)**: 모든 테이블의 `event_date` 컬럼 사용 (DATE 타입)
  - 디스코드: `message.event_date`
  - 스팀 리뷰: `store_appreviews.event_date`
  - 스팀 토픽: `community_discussions_topics.event_date`
  - 스팀 코멘트: `community_discussions_comments.event_date`
- **세밀한 시간대 분석 (선택적)**: 시간대별 그룹핑 및 정렬에만 사용
  - 디스코드: `message.created_at` (timestamp 타입)
  - 스팀: `FROM_UNIXTIME(timestamp_created)` 또는 `FROM_UNIXTIME(timestamp)` (bigint → timestamp 변환)

### 원본 메시지 출력
- 디스코드: `message.message` (실제 컬럼명)
- 스팀 리뷰: `store_appreviews.review`
- 스팀 커뮤니티: `community_discussions_topics.content`, `community_discussions_comments.content`

