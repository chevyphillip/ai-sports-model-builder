-- Create a view for cleaned game odds data
CREATE
OR REPLACE VIEW nba_game_lines.clean_game_odds AS
WITH
  latest_odds AS (
    -- Get the latest odds for each game
    SELECT DISTINCT
      ON (game_id) game_id,
      home_price,
      away_price,
      spread,
      total,
      over_price,
      under_price,
      timestamp,
      -- Add data quality flags
      CASE
        WHEN home_price IS NOT NULL
        AND away_price IS NOT NULL THEN true
        ELSE false
      END as has_moneyline,
      CASE
        WHEN spread IS NOT NULL THEN true
        ELSE false
      END as has_spread,
      CASE
        WHEN total IS NOT NULL
        AND over_price IS NOT NULL
        AND under_price IS NOT NULL THEN true
        ELSE false
      END as has_totals
    FROM
      nba_game_lines.game_odds
    ORDER BY
      game_id,
      timestamp DESC
  )
SELECT
  g.id,
  g.home_team_id,
  g.away_team_id,
  g.commence_time,
  ht.name as home_team,
  at.name as away_team,
  go.home_price,
  go.away_price,
  go.spread,
  go.total,
  go.over_price,
  go.under_price,
  go.has_moneyline,
  go.has_spread,
  go.has_totals,
  go.timestamp as odds_timestamp
FROM
  nba_game_lines.games g
  JOIN nba_game_lines.nba_teams ht ON g.home_team_id = ht.id
  JOIN nba_game_lines.nba_teams at ON g.away_team_id = at.id
  LEFT JOIN latest_odds go ON g.id = go.game_id
  -- Only include games that have at least one type of odds
WHERE
  go.has_moneyline = true
  OR go.has_spread = true
  OR go.has_totals = true;