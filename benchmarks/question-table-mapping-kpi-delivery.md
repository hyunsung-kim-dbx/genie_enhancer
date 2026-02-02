# KPI 수치형 질문별 테이블 및 데이터 매핑

## 📊 지표 관련 질문

### 1. 디스코드에서 리액션이 가장 많은 메시지는 무엇인가요?

**필요한 테이블:**
- `main.log_discord.message`
- `main.log_discord.reaction`
- `main.log_discord.channel_list` (선택적)

**필요한 컬럼:**
- `message.message_id`, `message.content`, `message.created_at`, `message.channel_id`, `message.author_id`
- `reaction.reaction_id`, `reaction.message_id`, `reaction.emoji_name` (선택적)
- `channel_list.channel_name` (선택적)

**조인 관계:**
```sql
message LEFT JOIN reaction ON message.message_id = reaction.message_id
(선택적) JOIN channel_list ON message.channel_id = channel_list.channel_id
```

**필터링 조건:**
- `message.game_code` = '게임코드'
- `message.event_date` 기준으로 기간 필터링 (예: `event_date >= DATE '2025-08-18'`)
- `message.created_at`은 정렬 및 표시에만 사용

**집계 방식:**
- `reaction.reaction_id`를 `COUNT(DISTINCT)` 또는 `COUNT(*)`로 집계
- `message.message_id`별로 그룹핑하여 리액션 수가 많은 메시지 순으로 정렬

**예시 쿼리:**
```sql
SELECT 
  m.message_id,
  m.created_at,
  c.channel_name,
  COALESCE(SUM(r.count), 0) as reaction_count,
  COUNT(DISTINCT r.emoji_name) as unique_emojis,
  STRING_AGG(DISTINCT r.emoji_name, ', ') as emoji_list
FROM main.log_discord.message m
LEFT JOIN main.log_discord.reaction r ON m.message_id = r.message_id
LEFT JOIN main.log_discord.channel_list c ON m.channel_id = c.channel_id
WHERE m.game_code = 'inzoi'
  AND m.event_date >= DATE '2025-07-26'
  AND m.event_date <= DATE '2025-08-25'
GROUP BY m.message_id, m.created_at, c.channel_name
HAVING COALESCE(SUM(r.count), 0) > 0
ORDER BY reaction_count DESC
LIMIT 20;
```

**쿼리 결과 (2025-07-26 ~ 2025-08-25, app_id: 2456740):**

| message_id | created_at | channel_name | reaction_count | unique_emojis | emoji_list |
|------------|------------|--------------|----------------|---------------|------------|
| 1408450871041458367 | 2025-08-22T14:00:55.408Z | service-notice | 317415 | 3 | Psycat_ThumbsUp, psycat_cahaya, Icon_Heart |
| 1407693181922971789 | 2025-08-20T11:50:08.245Z | service-notice | 305910 | 3 | Psycat_ThumbsUp, psycat_cahaya, Icon_Heart |
| 1406527394835202118 | 2025-08-17T06:37:42.944Z | announcements | 234213 | 3 | Psycat_ThumbsUp, psycat_cahaya, Icon_Heart |
| 1407713991798558902 | 2025-08-20T13:12:49.706Z | service-notice | 172752 | 3 | Icon_Heart, Psycat_ThumbsUp, psycat_cahaya |
| 1407605526677684325 | 2025-08-20T06:01:49.606Z | announcements | 171762 | 3 | psycat_cahaya, Icon_Heart, Psycat_ThumbsUp |
| 1404995686813929556 | 2025-08-13T01:11:15.294Z | announcements | 165447 | 3 | Doodle_Heart, Icon_Heart, Psycat_ThumbsUp |
| 1408332975224918026 | 2025-08-22T06:12:26.855Z | announcements | 165432 | 3 | Psycat_ThumbsUp, psycat_cahaya, Icon_Heart |
| 1406677937016799414 | 2025-08-17T16:35:54.997Z | announcements | 141999 | 3 | Psycat_ThumbsUp, Icon_Heart, psycat_cahaya |
| 1407424163593060494 | 2025-08-19T18:01:09.277Z | announcements | 112938 | 3 | Psycat_ThumbsUp, Icon_Heart, psycat_cahaya |
| 1409418113161629706 | 2025-08-25T06:04:23.900Z | service-notice | 102162 | 3 | psycat_cahaya, Icon_Heart, Psycat_ThumbsUp |

---

### 2. 스팀 리뷰에서 추천 수가 높은 리뷰는 무엇인가요?

**필요한 테이블:**
- `main.log_steam.store_appreviews`
- `main.log_steam.steam_app_id` (선택적)

**필요한 컬럼:**
- `store_appreviews.recommendationid`, `store_appreviews.review`, `store_appreviews.votes_up`, `store_appreviews.voted_up`, `store_appreviews.weighted_vote_score`, `store_appreviews.timestamp_created`, `store_appreviews.app_id`
- `steam_app_id.game_code` (필터링용)

**조인 관계:**
```sql
store_appreviews 
WHERE app_id IN (SELECT app_id FROM steam_app_id WHERE game_code = '게임코드')
```

**필터링 조건:**
- `steam_app_id.game_code` = '게임코드' (또는 `app_id` 직접 필터링)
- `store_appreviews.event_date` 기준으로 기간 필터링 (예: `event_date >= DATE '2025-08-18'`)
- `FROM_UNIXTIME(timestamp_created)`는 정렬 및 표시에만 사용

**집계 방식:**
- `votes_up` 또는 `weighted_vote_score` 기준으로 내림차순 정렬
- `recommendationid`별로 그룹핑

**예시 쿼리:**
```sql
SELECT 
  sa.recommendationid,
  FROM_UNIXTIME(sa.timestamp_created) as created_at,
  sa.votes_up,
  sa.votes_funny,
  sa.weighted_vote_score,
  sa.voted_up,
  sa.comment_count
FROM main.log_steam.store_appreviews sa
WHERE sa.app_id = 2456740
  AND sa.event_date >= DATE '2025-07-26'
  AND sa.event_date <= DATE '2025-08-25'
ORDER BY sa.votes_up DESC, sa.weighted_vote_score DESC
LIMIT 20;
```

**쿼리 결과 (2025-07-26 ~ 2025-08-25, app_id: 2456740):**

| recommendationid | created_at | votes_up | votes_funny | weighted_vote_score | voted_up | comment_count |
|------------------|------------|----------|-------------|---------------------|----------|---------------|
| 200642239 | 2025-07-25 04:39:25 | 2112 | 42 | 0.837083 | false | 60 |
| 200642239 | 2025-07-25 04:39:25 | 2100 | 41 | 0.836752 | false | 60 |
| 200642239 | 2025-07-25 04:39:25 | 2094 | 41 | 0.836799 | false | 60 |
| 200642239 | 2025-07-25 04:39:25 | 2079 | 41 | 0.836441 | false | 60 |
| 200642239 | 2025-07-25 04:39:25 | 2062 | 39 | 0.837581 | false | 60 |
| 200642239 | 2025-07-25 04:39:25 | 1977 | 36 | 0.837426 | false | 56 |
| 200642239 | 2025-07-25 04:39:25 | 1950 | 36 | 0.837702 | false | 56 |
| 200642239 | 2025-07-25 04:39:25 | 1897 | 34 | 0.837864 | false | 56 |
| 200642239 | 2025-07-25 04:39:25 | 1873 | 33 | 0.837185 | false | 54 |
| 200642239 | 2025-07-25 04:39:25 | 1862 | 33 | 0.837801 | false | 54 |

*참고: `created_at`은 실제 리뷰 작성 시간(`timestamp_created`)이고, `event_date`는 데이터 수집/처리 날짜입니다. 따라서 `created_at`이 필터 기간보다 이전일 수 있습니다. 쿼리는 `event_date` 기준으로 필터링되므로 정상입니다.*

---

### 5. 스팀 커뮤니티에서 댓글이 많이 달린 토픽은 무엇인가요?

**필요한 테이블:**
- `main.log_steam.community_discussions_topics`
- `main.log_steam.community_discussions_comments`
- `main.log_steam.steam_app_id`

**필요한 컬럼:**
- `community_discussions_topics.topic_id`, `community_discussions_topics.title`, `community_discussions_topics.content`, `community_discussions_topics.timestamp`, `community_discussions_topics.app_id`
- `community_discussions_comments.comment_id`, `community_discussions_comments.topic_url`, `community_discussions_comments.content`

**조인 관계:**
```sql
community_discussions_topics 
LEFT JOIN community_discussions_comments ON topics.url = comments.topic_url
WHERE topics.app_id IN (SELECT app_id FROM steam_app_id WHERE game_code = '게임코드')
```

**필터링 조건:**
- `steam_app_id.game_code` = '게임코드'
- `community_discussions_topics.event_date` 기준으로 기간 필터링 (예: `event_date >= DATE '2025-08-18'`)
- `FROM_UNIXTIME(topics.timestamp)`는 정렬 및 표시에만 사용

**집계 방식:**
- `topics.topic_id`별로 `COUNT(DISTINCT comments.comment_id)` 집계
- 댓글 수 기준 내림차순 정렬

**예시 쿼리:**
```sql
SELECT 
  ct.topic_id,
  ct.title as topic_title,
  FROM_UNIXTIME(ct.timestamp) as created_at,
  ct.subforum,
  COUNT(DISTINCT cc.comment_id) as comment_count,
  COUNT(DISTINCT cc.author) as unique_commenters,
  MAX(FROM_UNIXTIME(cc.timestamp)) as last_comment_time
FROM main.log_steam.community_discussions_topics ct
LEFT JOIN main.log_steam.community_discussions_comments cc 
  ON ct.url = cc.topic_url
WHERE ct.app_id = 2456740
  AND ct.event_date >= DATE '2025-07-26'
  AND ct.event_date <= DATE '2025-08-25'
  AND FROM_UNIXTIME(ct.timestamp) >= TIMESTAMP '2025-07-26 00:00:00'
  AND FROM_UNIXTIME(ct.timestamp) <= TIMESTAMP '2025-08-25 23:59:59'
  AND (cc.comment_id IS NULL OR cc.is_deleted = false)
GROUP BY ct.topic_id, ct.title, ct.timestamp, ct.subforum
HAVING COUNT(DISTINCT cc.comment_id) > 0
ORDER BY comment_count DESC
LIMIT 20;
```

**쿼리 결과 (2025-07-26 ~ 2025-08-25에 생성된 토픽, app_id: 2456740):**

| topic_id | topic_title | created_at | subforum | comment_count | unique_commenters | last_comment_time |
|----------|-------------|------------|----------|---------------|-------------------|-------------------|
| 599659270907182863 | building mode is real bad | 2025-07-27 21:00:51 | General Discussions | 25 | 6 | 2025-07-29 08:41:58 |
| 599661451928477335 | Gay people aren't real? (In game) | 2025-08-20 21:43:11 | General Discussions | 20 | 9 | 2025-08-21 11:55:21 |
| 615423851387539585 | High Priority Issues in the August 20 Update | 2025-08-19 01:00:07 | Events & Announcements | 20 | 23 | 2025-08-19 09:34:03 |
| 599660183449507201 | Please stop bumping hate threads instead real gameplay issues to solve. | 2025-08-09 01:28:39 | General Discussions | 19 | 10 | 2025-08-11 16:02:33 |
| 594031317713177497 | 40$ game and the first "major" content is locked behind dlc. | 2025-08-13 05:11:19 | General Discussions | 19 | 13 | 2025-08-15 22:03:24 |
| 599661451928421594 | [v0.3.0 & DLC] Patch Notes | 2025-08-20 06:01:30 | Events & Announcements | 17 | 16 | 2025-08-20 07:37:04 |
| 599660572366250664 | Reminder: inZOI@Cahaya Broadcast Details | 2025-08-12 01:00:52 | Events & Announcements | 17 | 53 | 2025-08-12 09:59:30 |
| 599660572366214443 | Moderators, please activate bug and feedback forums etc. | 2025-08-11 16:50:49 | General Discussions | 17 | 6 | 2025-08-14 09:17:58 |
| 594031317713248725 | Cahaya island free DLC facts | 2025-08-13 20:15:29 | General Discussions | 17 | 8 | 2025-08-16 07:03:58 |
| 599661851858499949 | [v0.3.3] Hotfix Details | 2025-08-25 06:04:17 | Events & Announcements | 17 | 30 | 2025-08-25 12:37:08 |

---

### 7. 디스코드에서 가장 활발한 채널은 어디인가요?

**필요한 테이블:**
- `main.log_discord.channel_list`
- `main.log_discord.message`
- `main.log_discord.reaction` (선택적)

**필요한 컬럼:**
- `channel_list.channel_id`, `channel_list.channel_name`, `channel_list.server_id`, `channel_list.game_code`
- `message.message_id`, `message.channel_id`, `message.created_at`
- `reaction.reaction_id` (선택적)

**조인 관계:**
```sql
channel_list 
JOIN message ON channel_list.channel_id = message.channel_id
LEFT JOIN reaction ON message.message_id = reaction.message_id
```

**필터링 조건:**
- `channel_list.game_code` = '게임코드'
- `message.event_date` 기준으로 기간 필터링 (예: `event_date >= DATE '2025-08-18'`)
- `message.created_at`은 시간대별 분석 및 표시에만 사용

**집계 방식:**
- `channel_list.channel_id`별로 그룹핑
- `COUNT(DISTINCT message.message_id)` (메시지 수)
- `COUNT(DISTINCT reaction.reaction_id)` (리액션 수, 선택적)
- 활발도 지표 = 메시지 수 + 리액션 수 (또는 가중치 적용)

**예시 쿼리:**
```sql
SELECT 
  c.channel_id,
  c.channel_name,
  c.guild_id,
  COUNT(DISTINCT m.message_id) as message_count,
  COUNT(DISTINCT m.author_id) as unique_authors,
  COALESCE(SUM(r.count), 0) as reaction_count,
  COUNT(DISTINCT r.emoji_name) as unique_reactors,
  COUNT(DISTINCT m.message_id) + COALESCE(SUM(r.count), 0) * 0.5 as activity_score,
  MIN(m.created_at) as first_message_time,
  MAX(m.created_at) as last_message_time
FROM main.log_discord.channel_list c
INNER JOIN main.log_discord.message m ON c.channel_id = m.channel_id
LEFT JOIN main.log_discord.reaction r ON m.message_id = r.message_id
WHERE c.game_code = 'inzoi'
  AND m.event_date >= DATE '2025-07-26'
  AND m.event_date <= DATE '2025-08-25'
GROUP BY c.channel_id, c.channel_name, c.guild_id
ORDER BY activity_score DESC
LIMIT 20;
```

**쿼리 결과 (2025-08-18 ~ 2025-08-25, app_id: 2456740):**

| channel_id | channel_name | guild_id | message_count | unique_authors | reaction_count | unique_reactors | activity_score | first_message_time | last_message_time |
|------------|--------------|----------|---------------|----------------|----------------|-----------------|----------------|-------------------|-------------------|
| 1162040845181124621 | inzoi-chat | 1162040845181124618 | 57788 | 2208 | 1347414 | 354 | 731495.0 | 2025-06-18T10:38:20.599Z | 2025-08-25T23:57:08.073Z |
| 1207578601008926791 | announcements | 1162040845181124618 | 38 | 4 | 1325394 | 4 | 662735.0 | 2025-06-19T03:14:28.431Z | 2025-08-22T06:12:26.855Z |
| 1275647854890979470 | service-notice | 1162040845181124618 | 18 | 1 | 1171821 | 3 | 585928.5 | 2025-06-19T08:30:40.848Z | 2025-08-25T06:04:23.900Z |
| 1352689895386382346 | share-your-zoi | 1162040845181124618 | 990 | 289 | 445604 | 26 | 223792.0 | 2025-06-18T10:29:49.291Z | 2025-08-25T23:14:03.904Z |
| 1387652526156808283 | brainstorm-with-kjun | 1162040845181124618 | 2365 | 665 | 293743 | 54 | 149236.5 | 2025-06-27T08:32:05.961Z | 2025-08-25T23:59:38.329Z |
| 1174875129906462801 | mod-chat | 1162040845181124618 | 8774 | 28 | 123831 | 130 | 70689.5 | 2025-06-18T10:49:47.668Z | 2025-08-25T23:59:43.973Z |
| 1409612249835896852 | cahaya-treasure-hunt-event | 1162040845181124618 | 2 | 1 | 96997 | 32 | 48500.5 | 2025-08-25T19:06:39.217Z | 2025-08-25T19:07:22.247Z |
| 1349133210100961300 | inzoi-feedback | 1162040845181124618 | 2149 | 445 | 78828 | 32 | 41563.0 | 2025-06-18T11:16:36.659Z | 2025-08-25T23:07:35.738Z |
| 1356166900836466829 | partners-chat | 1162040845181124618 | 1009 | 83 | 75921 | 46 | 38969.5 | 2025-06-18T22:35:13.023Z | 2025-08-25T23:05:18.179Z |
| 1353910961760637121 | gameplay-questions | 1162040845181124618 | 5788 | 735 | 65670 | 65 | 38623.0 | 2025-06-18T15:06:07.476Z | 2025-08-25T23:52:56.042Z |

---

### 8. 시간대별로 언급량이 가장 많은 시간은 언제인가요?

**필요한 테이블:**
- `main.log_discord.message`
- `main.log_steam.store_appreviews` (선택적)
- `main.log_steam.community_discussions_topics` (선택적)

**필요한 컬럼:**
- 디스코드: `message.created_at` (timestamp)
- 스팀: `store_appreviews.timestamp_created` (bigint), `community_discussions_topics.timestamp` (bigint)

**조인 관계:**
- 각 플랫폼별로 독립적으로 집계 후 통합 (UNION ALL)

**필터링 조건:**
- `message.game_code` = '게임코드' (디스코드)
- `steam_app_id.game_code` = '게임코드' (스팀)
- `event_date` 기준으로 시간 범위 필터링 (각 테이블의 `event_date` 컬럼 사용)
- `created_at`, `timestamp_created`, `timestamp`는 시간대별 그룹핑에만 사용

**집계 방식:**
- 시간대별 그룹핑: `HOUR(created_at)` 또는 `DATE_TRUNC('hour', created_at)`
- `COUNT(DISTINCT message_id)` 또는 `COUNT(*)` 집계
- 시간대별 언급량 내림차순 정렬

**예시 쿼리:**
```sql
WITH hourly_mentions AS (
  SELECT 
    HOUR(m.created_at) as hour_of_day,
    DATE_TRUNC('hour', m.created_at) as hour_bucket,
    COUNT(DISTINCT m.message_id) as mention_count,
    COUNT(DISTINCT m.author_id) as unique_authors,
    'discord' as platform
  FROM main.log_discord.message m
  WHERE m.game_code = 'inzoi'
    AND m.event_date >= DATE '2025-08-18'
  AND m.event_date <= DATE '2025-08-25'
  GROUP BY HOUR(m.created_at), DATE_TRUNC('hour', m.created_at)
  
  UNION ALL
  
  SELECT 
    HOUR(FROM_UNIXTIME(sa.timestamp_created)) as hour_of_day,
    DATE_TRUNC('hour', FROM_UNIXTIME(sa.timestamp_created)) as hour_bucket,
    COUNT(DISTINCT sa.recommendationid) as mention_count,
    NULL as unique_authors,
    'steam_review' as platform
  FROM main.log_steam.store_appreviews sa
  WHERE sa.app_id = 2456740
    AND sa.event_date >= DATE '2025-08-18'
  AND sa.event_date <= DATE '2025-08-25'
  GROUP BY HOUR(FROM_UNIXTIME(sa.timestamp_created)), 
           DATE_TRUNC('hour', FROM_UNIXTIME(sa.timestamp_created))
  
  UNION ALL
  
  SELECT 
    HOUR(FROM_UNIXTIME(ct.timestamp)) as hour_of_day,
    DATE_TRUNC('hour', FROM_UNIXTIME(ct.timestamp)) as hour_bucket,
    COUNT(DISTINCT ct.topic_id) as mention_count,
    COUNT(DISTINCT ct.author) as unique_authors,
    'steam_topic' as platform
  FROM main.log_steam.community_discussions_topics ct
  WHERE ct.app_id = 2456740
    AND ct.event_date >= DATE '2025-08-18'
  AND ct.event_date <= DATE '2025-08-25'
  GROUP BY HOUR(FROM_UNIXTIME(ct.timestamp)), 
           DATE_TRUNC('hour', FROM_UNIXTIME(ct.timestamp))
)
SELECT 
  hour_of_day,
  SUM(mention_count) as total_mentions,
  SUM(COALESCE(unique_authors, 0)) as total_unique_authors,
  COUNT(DISTINCT platform) as platform_count,
  STRING_AGG(DISTINCT platform, ', ') as platforms,
  ROUND(AVG(mention_count), 2) as avg_mentions_per_hour
FROM hourly_mentions
GROUP BY hour_of_day
ORDER BY total_mentions DESC;
```

**쿼리 결과 (2025-08-18 ~ 2025-08-25, app_id: 2456740):**

| hour_of_day | total_mentions | total_unique_authors | platform_count | platforms | avg_mentions_per_hour |
|-------------|----------------|----------------------|----------------|-----------|----------------------|
| 15 | 7436 | 1728 | 3 | steam_topic, steam_review, discord | 66.39 |
| 17 | 7243 | 1640 | 3 | steam_topic, steam_review, discord | 58.89 |
| 16 | 6547 | 1672 | 3 | steam_topic, steam_review, discord | 57.94 |
| 14 | 6364 | 1612 | 3 | steam_topic, steam_review, discord | 53.93 |
| 1 | 6215 | 1289 | 3 | steam_topic, steam_review, discord | 55.99 |
| 18 | 5773 | 1530 | 3 | steam_topic, steam_review, discord | 49.34 |
| 19 | 5637 | 1413 | 3 | steam_topic, steam_review, discord | 49.02 |
| 22 | 5507 | 1298 | 3 | steam_topic, steam_review, discord | 52.45 |
| 2 | 5408 | 1123 | 3 | steam_topic, steam_review, discord | 49.61 |
| 20 | 5240 | 1346 | 3 | steam_topic, steam_review, discord | 44.41 |

---

## 😊😢 감성 분석 질문

### 12. 디스코드와 스팀에서 긍정/부정 비율은 어떻게 다른가요?

**필요한 테이블:**
- `main.log_discord.message`
- `main.log_steam.store_appreviews`
- `main.log_steam.steam_app_id`

**필요한 컬럼:**
- 디스코드: `message.content`, `message.message_id`
- 스팀: `store_appreviews.voted_up`, `store_appreviews.recommendationid`

**조인 관계:**
- 각 플랫폼별로 독립적으로 집계 후 비교

**필터링 조건:**
- `message.game_code` = '게임코드' (디스코드)
- `steam_app_id.game_code` = '게임코드' (스팀)
- 동일한 `event_date` 기준 시간 범위 적용 (각 테이블의 `event_date` 컬럼 사용)

**집계 방식:**
- 디스코드: AI 기반 감성 분류 또는 키워드 기반 분류
- 스팀: `voted_up = true/false` 기준
- 플랫폼별 긍정/부정 비율 계산

**예시 쿼리:**
```sql
WITH discord_stats AS (
  SELECT 
    COUNT(DISTINCT m.message_id) as message_count,
    COUNT(DISTINCT m.author_id) as unique_authors,
    COALESCE(SUM(r.count), 0) as total_reactions
  FROM main.log_discord.message m
  LEFT JOIN main.log_discord.reaction r ON m.message_id = r.message_id
  WHERE m.game_code = 'inzoi'
    AND m.event_date >= DATE '2025-08-18'
  AND m.event_date <= DATE '2025-08-25'
    AND m.message IS NOT NULL
    AND LENGTH(m.message) > 5
),
steam_sentiment AS (
  SELECT 
    CASE 
      WHEN sa.voted_up = true THEN 'positive'
      WHEN sa.voted_up = false THEN 'negative'
    END as sentiment,
    COUNT(DISTINCT sa.recommendationid) as review_count,
    SUM(sa.votes_up) as total_votes_up
  FROM main.log_steam.store_appreviews sa
  WHERE sa.app_id = 2456740
    AND sa.event_date >= DATE '2025-08-18'
  AND sa.event_date <= DATE '2025-08-25'
  GROUP BY sa.voted_up
),
steam_summary AS (
  SELECT 
    sentiment,
    review_count,
    total_votes_up,
    ROUND(review_count * 100.0 / SUM(review_count) OVER (), 2) as percentage
  FROM steam_sentiment
)
SELECT 
  'discord' as platform,
  0 as positive_ratio,
  0 as negative_ratio,
  ds.message_count as total_count,
  ds.total_reactions
FROM discord_stats ds

UNION ALL

SELECT 
  'steam' as platform,
  COALESCE(SUM(CASE WHEN sentiment = 'positive' THEN percentage END), 0) as positive_ratio,
  COALESCE(SUM(CASE WHEN sentiment = 'negative' THEN percentage END), 0) as negative_ratio,
  SUM(review_count) as total_count,
  SUM(total_votes_up) as total_reactions
FROM steam_summary
GROUP BY platform
ORDER BY platform;
```

*참고: Discord의 감성 비율(긍정/부정)은 AI 기반 감성 분석이 필요하므로 현재는 0.00으로 표시됩니다. Steam은 `voted_up` 컬럼(boolean: true/false)으로 긍정/부정을 명확히 구분할 수 있지만, Discord 메시지는 텍스트 내용을 LLM이나 감성 분석 모델로 분석해야 감성을 판별할 수 있습니다. 따라서 플랫폼 간 감성 비율 비교는 제한적이며, `total_count`와 `total_reactions` 같은 양적 지표 비교가 더 유의미합니다.*

**쿼리 결과 (2025-08-18 ~ 2025-08-25, app_id: 2456740):**

| platform | positive_ratio | negative_ratio | total_count | total_reactions |
|----------|---------------|----------------|-------------|-----------------|
| discord | 0.00 | 0.00 | 106867 | 5482587 |
| steam | 60.94 | 39.06 | 1933 | 956148 |

---

## 🔄 비교 분석 질문

### 13. 게임별로 소셜 반응을 비교해주세요

**필요한 테이블:**
- `main.log_discord.message`
- `main.log_discord.reaction`
- `main.log_steam.store_appreviews`
- `main.log_steam.community_discussions_topics`
- `main.log_steam.steam_app_id`

**필요한 컬럼:**
- `message.game_code` (디스코드)
- `steam_app_id.game_code` (스팀)
- 각 플랫폼별 활동 지표

**조인 관계:**
- 게임 코드 기준으로 그룹핑

**필터링 조건:**
- 여러 게임 코드 필터링: `game_code IN ('GAME1', 'GAME2', ...)`
- `event_date` 기준으로 시간 범위 필터링 (각 테이블의 `event_date` 컬럼 사용)
- **중요**: Discord와 Steam 데이터를 비교할 때는 동일한 기간으로 필터링 (예: Discord 데이터가 2025-08-18부터 가용한 경우, Steam도 2025-08-18부터 조회하여 공정한 비교)

**집계 방식:**
- `game_code`별로 그룹핑
- 플랫폼별 활동 지표 집계

**예시 쿼리:**
```sql
-- inzoi (2456740), dko/Dinkum (1062520) 두 게임 비교
WITH game_info AS (
  SELECT 'inZOI' as game_name, 'inzoi' as game_code, 2456740 as app_id
  UNION ALL
  SELECT 'Dinkum' as game_name, 'dko' as game_code, 1062520 as app_id
),
discord_activity AS (
  SELECT 
    m.game_code,
    COUNT(DISTINCT m.message_id) as message_count,
    COALESCE(SUM(r.count), 0) as reaction_count,
    COUNT(DISTINCT m.author_id) as unique_authors,
    COUNT(DISTINCT m.channel_id) as active_channels
  FROM main.log_discord.message m
  LEFT JOIN main.log_discord.reaction r ON m.message_id = r.message_id
  WHERE m.game_code IN ('inzoi', 'dko')
    AND m.event_date >= DATE '2025-08-18'
    AND m.event_date <= DATE '2025-08-25'
  GROUP BY m.game_code
),
steam_activity AS (
  SELECT 
    sa.app_id,
    COUNT(DISTINCT sa.recommendationid) as review_count,
    SUM(sa.votes_up) as total_votes_up,
    AVG(sa.votes_up) as avg_votes_up,
    COUNT(DISTINCT CASE WHEN sa.voted_up = true THEN sa.recommendationid END) as positive_reviews,
    COUNT(DISTINCT CASE WHEN sa.voted_up = false THEN sa.recommendationid END) as negative_reviews
  FROM main.log_steam.store_appreviews sa
  WHERE sa.app_id IN (2456740, 1062520)
    AND sa.event_date >= DATE '2025-08-18'
    AND sa.event_date <= DATE '2025-08-25'
  GROUP BY sa.app_id
)
SELECT 
  gi.game_name,
  COALESCE(d.message_count, 0) as discord_messages,
  COALESCE(d.reaction_count, 0) as discord_reactions,
  COALESCE(d.unique_authors, 0) as discord_authors,
  COALESCE(d.active_channels, 0) as discord_channels,
  COALESCE(s.review_count, 0) as steam_reviews,
  COALESCE(s.total_votes_up, 0) as steam_votes_up,
  ROUND(COALESCE(s.avg_votes_up, 0), 2) as steam_avg_votes,
  COALESCE(s.positive_reviews, 0) as steam_positive,
  COALESCE(s.negative_reviews, 0) as steam_negative,
  COALESCE(d.message_count, 0) + COALESCE(s.review_count, 0) as total_content,
  COALESCE(d.reaction_count, 0) + COALESCE(s.total_votes_up, 0) as total_engagement,
  CASE 
    WHEN COALESCE(s.review_count, 0) > 0 
    THEN ROUND(COALESCE(s.positive_reviews, 0) * 100.0 / s.review_count, 2)
    ELSE NULL
  END as positive_ratio
FROM game_info gi
LEFT JOIN discord_activity d ON gi.game_code = d.game_code
LEFT JOIN steam_activity s ON gi.app_id = s.app_id
ORDER BY total_engagement DESC;
```

**쿼리 결과 (2025-08-18 ~ 2025-08-25, Discord와 Steam 동일 기간 비교):**

| game_name | discord_messages | discord_reactions | discord_authors | discord_channels | steam_reviews | steam_votes_up | steam_avg_votes | steam_positive | steam_negative | total_content | total_engagement | positive_ratio |
|-----------|------------------|-------------------|-----------------|------------------|---------------|----------------|-----------------|----------------|----------------|---------------|------------------|----------------|
| inZOI | 115454 | 5634327 | 4805 | 157 | 1913 | 956148 | 4.98 | 1178 | 755 | 117367 | 6590475 | 61.58 |
| Dinkum | 18924 | 128548 | 3002 | 80 | 1063 | 265696 | 1.38 | 910 | 157 | 19987 | 394244 | 85.61 |

*참고: Discord 데이터가 2025-08-18부터만 조회되므로, 공정한 비교를 위해 Steam 데이터도 동일한 기간(2025-08-18 ~ 2025-08-25)으로 조회했습니다. 두 게임 모두 Discord와 Steam에서 활발한 활동을 보이고 있습니다.*

---

### 15. 이벤트 전후 소셜 반응 변화는 어떻게 되나요?

**필요한 테이블:**
- `main.log_discord.message`
- `main.log_discord.reaction`
- `main.log_steam.store_appreviews`
- `main.log_steam.partner_wishlist` (선택적)
- `main.log_steam.steam_app_id`

**필요한 컬럼:**
- `message.created_at` (디스코드)
- `store_appreviews.timestamp_created` (스팀)
- 이벤트 날짜 기준 전후 구분

**조인 관계:**
- 각 플랫폼별로 독립적으로 집계

**필터링 조건:**
- `message.game_code` = '게임코드'
- `steam_app_id.game_code` = '게임코드'
- `event_date` 기준으로 이벤트 전후 기간 필터링 (예: before/during/after)

**집계 방식:**
- 이벤트 전후 구분: `CASE WHEN event_date < event_start_date THEN 'before' ELSE 'after' END`
- 기간별 활동 지표 집계
- 전후 비교: 증감율 계산

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
  GROUP BY 
    CASE 
      WHEN sa.event_date < DATE '2025-08-25' THEN 'before'
      WHEN sa.event_date BETWEEN DATE '2025-08-25' AND DATE '2025-09-01' THEN 'during'
      ELSE 'after'
    END
),
comparison AS (
  SELECT 
    'discord' as platform,
    period,
    message_count,
    reaction_count
  FROM discord_activity
  
  UNION ALL
  
  SELECT 
    'steam' as platform,
    period,
    review_count as message_count,
    total_votes_up as reaction_count
  FROM steam_activity
)
SELECT 
  platform,
  period,
  message_count,
  reaction_count
FROM comparison
ORDER BY platform, 
  CASE period WHEN 'before' THEN 1 WHEN 'during' THEN 2 ELSE 3 END;
```

**쿼리 결과 (2025-08-18 ~ 2025-09-08, 이벤트 기간: 2025-08-25 ~ 2025-09-01, app_id: 2456740):**

| platform | period | message_count | reaction_count |
|----------|--------|---------------|----------------|
| discord | before | 110001 | 5171119 |
| discord | during | 24489 | 2382323 |
| discord | after | 13560 | 1448646 |
| steam | before | 1787 | 847676 |
| steam | during | 1701 | 535890 |
| steam | after | 1447 | 140437 |

---

## ⏰ 기간별 분석 질문

### 19. 주간/월간 트렌드에서 주요 변화는 무엇인가요?

**필요한 테이블:**
- `main.log_discord.message`
- `main.log_discord.reaction`
- `main.log_steam.store_appreviews`
- `main.log_steam.community_discussions_topics`
- `main.log_steam.steam_app_id`

**필요한 컬럼:**
- `message.created_at` (디스코드)
- `store_appreviews.timestamp_created` (스팀)
- 각 플랫폼별 활동 지표

**조인 관계:**
- 각 플랫폼별로 독립적으로 집계

**필터링 조건:**
- `message.game_code` = '게임코드'
- `steam_app_id.game_code` = '게임코드'
- `event_date` 기준으로 주간/월간 기간 필터링 (예: `event_date >= DATE '2025-08-18'`)
- `created_at`, `timestamp_created`는 시간대별 그룹핑에만 사용

**집계 방식:**
- 주간/월간 그룹핑: `DATE_TRUNC('week', created_at)` 또는 `DATE_TRUNC('month', created_at)`
- 기간별 활동 지표 집계
- 전주/전월 대비 변화율 계산: `LAG()` 함수 활용

**예시 쿼리:**
```sql
WITH weekly_activity AS (
  SELECT 
    DATE_TRUNC('week', m.created_at) as week_start,
    COUNT(DISTINCT m.message_id) as message_count,
    COALESCE(SUM(r.count), 0) as reaction_count,
    'discord' as platform
  FROM main.log_discord.message m
  LEFT JOIN main.log_discord.reaction r ON m.message_id = r.message_id
  WHERE m.game_code = 'inzoi'
    AND m.event_date >= DATE '2025-08-18'
    AND m.event_date <= DATE '2025-08-25'
  GROUP BY DATE_TRUNC('week', m.created_at)
  
  UNION ALL
  
  SELECT 
    DATE_TRUNC('week', FROM_UNIXTIME(sa.timestamp_created)) as week_start,
    COUNT(DISTINCT sa.recommendationid) as message_count,
    SUM(sa.votes_up) as reaction_count,
    'steam' as platform
  FROM main.log_steam.store_appreviews sa
  WHERE sa.app_id = 2456740
    AND sa.event_date >= DATE '2025-08-18'
    AND sa.event_date <= DATE '2025-08-25'
  GROUP BY DATE_TRUNC('week', FROM_UNIXTIME(sa.timestamp_created))
),
weekly_summary AS (
  SELECT 
    week_start,
    platform,
    SUM(message_count) as total_messages,
    SUM(reaction_count) as total_reactions
  FROM weekly_activity
  GROUP BY week_start, platform
),
trend_analysis AS (
  SELECT 
    week_start,
    platform,
    total_messages,
    total_reactions,
    LAG(total_messages) OVER (PARTITION BY platform ORDER BY week_start) as prev_messages,
    LAG(total_reactions) OVER (PARTITION BY platform ORDER BY week_start) as prev_reactions,
    CASE 
      WHEN LAG(total_messages) OVER (PARTITION BY platform ORDER BY week_start) > 0
      THEN ROUND((total_messages - LAG(total_messages) OVER (PARTITION BY platform ORDER BY week_start)) * 100.0 
                 / LAG(total_messages) OVER (PARTITION BY platform ORDER BY week_start), 2)
      ELSE NULL
    END as message_change_rate,
    CASE 
      WHEN LAG(total_reactions) OVER (PARTITION BY platform ORDER BY week_start) > 0
      THEN ROUND((total_reactions - LAG(total_reactions) OVER (PARTITION BY platform ORDER BY week_start)) * 100.0 
                 / LAG(total_reactions) OVER (PARTITION BY platform ORDER BY week_start), 2)
      ELSE NULL
    END as reaction_change_rate
  FROM weekly_summary
)
SELECT 
  week_start,
  platform,
  total_messages,
  total_reactions,
  prev_messages,
  prev_reactions,
  message_change_rate,
  reaction_change_rate,
  CASE 
    WHEN ABS(message_change_rate) > 30 THEN '큰 변화'
    WHEN ABS(message_change_rate) > 10 THEN '중간 변화'
    ELSE '작은 변화'
  END as change_magnitude
FROM trend_analysis
ORDER BY week_start DESC, platform;
```

**쿼리 결과 (Discord와 Steam 모두 동일 기간: 2025-08-18 ~ 2025-08-25):**

| week_start | platform | total_messages | total_reactions | prev_messages | prev_reactions | message_change_rate | reaction_change_rate | change_magnitude |
|------------|----------|----------------|-----------------|---------------|----------------|---------------------|----------------------|------------------|
| 2025-08-25T00:00:00.000Z | discord | 5453 | 463208 | 36875 | 3819342 | -85.21 | -87.87 | 큰 변화 |
| 2025-08-25T00:00:00.000Z | steam | 119 | 1279 | 791 | 305921 | -84.96 | -99.58 | 큰 변화 |
| 2025-08-18T00:00:00.000Z | discord | 36875 | 3819342 | 14973 | 1351777 | 146.28 | 182.54 | 큰 변화 |
| 2025-08-18T00:00:00.000Z | steam | 791 | 305921 | 198 | 122364 | 299.49 | 150.01 | 큰 변화 |
| 2025-08-11T00:00:00.000Z | discord | 14973 | 1351777 | 7416 | 0 | 101.90 | NULL | 큰 변화 |
| 2025-08-11T00:00:00.000Z | steam | 198 | 122364 | 163 | 118105 | 21.47 | 3.61 | 중간 변화 |
| 2025-08-04T00:00:00.000Z | discord | 7416 | 0 | 6012 | 0 | 23.35 | NULL | 중간 변화 |
| 2025-08-04T00:00:00.000Z | steam | 163 | 118105 | 154 | 93678 | 5.84 | 26.08 | 작은 변화 |
| 2025-07-28T00:00:00.000Z | discord | 6012 | 0 | 5171 | 0 | 16.26 | NULL | 중간 변화 |
| 2025-07-28T00:00:00.000Z | steam | 154 | 93678 | 159 | 240696 | -3.14 | -61.08 | 작은 변화 |

*참고: 플랫폼 간 공통 지표(total_messages, total_reactions)만 비교하여 명확한 데이터 비교가 가능합니다.*

---

### 20. 최근 일주일 동안 소셜 반응의 주요 변화는 무엇인가요?

**필요한 테이블:**
- `main.log_discord.message`
- `main.log_discord.reaction`
- `main.log_steam.store_appreviews`
- `main.log_steam.community_discussions_topics`
- `main.log_steam.steam_app_id`

**필요한 컬럼:**
- 각 플랫폼별 활동 지표 및 시간 정보

**조인 관계:**
- 각 플랫폼별로 독립적으로 집계 후 통합

**필터링 조건:**
- `message.game_code` = '게임코드'
- `steam_app_id.game_code` = '게임코드'
- `event_date` 기준으로 최근 7일 필터링 (예: `event_date >= DATE '2025-08-18'`)
- `created_at`, `timestamp_created`는 시간대별 분석 및 정렬에만 사용

**집계 방식:**
- 일자별 그룹핑: `event_date`
- 일자별 활동 지표 집계
- 전일 대비 변화율 계산

**예시 쿼리:**
```sql
WITH daily_activity AS (
  SELECT 
    m.event_date as activity_date,
    COUNT(DISTINCT m.message_id) as message_count,
    COALESCE(SUM(r.count), 0) as reaction_count,
    'discord' as platform
  FROM main.log_discord.message m
  LEFT JOIN main.log_discord.reaction r ON m.message_id = r.message_id
  WHERE m.game_code = 'inzoi'
    AND m.event_date >= DATE '2025-08-18'
    AND m.event_date <= DATE '2025-08-25'
  GROUP BY m.event_date
  
  UNION ALL
  
  SELECT 
    sa.event_date as activity_date,
    COUNT(DISTINCT sa.recommendationid) as message_count,
    SUM(sa.votes_up) as reaction_count,
    'steam' as platform
  FROM main.log_steam.store_appreviews sa
  WHERE sa.app_id = 2456740
    AND sa.event_date >= DATE '2025-08-18'
    AND sa.event_date <= DATE '2025-08-25'
  GROUP BY sa.event_date
),
daily_summary AS (
  SELECT 
    activity_date,
    SUM(message_count) as total_messages,
    SUM(reaction_count) as total_reactions,
    COUNT(DISTINCT platform) as platform_count
  FROM daily_activity
  GROUP BY activity_date
),
change_analysis AS (
  SELECT 
    activity_date,
    total_messages,
    total_reactions,
    LAG(total_messages) OVER (ORDER BY activity_date) as prev_messages,
    LAG(total_reactions) OVER (ORDER BY activity_date) as prev_reactions,
    CASE 
      WHEN LAG(total_messages) OVER (ORDER BY activity_date) > 0
      THEN ROUND((total_messages - LAG(total_messages) OVER (ORDER BY activity_date)) * 100.0 
                 / LAG(total_messages) OVER (ORDER BY activity_date), 2)
      ELSE NULL
    END as message_change_rate,
    CASE 
      WHEN LAG(total_reactions) OVER (ORDER BY activity_date) > 0
      THEN ROUND((total_reactions - LAG(total_reactions) OVER (ORDER BY activity_date)) * 100.0 
                 / LAG(total_reactions) OVER (ORDER BY activity_date), 2)
      ELSE NULL
    END as reaction_change_rate
  FROM daily_summary
)
SELECT 
  activity_date,
  total_messages,
  total_reactions,
  prev_messages,
  prev_reactions,
  message_change_rate,
  reaction_change_rate,
  CASE 
    WHEN message_change_rate > 20 THEN '급증'
    WHEN message_change_rate > 5 THEN '증가'
    WHEN message_change_rate < -20 THEN '급감'
    WHEN message_change_rate < -5 THEN '감소'
    ELSE '안정'
  END as trend_direction
FROM change_analysis
ORDER BY activity_date DESC;
```

**쿼리 결과 (2025-08-18 ~ 2025-08-25, app_id: 2456740):**

| activity_date | total_messages | total_reactions | prev_messages | prev_reactions | message_change_rate | reaction_change_rate | trend_direction |
|---------------|----------------|-----------------|---------------|----------------|---------------------|----------------------|-----------------|
| 2025-08-25 | 6578 | 571680 | 4715 | 273452 | 39.51 | 109.06 | 급증 |
| 2025-08-24 | 4715 | 273452 | 4985 | 316931 | -5.42 | -13.72 | 감소 |
| 2025-08-23 | 4985 | 316931 | 5494 | 818574 | -9.26 | -61.28 | 감소 |
| 2025-08-22 | 5494 | 818574 | 6553 | 483427 | -16.16 | 69.33 | 감소 |
| 2025-08-21 | 6553 | 483427 | 11612 | 1537575 | -43.57 | -68.56 | 급감 |
| 2025-08-20 | 11612 | 1537575 | 7464 | 812132 | 55.57 | 89.33 | 급증 |
| 2025-08-19 | 7464 | 812132 | 76968 | 1776704 | -90.30 | -54.29 | 급감 |
| 2025-08-18 | 76968 | 1776704 | NULL | NULL | NULL | NULL | 안정 |

---

## 🌍 지역별 분석 질문

### 21. 국가별로 반응 속도 차이는 어떻게 되나요?

**필요한 테이블:**
- `main.log_steam.partner_regions_and_countries`
- `main.log_steam.store_appreviews`
- `main.log_steam.steam_app_id`

**필요한 컬럼:**
- `partner_regions_and_countries.scope`, `partner_regions_and_countries.name`, `partner_regions_and_countries.wishlists`
- `store_appreviews.timestamp_created`, `store_appreviews.language` (선택적)

**조인 관계:**
```sql
partner_regions_and_countries 
LEFT JOIN store_appreviews ON CAST(partner_regions_and_countries.app_id AS BIGINT) = store_appreviews.app_id
WHERE partner_regions_and_countries.app_id IN (SELECT app_id FROM steam_app_id WHERE game_code = '게임코드')
```

**필터링 조건:**
- `steam_app_id.game_code` = '게임코드'
- `partner_regions_and_countries.scope` = 'country'
- `event_date` 기준으로 시간 범위 필터링 (`partner_regions_and_countries.event_date`, `store_appreviews.event_date`)
- `timestamp_created`는 반응 속도 계산에만 사용

**집계 방식:**
- 국가별 그룹핑: `partner_regions_and_countries.name`
- 국가별 리뷰 생성 시간 분석 (반응 속도)
- 국가별 위시리스트 변화 분석
- 시간대별 반응 속도 차이 분석

**예시 쿼리:**
```sql
-- event_date 기준으로 국가별 리뷰 데이터 집계
WITH country_reviews AS (
  SELECT 
    prc.name as country_name,
    sa.recommendationid,
    FROM_UNIXTIME(sa.timestamp_created) as review_time,
    sa.event_date as review_date,
    HOUR(FROM_UNIXTIME(sa.timestamp_created)) as review_hour,
    sa.voted_up,
    sa.votes_up,
    DATEDIFF(hour, TIMESTAMP '2025-07-28 00:00:00', FROM_UNIXTIME(sa.timestamp_created)) as hours_after_event
  FROM main.log_steam.partner_regions_and_countries prc
  INNER JOIN main.log_steam.store_appreviews sa 
    ON CAST(prc.app_id AS BIGINT) = sa.app_id
    AND sa.event_date = prc.event_date
  WHERE prc.app_id = 2456740
    AND prc.scope = 'country'
    AND sa.event_date >= DATE '2025-07-26'
    AND sa.event_date <= DATE '2025-08-25'
),
country_wishlist AS (
  SELECT 
    prc.name as country_name,
    prc.wishlists,
    prc.units as sales,
    prc.event_date
  FROM main.log_steam.partner_regions_and_countries prc
  WHERE prc.app_id = 2456740
    AND prc.scope = 'country'
    AND prc.event_date >= DATE '2025-07-26'
    AND prc.event_date <= DATE '2025-08-25'
),
peak_hours AS (
  SELECT 
    country_name,
    review_hour,
    COUNT(*) as hour_count,
    ROW_NUMBER() OVER (PARTITION BY country_name ORDER BY COUNT(*) DESC) as rn
  FROM country_reviews
  GROUP BY country_name, review_hour
),
peak_hour_summary AS (
  SELECT 
    country_name,
    review_hour as peak_response_hour
  FROM peak_hours
  WHERE rn = 1
),
country_summary AS (
  SELECT 
    cr.country_name,
    COUNT(DISTINCT cr.recommendationid) as total_reviews,
    AVG(cr.hours_after_event) as avg_response_hours,
    MIN(cr.hours_after_event) as fastest_response_hours,
    COUNT(CASE WHEN cr.hours_after_event <= 24 THEN 1 END) as reviews_within_24h,
    ROUND(COUNT(CASE WHEN cr.hours_after_event <= 24 THEN 1 END) * 100.0 / COUNT(*), 2) as response_rate_24h,
    COUNT(CASE WHEN cr.voted_up = true THEN 1 END) as positive_reviews,
    COUNT(CASE WHEN cr.voted_up = false THEN 1 END) as negative_reviews,
    AVG(cr.votes_up) as avg_votes_up,
    SUM(cw.wishlists) as total_wishlists,
    SUM(cw.sales) as total_sales
  FROM country_reviews cr
  LEFT JOIN country_wishlist cw ON cr.country_name = cw.country_name
  GROUP BY cr.country_name
)
SELECT 
  cs.country_name,
  cs.total_reviews,
  ROUND(cs.avg_response_hours, 2) as avg_response_hours,
  cs.fastest_response_hours,
  cs.reviews_within_24h,
  cs.response_rate_24h,
  cs.positive_reviews,
  cs.negative_reviews,
  ROUND(cs.positive_reviews * 100.0 / NULLIF(cs.total_reviews, 0), 2) as positive_ratio,
  ROUND(cs.avg_votes_up, 2) as avg_votes_up,
  phs.peak_response_hour,
  cs.total_wishlists,
  cs.total_sales,
  RANK() OVER (ORDER BY cs.avg_response_hours ASC) as response_speed_rank,
  RANK() OVER (ORDER BY cs.response_rate_24h DESC) as response_rate_rank
FROM country_summary cs
LEFT JOIN peak_hour_summary phs ON cs.country_name = phs.country_name
ORDER BY cs.avg_response_hours ASC
LIMIT 20;
```

**쿼리 결과 (2025-07-26 ~ 2025-08-25, app_id: 2456740, 상위 20개국):**

| country_name | total_reviews | avg_response_hours | fastest_response_hours | reviews_within_24h | response_rate_24h | positive_reviews | negative_reviews | positive_ratio | avg_votes_up | peak_response_hour | total_wishlists | total_sales | response_speed_rank | response_rate_rank |
|--------------|---------------|--------------------|-----------------------|-------------------|------------------|------------------|------------------|----------------|--------------|-------------------|----------------|-------------|--------------------|--------------------|
| Cameroon | 1015 | -178.16 | -633 | 16939 | 70.59 | 11989 | 12008 | 1181.18 | 4.38 | 17 | 23997 | 0 | 1 | 1 |
| Saint Vincent And The Grenadines | 1215 | -116.03 | -655 | 61726 | 64.30 | 47340 | 48658 | 3896.30 | 4.46 | 14 | 95998 | 0 | 2 | 2 |
| Rwanda | 1063 | -102.04 | -601 | 60246 | 62.78 | 47136 | 48824 | 4434.24 | 4.46 | 17 | 95960 | 0 | 3 | 3 |
| Saint Martin, French Part | 1030 | -88.23 | -581 | 14721 | 61.39 | 11780 | 12201 | 1143.69 | 4.38 | 17 | 23981 | 0 | 4 | 4 |
| Gambia | 1037 | -30.13 | -529 | 13319 | 55.50 | 11774 | 12226 | 1135.39 | 4.65 | 14 | 24000 | 0 | 5 | 5 |
| Antigua And Barbuda | 1037 | -30.13 | -529 | 13319 | 55.50 | 11774 | 12226 | 1135.39 | 4.65 | 14 | 0 | 24000 | 5 | 5 |
| Madagascar | 1510 | -7.04 | -655 | 114270 | 52.90 | 108525 | 107469 | 7187.09 | 4.8 | 14 | 215994 | 0 | 7 | 8 |
| Belize | 1213 | -5.76 | -581 | 50796 | 52.94 | 47530 | 48424 | 3918.38 | 4.68 | 14 | 95954 | 47977 | 8 | 7 |
| Turkmenistan | 1747 | 16.46 | -655 | 188824 | 49.19 | 199052 | 184848 | 11393.93 | 4.56 | 14 | 383900 | 0 | 9 | 10 |
| Gibraltar | 1440 | 21.62 | -608 | 46798 | 49.79 | 47678 | 46314 | 3310.97 | 5.1 | 14 | 46996 | 46996 | 10 | 9 |

*참고: 이 쿼리는 `partner_regions_and_countries`와 `store_appreviews`를 조인하므로, 국가별 위시리스트/판매량과 리뷰 데이터를 함께 보여줍니다. 음수 시간은 기준 시점(2025-07-28) 이전에 작성된 리뷰를 의미합니다.*

---

## 🔗 통합 분석 질문

### 25. 트래픽 증가와 소셜 반응의 연관성은 무엇인가요?

**필요한 테이블:**
- `main.log_steam.partner_traffic`
- `main.log_discord.message`
- `main.log_steam.store_appreviews`
- `main.log_steam.steam_app_id`

**필요한 컬럼:**
- `partner_traffic.visits`, `partner_traffic.event_date`
- `message.created_at`
- `store_appreviews.timestamp_created`

**조인 관계:**
```sql
partner_traffic 
LEFT JOIN message ON message.game_code = 'inzoi' AND message.event_date = partner_traffic.event_date
LEFT JOIN store_appreviews ON CAST(partner_traffic.app_id AS BIGINT) = store_appreviews.app_id
  AND store_appreviews.event_date = partner_traffic.event_date
```

**필터링 조건:**
- `partner_traffic.app_id` = 2456740
- 트래픽 증가 시점 식별
- 해당 시점 전후 소셜 반응 분석

**집계 방식:**
- 트래픽과 소셜 반응의 상관관계 분석
- 트래픽 증가 시점의 소셜 반응 집계

**예시 쿼리:**
```sql
WITH traffic_data AS (
  SELECT 
    pt.event_date,
    pt.app_id,
    SUM(pt.visits) as total_visits,
    SUM(pt.owner_visits) as owner_visits,
    CASE 
      WHEN LAG(SUM(pt.visits)) OVER (PARTITION BY pt.app_id ORDER BY pt.event_date) > 0
      THEN ROUND((SUM(pt.visits) - LAG(SUM(pt.visits)) OVER (PARTITION BY pt.app_id ORDER BY pt.event_date)) * 100.0 
                 / LAG(SUM(pt.visits)) OVER (PARTITION BY pt.app_id ORDER BY pt.event_date), 2)
      ELSE NULL
    END as traffic_growth_rate
  FROM main.log_steam.partner_traffic pt
  WHERE pt.app_id = 2456740
    AND pt.event_date >= DATE '2025-08-18'
    AND pt.event_date <= DATE '2025-08-25'
  GROUP BY pt.event_date, pt.app_id
),
social_data AS (
  SELECT 
    m.event_date as reaction_date,
    COUNT(DISTINCT m.message_id) as message_count,
    COALESCE(SUM(r.count), 0) as reaction_count,
    COUNT(DISTINCT m.author_id) as unique_authors
  FROM main.log_discord.message m
  LEFT JOIN main.log_discord.reaction r ON m.message_id = r.message_id
  WHERE m.game_code = 'inzoi'
    AND m.event_date >= DATE '2025-08-18'
    AND m.event_date <= DATE '2025-08-25'
  GROUP BY m.event_date
  
  UNION ALL
  
  SELECT 
    sa.event_date as reaction_date,
    COUNT(DISTINCT sa.recommendationid) as message_count,
    SUM(sa.votes_up) as reaction_count,
    NULL as unique_authors
  FROM main.log_steam.store_appreviews sa
  WHERE sa.app_id = 2456740
    AND sa.event_date >= DATE '2025-08-18'
    AND sa.event_date <= DATE '2025-08-25'
  GROUP BY sa.event_date
),
social_summary AS (
  SELECT 
    reaction_date,
    SUM(message_count) as total_messages,
    SUM(reaction_count) as total_reactions,
    SUM(COALESCE(unique_authors, 0)) as total_authors
  FROM social_data
  GROUP BY reaction_date
),
correlation_analysis AS (
  SELECT 
    td.event_date,
    td.total_visits,
    td.traffic_growth_rate,
    COALESCE(ss.total_messages, 0) as social_messages,
    COALESCE(ss.total_reactions, 0) as social_reactions,
    COALESCE(ss.total_authors, 0) as social_authors,
    CASE 
      WHEN LAG(COALESCE(ss.total_messages, 0)) OVER (ORDER BY td.event_date) > 0
      THEN ROUND((COALESCE(ss.total_messages, 0) - 
                  LAG(COALESCE(ss.total_messages, 0)) OVER (ORDER BY td.event_date)) * 100.0 
                 / LAG(COALESCE(ss.total_messages, 0)) OVER (ORDER BY td.event_date), 2)
      ELSE NULL
    END as social_growth_rate
  FROM traffic_data td
  LEFT JOIN social_summary ss ON td.event_date = ss.reaction_date
)
SELECT 
  event_date,
  total_visits,
  traffic_growth_rate,
  social_messages,
  social_reactions,
  social_authors,
  social_growth_rate,
  CASE 
    WHEN traffic_growth_rate > 20 AND social_growth_rate > 20 THEN '강한 양의 상관관계'
    WHEN traffic_growth_rate > 20 AND social_growth_rate < -20 THEN '강한 음의 상관관계'
    WHEN traffic_growth_rate < -20 AND social_growth_rate > 20 THEN '역상관관계'
    WHEN ABS(traffic_growth_rate) < 10 AND ABS(social_growth_rate) < 10 THEN '약한 상관관계'
    ELSE '중간 상관관계'
  END as correlation_type,
  CASE 
    WHEN traffic_growth_rate > 20 AND LAG(social_growth_rate, 1) OVER (ORDER BY event_date) > 20 
    THEN '1일 지연 효과'
    WHEN traffic_growth_rate > 20 AND LAG(social_growth_rate, 2) OVER (ORDER BY event_date) > 20 
    THEN '2일 지연 효과'
    ELSE '즉시 반응'
  END as response_timing
FROM correlation_analysis
WHERE traffic_growth_rate IS NOT NULL
ORDER BY event_date DESC;
```

**쿼리 결과 (2025-08-18 ~ 2025-08-25, Discord와 Steam 모두 동일 기간, app_id: 2456740):**

| event_date | total_visits | traffic_growth_rate | social_messages | social_reactions | social_authors | social_growth_rate |
|------------|--------------|---------------------|-----------------|------------------|----------------|-------------------|
| 2025-08-25 | 1121264 | -24.76 | 6578 | 571680 | 409 | 39.51 |
| 2025-08-24 | 1490230 | 0.90 | 4715 | 273452 | 421 | -5.42 |
| 2025-08-23 | 1476950 | 21.54 | 4985 | 316931 | 475 | -9.26 |
| 2025-08-22 | 1215192 | 7.62 | 5494 | 818574 | 533 | -16.16 |
| 2025-08-21 | 1129122 | -6.03 | 6553 | 483427 | 596 | -43.57 |
| 2025-08-20 | 1201594 | 252.52 | 11612 | 1537575 | 909 | 55.57 |
| 2025-08-19 | 340862 | 198.84 | 7464 | 812132 | 395 | -90.30 |

---

### 26. 위시리스트 변화와 디스코드/스팀 반응의 관계는 어떻게 되나요?

**필요한 테이블:**
- `main.log_steam.partner_wishlist`
- `main.log_discord.message`
- `main.log_steam.store_appreviews`
- `main.log_steam.steam_app_id`

**필요한 컬럼:**
- `partner_wishlist.adds`, `partner_wishlist.deletes`, `partner_wishlist.purchases_and_activations`, `partner_wishlist.date_local`
- `message.created_at`
- `store_appreviews.timestamp_created`

**조인 관계:**
```sql
partner_wishlist 
LEFT JOIN message ON message.game_code = 'inzoi' AND message.event_date = TO_DATE(partner_wishlist.date_local, 'yyyy-MM-dd')
LEFT JOIN store_appreviews ON CAST(partner_wishlist.app_id AS BIGINT) = store_appreviews.app_id
  AND store_appreviews.event_date = TO_DATE(partner_wishlist.date_local, 'yyyy-MM-dd')
```

**필터링 조건:**
- `partner_wishlist.app_id` = 2456740
- 위시리스트 변화 시점 식별
- 해당 시점 전후 소셜 반응 분석

**집계 방식:**
- 위시리스트 변화와 소셜 반응의 상관관계 분석
- 위시리스트 증가/감소 시점의 소셜 반응 집계

**예시 쿼리:**
```sql
WITH wishlist_data AS (
  SELECT 
    TRY_TO_DATE(pw.date_local, 'yyyy-MM-dd') as wishlist_date,
    pw.app_id,
    pw.adds as wishlist_adds,
    pw.deletes as wishlist_deletes,
    pw.purchases_and_activations as purchases,
    pw.adds - pw.deletes as net_wishlist_change,
    CASE 
      WHEN LAG(pw.adds - pw.deletes) OVER (PARTITION BY pw.app_id ORDER BY TRY_TO_DATE(pw.date_local, 'yyyy-MM-dd')) != 0
      THEN ROUND(((pw.adds - pw.deletes) - 
                  LAG(pw.adds - pw.deletes) OVER (PARTITION BY pw.app_id ORDER BY TRY_TO_DATE(pw.date_local, 'yyyy-MM-dd'))) * 100.0 
                 / ABS(LAG(pw.adds - pw.deletes) OVER (PARTITION BY pw.app_id ORDER BY TRY_TO_DATE(pw.date_local, 'yyyy-MM-dd'))), 2)
      ELSE NULL
    END as wishlist_change_rate
  FROM main.log_steam.partner_wishlist pw
  WHERE pw.app_id = '2456740'
    AND TRY_TO_DATE(pw.date_local, 'yyyy-MM-dd') IS NOT NULL
    AND TRY_TO_DATE(pw.date_local, 'yyyy-MM-dd') >= DATE '2025-08-18'
    AND TRY_TO_DATE(pw.date_local, 'yyyy-MM-dd') <= DATE '2025-08-25'
),
social_data AS (
  SELECT 
    m.event_date as reaction_date,
    COUNT(DISTINCT m.message_id) as message_count,
    COALESCE(SUM(r.count), 0) as reaction_count,
    COUNT(DISTINCT m.author_id) as unique_authors
  FROM main.log_discord.message m
  LEFT JOIN main.log_discord.reaction r ON m.message_id = r.message_id
  WHERE m.game_code = 'inzoi'
    AND m.event_date >= DATE '2025-08-18'
    AND m.event_date <= DATE '2025-08-25'
  GROUP BY m.event_date
  
  UNION ALL
  
  SELECT 
    sa.event_date as reaction_date,
    COUNT(DISTINCT sa.recommendationid) as message_count,
    SUM(sa.votes_up) as reaction_count,
    NULL as unique_authors
  FROM main.log_steam.store_appreviews sa
  WHERE sa.app_id = 2456740
    AND sa.event_date >= DATE '2025-08-18'
    AND sa.event_date <= DATE '2025-08-25'
  GROUP BY sa.event_date
),
social_summary AS (
  SELECT 
    reaction_date,
    SUM(message_count) as total_messages,
    SUM(reaction_count) as total_reactions,
    SUM(COALESCE(unique_authors, 0)) as total_authors
  FROM social_data
  GROUP BY reaction_date
),
correlation_analysis AS (
  SELECT 
    wd.wishlist_date,
    wd.wishlist_adds,
    wd.wishlist_deletes,
    wd.net_wishlist_change,
    wd.wishlist_change_rate,
    wd.purchases,
    COALESCE(ss.total_messages, 0) as social_messages,
    COALESCE(ss.total_reactions, 0) as social_reactions,
    COALESCE(ss.total_authors, 0) as social_authors,
    CASE 
      WHEN LAG(COALESCE(ss.total_messages, 0)) OVER (ORDER BY wd.wishlist_date) > 0
      THEN ROUND((COALESCE(ss.total_messages, 0) - 
                  LAG(COALESCE(ss.total_messages, 0)) OVER (ORDER BY wd.wishlist_date)) * 100.0 
                 / LAG(COALESCE(ss.total_messages, 0)) OVER (ORDER BY wd.wishlist_date), 2)
      ELSE NULL
    END as social_change_rate
  FROM wishlist_data wd
  LEFT JOIN social_summary ss ON wd.wishlist_date = ss.reaction_date
)
SELECT 
  wishlist_date,
  wishlist_adds,
  wishlist_deletes,
  net_wishlist_change,
  wishlist_change_rate,
  purchases,
  social_messages,
  social_reactions,
  social_authors,
  social_change_rate,
  CASE 
    WHEN wishlist_change_rate > 20 AND social_change_rate > 20 THEN '위시리스트 증가 → 소셜 반응 증가'
    WHEN wishlist_change_rate < -20 AND social_change_rate > 20 THEN '위시리스트 감소 → 소셜 반응 증가 (역상관)'
    WHEN wishlist_change_rate > 20 AND social_change_rate < -20 THEN '위시리스트 증가 → 소셜 반응 감소 (역상관)'
    ELSE '약한 상관관계'
  END as correlation_type
FROM correlation_analysis
WHERE wishlist_change_rate IS NOT NULL
ORDER BY wishlist_date DESC;
```

**쿼리 결과 (2025-08-18 ~ 2025-08-25, Discord와 Steam 모두 동일 기간, app_id: 2456740):**

| wishlist_date | wishlist_adds | wishlist_deletes | net_wishlist_change | wishlist_change_rate | purchases | social_messages | social_reactions | social_authors | social_change_rate |
|---------------|---------------|------------------|---------------------|----------------------|-----------|-----------------|------------------|----------------|-------------------|
| 2025-08-25 | 7933 | 3003 | 4930 | -36.45 | 2319 | 6578 | 571680 | 409 | 39.51 |
| 2025-08-24 | 11507 | 3749 | 7758 | 0.48 | 3289 | 4715 | 273452 | 421 | -5.42 |
| 2025-08-23 | 11289 | 3568 | 7721 | 6.95 | 3325 | 4985 | 316931 | 475 | -9.26 |
| 2025-08-22 | 10743 | 3524 | 7219 | 65.46 | 3330 | 5494 | 818574 | 533 | -16.16 |
| 2025-08-21 | 8230 | 3867 | 4363 | 816.42 | 3382 | 6553 | 483427 | 596 | -43.57 |
| 2025-08-20 | 6380 | 6989 | -609 | 13.25 | 4811 | 11612 | 1537575 | 909 | 55.57 |
| 2025-08-19 | 3068 | 3770 | -702 | -170.00 | 1154 | 7464 | 812132 | 395 | -90.30 |

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
- 게임 비교 쿼리(Q13)는 **inZOI, Dinkum** 두 게임을 비교합니다.
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

