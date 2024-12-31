-- Analyze missing odds data patterns
WITH
  game_odds_summary AS (
    SELECT
      g.id as game_id,
      g.commence_time,
      COUNT(DISTINCT go.id) as total_odds_records,
      COUNT(
        DISTINCT CASE
          WHEN go.home_price IS NOT NULL
          AND go.away_price IS NOT NULL THEN go.id
        END
      ) as moneyline_records,
      COUNT(
        DISTINCT CASE
          WHEN go.spread IS NOT NULL THEN go.id
        END
      ) as spread_records,
      COUNT(
        DISTINCT CASE
          WHEN go.total IS NOT NULL THEN go.id
        END
      ) as total_records,
      MAX(go.timestamp) as last_update,
      EXTRACT(
        HOUR
        FROM
          g.commence_time
      ) as game_hour,
      EXTRACT(
        DOW
        FROM
          g.commence_time
      ) as game_dow,
      ht.name as home_team,
      at.name as away_team
    FROM
      nba_game_lines.games g
      LEFT JOIN nba_game_lines.game_odds go ON g.id = go.game_id
      LEFT JOIN nba_game_lines.nba_teams ht ON g.home_team_id = ht.id
      LEFT JOIN nba_game_lines.nba_teams at ON g.away_team_id = at.id
    WHERE
      g.commence_time >= '2020-01-01'
    GROUP BY
      g.id,
      g.commence_time,
      ht.name,
      at.name
  )
SELECT
  -- Overall summary
  COUNT(*) as total_games,
  COUNT(
    CASE
      WHEN moneyline_records > 0 THEN 1
    END
  ) as games_with_moneyline,
  COUNT(
    CASE
      WHEN spread_records > 0 THEN 1
    END
  ) as games_with_spread,
  COUNT(
    CASE
      WHEN total_records > 0 THEN 1
    END
  ) as games_with_total,
  -- Average records per game
  AVG(total_odds_records) as avg_odds_records_per_game,
  -- Missing data by time of day
  json_agg (
    json_build_object (
      'hour',
      game_hour,
      'total_games',
      COUNT(*),
      'missing_moneyline',
      COUNT(
        CASE
          WHEN moneyline_records = 0 THEN 1
        END
      ),
      'missing_spread',
      COUNT(
        CASE
          WHEN spread_records = 0 THEN 1
        END
      ),
      'missing_total',
      COUNT(
        CASE
          WHEN total_records = 0 THEN 1
        END
      )
    )
    ORDER BY
      game_hour
  ) as missing_by_hour,
  -- Missing data by day of week
  json_agg (
    json_build_object (
      'dow',
      game_dow,
      'total_games',
      COUNT(*),
      'missing_moneyline',
      COUNT(
        CASE
          WHEN moneyline_records = 0 THEN 1
        END
      ),
      'missing_spread',
      COUNT(
        CASE
          WHEN spread_records = 0 THEN 1
        END
      ),
      'missing_total',
      COUNT(
        CASE
          WHEN total_records = 0 THEN 1
        END
      )
    )
    ORDER BY
      game_dow
  ) as missing_by_dow,
  -- Time between last update and game start
  AVG(
    EXTRACT(
      EPOCH
      FROM
        (commence_time - last_update)
    ) / 3600
  ) as avg_hours_before_game,
  MIN(
    EXTRACT(
      EPOCH
      FROM
        (commence_time - last_update)
    ) / 3600
  ) as min_hours_before_game,
  MAX(
    EXTRACT(
      EPOCH
      FROM
        (commence_time - last_update)
    ) / 3600
  ) as max_hours_before_game
FROM
  game_odds_summary
GROUP BY
  1;