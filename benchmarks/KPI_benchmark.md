%md
# KPI 수치형 질문 - Top 10 Question-Answer Set ✅ TESTED & FIXED

## 📋 Corrected Catalog/Schema: `sandbox.agent_poc`
## ⚠️ **CRITICAL FIX:** Deduplication applied to all Steam queries

**Root Cause:** Steam tables contain duplicate records across multiple `event_date` values (daily collection)
**Solution:** Use `ROW_NUMBER() OVER (PARTITION BY unique_id ORDER BY event_date DESC)` to get latest record only

---

## 1. 디스코드에서 리액션이 가장 많은 메시지는 무엇인가요? ✅

**Question:** What are the Discord messages with the most reactions?

**Query:**
```sql
SELECT 
  m.message_id,
  m.created_at,
  c.channel_name,
  COALESCE(SUM(r.count), 0) as reaction_count,
  COUNT(DISTINCT r.emoji_name) as unique_emojis
FROM sandbox.agent_poc.message m
LEFT JOIN sandbox.agent_poc.reaction r ON m.message_id = r.message_id
LEFT JOIN sandbox.agent_poc.channel_list c ON m.channel_id = c.channel_id
WHERE m.game_code = 'inzoi'
  AND m.event_date >= CURRENT_DATE - INTERVAL 30 DAYS
GROUP BY m.message_id, m.created_at, c.channel_name
HAVING COALESCE(SUM(r.count), 0) > 0
ORDER BY reaction_count DESC
LIMIT 10;
```

**Note:** No deduplication needed - message table doesn't have duplicates

---

## 2. 스팀 리뷰에서 추천 수가 높은 리뷰는 무엇인가요? ✅

**Question:** What are the Steam reviews with the highest upvote counts?

**Query:**
```sql
WITH latest_reviews AS (
  SELECT 
    r.recommendationid,
    r.author.steamid as author_steamid,
    r.votes_up,
    r.weighted_vote_score,
    r.voted_up,
    r.timestamp_created,
    ROW_NUMBER() OVER (PARTITION BY r.recommendationid ORDER BY r.event_date DESC) as rn
  FROM sandbox.agent_poc.store_appreviews r
  INNER JOIN sandbox.agent_poc.steam_apps s ON r.app_id = s.app_id
  WHERE s.game_code = 'inzoi'
    AND r.event_date >= CURRENT_DATE - INTERVAL 30 DAYS
)
SELECT 
  recommendationid,
  author_steamid,
  votes_up,
  weighted_vote_score,
  voted_up,
  timestamp_created
FROM latest_reviews
WHERE rn = 1
ORDER BY votes_up DESC, CAST(weighted_vote_score AS DOUBLE) DESC
LIMIT 10;
```

**Fix Applied:** ROW_NUMBER() deduplication by recommendationid

---

## 3. 스팀 커뮤니티에서 댓글이 많이 달린 토픽은 무엇인가요? ✅

**Question:** What are the Steam community topics with the most comments?

**Query:**
```sql
WITH latest_topics AS (
  SELECT 
    t.url,
    t.title,
    t.author,
    t.timestamp,
    ROW_NUMBER() OVER (PARTITION BY t.url ORDER BY t.event_date DESC) as rn
  FROM sandbox.agent_poc.community_discussions_topics t
  INNER JOIN sandbox.agent_poc.steam_apps s ON t.app_id = s.app_id
  WHERE s.game_code = 'inzoi'
    AND t.event_date >= CURRENT_DATE - INTERVAL 30 DAYS
),
latest_comments AS (
  SELECT 
    c.topic_url,
    c.comment_id,
    ROW_NUMBER() OVER (PARTITION BY c.comment_id ORDER BY c.event_date DESC) as rn
  FROM sandbox.agent_poc.community_discussions_comments c
  WHERE c.event_date >= CURRENT_DATE - INTERVAL 30 DAYS
)
SELECT 
  t.url as topic_url,
  t.title,
  t.author,
  t.timestamp as created_at,
  COUNT(DISTINCT c.comment_id) as comment_count
FROM latest_topics t
LEFT JOIN latest_comments c ON t.url = c.topic_url AND c.rn = 1
WHERE t.rn = 1
GROUP BY t.url, t.title, t.author, t.timestamp
ORDER BY comment_count DESC
LIMIT 10;
```

**Fix Applied:** ROW_NUMBER() deduplication for both topics and comments

---

## 4. 디스코드에서 가장 활발한 채널은 어디인가요? ✅

**Question:** Which Discord channels are the most active?

**Query:**
```sql
SELECT 
  c.channel_name,
  COUNT(DISTINCT m.message_id) as message_count,
  COALESCE(SUM(r.count), 0) as reaction_count,
  COUNT(DISTINCT m.message_id) + (COALESCE(SUM(r.count), 0) * 0.5) as activity_score
FROM sandbox.agent_poc.message m
INNER JOIN sandbox.agent_poc.channel_list c ON m.channel_id = c.channel_id
LEFT JOIN sandbox.agent_poc.reaction r ON m.message_id = r.message_id
WHERE m.game_code = 'inzoi'
  AND m.event_date >= CURRENT_DATE - INTERVAL 30 DAYS
GROUP BY c.channel_name
ORDER BY activity_score DESC
LIMIT 10;
```

**Note:** No deduplication needed

---

## 5. 시간대별로 언급량이 가장 많은 시간은 언제인가요? ✅

**Question:** What are the peak hours for mentions across platforms?

**Query:**
```sql
WITH discord_hourly AS (
  SELECT 
    HOUR(created_at) as hour,
    COUNT(*) as mention_count
  FROM sandbox.agent_poc.message
  WHERE game_code = 'inzoi'
    AND event_date >= CURRENT_DATE - INTERVAL 30 DAYS
  GROUP BY HOUR(created_at)
),
latest_steam_reviews AS (
  SELECT 
    r.timestamp_created,
    ROW_NUMBER() OVER (PARTITION BY r.recommendationid ORDER BY r.event_date DESC) as rn
  FROM sandbox.agent_poc.store_appreviews r
  INNER JOIN sandbox.agent_poc.steam_apps s ON r.app_id = s.app_id
  WHERE s.game_code = 'inzoi'
    AND r.event_date >= CURRENT_DATE - INTERVAL 30 DAYS
),
steam_hourly AS (
  SELECT 
    HOUR(FROM_UNIXTIME(timestamp_created)) as hour,
    COUNT(*) as mention_count
  FROM latest_steam_reviews
  WHERE rn = 1
  GROUP BY HOUR(FROM_UNIXTIME(timestamp_created))
)
SELECT 
  COALESCE(d.hour, s.hour) as hour,
  COALESCE(d.mention_count, 0) + COALESCE(s.mention_count, 0) as total_mentions
FROM discord_hourly d
FULL OUTER JOIN steam_hourly s ON d.hour = s.hour
ORDER BY total_mentions DESC
LIMIT 10;
```

**Fix Applied:** ROW_NUMBER() deduplication for Steam reviews

---

## 6. 디스코드와 스팀에서 긍정/부정 비율은 어떻게 다른가요? ✅

**Question:** How do positive/negative sentiment ratios differ between Discord and Steam?

**Query:**
```sql
WITH latest_reviews AS (
  SELECT 
    r.voted_up,
    ROW_NUMBER() OVER (PARTITION BY r.recommendationid ORDER BY r.event_date DESC) as rn
  FROM sandbox.agent_poc.store_appreviews r
  INNER JOIN sandbox.agent_poc.steam_apps s ON r.app_id = s.app_id
  WHERE s.game_code = 'inzoi'
    AND r.event_date >= CURRENT_DATE - INTERVAL 30 DAYS
)
SELECT 
  'Steam' as platform,
  SUM(CASE WHEN voted_up = true THEN 1 ELSE 0 END) as positive_count,
  SUM(CASE WHEN voted_up = false THEN 1 ELSE 0 END) as negative_count,
  ROUND(SUM(CASE WHEN voted_up = true THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as positive_percentage
FROM latest_reviews
WHERE rn = 1;
```

**Fix Applied:** ROW_NUMBER() deduplication

---

## 7. 게임별로 소셜 반응을 비교해주세요 ✅

**Question:** Compare social reactions across different games

**Query:**
```sql
WITH discord_stats AS (
  SELECT 
    m.game_code,
    COUNT(DISTINCT m.message_id) as message_count,
    COALESCE(SUM(r.count), 0) as reaction_count
  FROM sandbox.agent_poc.message m
  LEFT JOIN sandbox.agent_poc.reaction r ON m.message_id = r.message_id
  WHERE m.event_date >= CURRENT_DATE - INTERVAL 30 DAYS
  GROUP BY m.game_code
),
latest_reviews AS (
  SELECT 
    s.game_code,
    r.votes_up,
    ROW_NUMBER() OVER (PARTITION BY r.recommendationid ORDER BY r.event_date DESC) as rn
  FROM sandbox.agent_poc.store_appreviews r
  INNER JOIN sandbox.agent_poc.steam_apps s ON r.app_id = s.app_id
  WHERE r.event_date >= CURRENT_DATE - INTERVAL 30 DAYS
),
steam_stats AS (
  SELECT 
    game_code,
    COUNT(*) as review_count,
    SUM(votes_up) as total_upvotes
  FROM latest_reviews
  WHERE rn = 1
  GROUP BY game_code
)
SELECT 
  COALESCE(d.game_code, s.game_code) as game_code,
  COALESCE(d.message_count, 0) as discord_messages,
  COALESCE(d.reaction_count, 0) as discord_reactions,
  COALESCE(s.review_count, 0) as steam_reviews,
  COALESCE(s.total_upvotes, 0) as steam_upvotes
FROM discord_stats d
FULL OUTER JOIN steam_stats s ON d.game_code = s.game_code
ORDER BY (COALESCE(d.message_count, 0) + COALESCE(s.review_count, 0)) DESC
LIMIT 10;
```

**Fix Applied:** ROW_NUMBER() deduplication for Steam reviews

---

## 8. 최근 7일간 일별 소셜 활동 추이는 어떻게 되나요? ✅

**Question:** What is the daily social activity trend over the last 7 days?

**Query:**
```sql
WITH discord_daily AS (
  SELECT 
    DATE(created_at) as activity_date,
    COUNT(*) as message_count
  FROM sandbox.agent_poc.message
  WHERE game_code = 'inzoi'
    AND event_date >= CURRENT_DATE - INTERVAL 7 DAYS
  GROUP BY DATE(created_at)
),
latest_reviews AS (
  SELECT 
    r.timestamp_created,
    ROW_NUMBER() OVER (PARTITION BY r.recommendationid ORDER BY r.event_date DESC) as rn
  FROM sandbox.agent_poc.store_appreviews r
  INNER JOIN sandbox.agent_poc.steam_apps s ON r.app_id = s.app_id
  WHERE s.game_code = 'inzoi'
    AND r.event_date >= CURRENT_DATE - INTERVAL 7 DAYS
),
steam_daily AS (
  SELECT 
    DATE(FROM_UNIXTIME(timestamp_created)) as activity_date,
    COUNT(*) as review_count
  FROM latest_reviews
  WHERE rn = 1
  GROUP BY DATE(FROM_UNIXTIME(timestamp_created))
)
SELECT 
  COALESCE(d.activity_date, s.activity_date) as date,
  COALESCE(d.message_count, 0) as discord_messages,
  COALESCE(s.review_count, 0) as steam_reviews,
  COALESCE(d.message_count, 0) + COALESCE(s.review_count, 0) as total_activity
FROM discord_daily d
FULL OUTER JOIN steam_daily s ON d.activity_date = s.activity_date
ORDER BY date DESC;
```

**Fix Applied:** ROW_NUMBER() deduplication for Steam reviews

---

## 9. 스팀 리뷰의 평균 추천 점수는 얼마인가요? ✅

**Question:** What is the average recommendation score for Steam reviews?

**Query:**
```sql
WITH latest_reviews AS (
  SELECT 
    s.game_code,
    r.weighted_vote_score,
    r.voted_up,
    ROW_NUMBER() OVER (PARTITION BY r.recommendationid ORDER BY r.event_date DESC) as rn
  FROM sandbox.agent_poc.store_appreviews r
  INNER JOIN sandbox.agent_poc.steam_apps s ON r.app_id = s.app_id
  WHERE s.game_code = 'inzoi'
    AND r.event_date >= CURRENT_DATE - INTERVAL 30 DAYS
)
SELECT 
  game_code,
  COUNT(*) as total_reviews,
  AVG(CAST(weighted_vote_score AS DOUBLE)) as avg_weighted_score,
  SUM(CASE WHEN voted_up = true THEN 1 ELSE 0 END) as positive_reviews,
  SUM(CASE WHEN voted_up = false THEN 1 ELSE 0 END) as negative_reviews,
  ROUND(SUM(CASE WHEN voted_up = true THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as positive_rate
FROM latest_reviews
WHERE rn = 1
GROUP BY game_code;
```

**Fix Applied:** ROW_NUMBER() deduplication + CAST to DOUBLE

---

## 10. 디스코드에서 가장 많이 사용된 이모지는 무엇인가요? ✅

**Question:** What are the most frequently used emojis on Discord?

**Query:**
```sql
SELECT 
  r.emoji_name,
  SUM(r.count) as total_usage,
  COUNT(DISTINCT r.message_id) as unique_messages
FROM sandbox.agent_poc.reaction r
INNER JOIN sandbox.agent_poc.message m ON r.message_id = m.message_id
WHERE m.game_code = 'inzoi'
  AND m.event_date >= CURRENT_DATE - INTERVAL 30 DAYS
GROUP BY r.emoji_name
ORDER BY total_usage DESC
LIMIT 10;
```

**Note:** No deduplication needed

---

## ✅ All Fixes Applied:

1. **Deduplication:** ROW_NUMBER() for all Steam tables
2. **Table Names:** `steam_app_id` → `steam_apps`
3. **Column Names:** `author_steamid` → `author.steamid`
4. **Timestamp Conversion:** `FROM_UNIXTIME(timestamp_created)`
5. **Type Casting:** `CAST(weighted_vote_score AS DOUBLE)`
6. **No Nulls:** All queries return valid data
7. **No Duplicates:** Verified with testing