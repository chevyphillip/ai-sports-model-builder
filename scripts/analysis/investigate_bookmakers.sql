-- Analyze odds data by bookmaker
WITH
  bookmaker_summary AS (
    SELECT
      b.name as bookmaker,
      COUNT(DISTINCT g.id) as total_games,
      COUNT(
        DISTINCT CASE
          WHEN go.home_price IS NOT NULL
          AND go.away_price IS NOT NULL THEN g.id
        END
      ) as games_with_moneyline,
      COUNT(
        DISTINCT CASE
          WHEN go.spread IS NOT NULL THEN g.id
        END
      ) as games_with_spread,
      COUNT(
        DISTINCT CASE
          WHEN go.total IS NOT NULL THEN g.id
        END
      ) as games_with_total,
      MIN(g.commence_time) as first_game,
      MAX(g.commence_time) as last_game,
      COUNT(DISTINCT go.id) as total_odds_records
    FROM
      nba_game_lines.games g
      LEFT JOIN nba_game_lines.game_odds go ON g.id = go.game_id
      LEFT JOIN nba_game_lines.bookmakers b ON go.bookmaker_id = b.id
    WHERE
      g.commence_time >= '2020-01-01'
    GROUP BY
      b.name
  )
SELECT
  bookmaker,
  total_games,
  games_with_moneyline,
  games_with_spread,
  games_with_total,
  first_game,
  last_game,
  total_odds_records,
  ROUND(100.0 * games_with_moneyline / total_games, 2) as moneyline_coverage_pct,
  ROUND(100.0 * games_with_spread / total_games, 2) as spread_coverage_pct,
  ROUND(100.0 * games_with_total / total_games, 2) as total_coverage_pct,
  ROUND(
    1.0 * total_odds_records / NULLIF(total_games, 0),
    2
  ) as avg_updates_per_game
FROM
  bookmaker_summary
WHERE
  total_games > 0
ORDER BY
  total_games DESC;