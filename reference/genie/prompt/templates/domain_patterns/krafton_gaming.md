# KRAFTON Gaming Domain Patterns

This document contains domain-specific SQL patterns and best practices for KRAFTON gaming analytics, including social platform aggregation, regional analysis, and game-specific filtering.

## Cross-platform Aggregation (CRITICAL for Social Analytics)

When users ask about "all social platforms", "전체 소셜 플랫폼", or want to compare across multiple data sources (Discord, Steam reviews, Steam community, etc.), you MUST use UNION ALL to combine data from all relevant sources. Do not rely on a single table or source.

**Pattern for cross-platform queries**:
```sql
WITH discord AS (
  SELECT 'discord' AS platform,
         CAST(message_id AS STRING) AS content_id,
         message AS content,
         event_date,
         COALESCE(SUM(reaction.count), 0) AS engagement
  FROM message
  LEFT JOIN reaction ON message.message_id = reaction.message_id
  WHERE game_code = 'inzoi' -- Always filter by game/app unless asked for "all games"
    AND event_date BETWEEN '2025-08-18' AND '2025-08-25'
  GROUP BY 1, 2, 3, 4
),
steam_reviews AS (
  SELECT 'steam_review' AS platform,
         CAST(recommendationid AS STRING) AS content_id,
         review AS content,
         event_date,
         votes_up AS engagement
  FROM store_appreviews
  WHERE app_id = 2456740 -- Always filter by app_id unless asked for "all games"
    AND event_date BETWEEN '2025-08-18' AND '2025-08-25'
),
steam_community AS (
  SELECT 'steam_community' AS platform,
         topic_url AS content_id,
         title AS content,
         t.event_date,
         COUNT(DISTINCT c.comment_id) AS engagement
  FROM community_discussions_topics t
  LEFT JOIN community_discussions_comments c ON t.topic_url = c.topic_url
  WHERE t.app_id = 2456740
    AND t.event_date BETWEEN '2025-08-18' AND '2025-08-25'
  GROUP BY 1, 2, 3, 4
)
SELECT * FROM discord
UNION ALL SELECT * FROM steam_reviews
UNION ALL SELECT * FROM steam_community
ORDER BY engagement DESC
LIMIT 20;
```

**Key principles**:
- Each CTE represents one platform/source with a unified schema (platform, content_id, content, event_date, engagement)
- ALWAYS use UNION ALL (not UNION) to preserve all records
- Normalize engagement metrics across sources (reactions, votes_up, comment counts)
- Filter each source by its appropriate game identifier (game_code for Discord, app_id for Steam)
- Group by platform for summary statistics when needed

## Regional Analysis Patterns

When analyzing regional or country-level data, use the `partner_regions_and_countries` table with proper date parsing and period comparison:

```sql
SELECT
  region,
  country,
  'before_event' AS period,
  AVG(wishlists_daily) AS avg_daily_wishlists,
  AVG(purchases_daily) AS avg_daily_purchases
FROM partner_regions_and_countries
WHERE app_id = 2456740
  AND TRY_TO_DATE(date, 'yyyy-MM-dd') BETWEEN '2025-08-11' AND '2025-08-17'
GROUP BY region, country
UNION ALL
SELECT
  region,
  country,
  'after_event' AS period,
  AVG(wishlists_daily) AS avg_daily_wishlists,
  AVG(purchases_daily) AS avg_daily_purchases
FROM partner_regions_and_countries
WHERE app_id = 2456740
  AND TRY_TO_DATE(date, 'yyyy-MM-dd') BETWEEN '2025-08-18' AND '2025-08-25'
GROUP BY region, country
ORDER BY region, country, period;
```

## Required Game/App Filters (DEFAULT BEHAVIOR)

**ALWAYS apply game/app filters** unless the user explicitly asks for "all games" or multiple games:

- **Discord data**: Filter by `game_code` (e.g., `game_code = 'inzoi'`)
- **Steam data**: Filter by `app_id` (e.g., `app_id = 2456740`)

If the user doesn't specify which game, use the default filters shown above or ask a clarification question.

## Time Range Handling (Korean Language Support)

Users specify time ranges in various ways:

**Relative time ranges**:
- "최근 24시간" (last 24 hours): `event_date >= DATE_SUB(CURRENT_DATE(), 1)`
- "지난 주" (last week): `event_date >= DATE_SUB(CURRENT_DATE(), 7)`
- "최근 한 달" (last month): `event_date >= DATE_SUB(CURRENT_DATE(), 30)`

**Absolute time ranges**:
- "2025년 8월 18일부터 25일까지": `event_date BETWEEN '2025-08-18' AND '2025-08-25'`

**Hour-level analysis**:
- Use `event_hour` column when available for granular time-of-day analysis
- Example: `WHERE event_date = '2025-08-20' AND event_hour BETWEEN 14 AND 16`

**Default behavior**: If no time range specified, default to last 7 days.

## Contextual Joins for Richer Analysis

**Discord channel context**:
Join `message` with `channel_list` to provide channel names for context:
```sql
FROM message m
LEFT JOIN channel_list cl ON m.channel_id = cl.channel_id
WHERE m.game_code = 'inzoi'
```

**Steam community engagement**:
Join `community_discussions_topics` with `community_discussions_comments` to analyze discussion engagement:
```sql
FROM community_discussions_topics t
LEFT JOIN community_discussions_comments c ON t.topic_url = c.topic_url
WHERE t.app_id = 2456740
GROUP BY t.topic_url, t.title
```

## Keyword Extraction and Analysis

For keyword/mention analysis, use word splitting with filtering:
```sql
WITH all_content AS (
  SELECT message AS text, event_date, 'discord' AS platform
  FROM message
  WHERE game_code = 'inzoi' AND event_date >= DATE_SUB(CURRENT_DATE(), 1)
  UNION ALL
  SELECT review AS text, event_date, 'steam_review' AS platform
  FROM store_appreviews
  WHERE app_id = 2456740 AND event_date >= DATE_SUB(CURRENT_DATE(), 1)
),
words AS (
  SELECT platform, LOWER(TRIM(word)) AS keyword
  FROM all_content
  LATERAL VIEW EXPLODE(SPLIT(text, ' ')) word_table AS word
  WHERE LENGTH(TRIM(word)) > 2  -- Filter out short words
)
SELECT keyword, platform, COUNT(*) AS mention_count
FROM words
GROUP BY keyword, platform
ORDER BY mention_count DESC
LIMIT 20;
```
