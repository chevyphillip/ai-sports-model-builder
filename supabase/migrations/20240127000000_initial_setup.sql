-- Create schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS nba_game_lines;
-- Create tables
CREATE TABLE
  IF NOT EXISTS nba_game_lines.function_monitoring (
    id BIGSERIAL PRIMARY KEY,
    function_name TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN ('start', 'success', 'error')),
    duration_ms INTEGER,
    error_message TEXT,
    metadata JSONB,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW (),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW ()
  );
CREATE TABLE
  IF NOT EXISTS nba_game_lines.games (
    id BIGSERIAL PRIMARY KEY,
    game_id TEXT NOT NULL,
    sport_key TEXT NOT NULL,
    sport_title TEXT NOT NULL,
    commence_time TIMESTAMPTZ NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW (),
    UNIQUE (game_id, timestamp)
  );
CREATE TABLE
  IF NOT EXISTS nba_game_lines.game_odds (
    id BIGSERIAL PRIMARY KEY,
    game_id TEXT NOT NULL,
    bookmaker_key TEXT NOT NULL,
    bookmaker_title TEXT NOT NULL,
    market_key TEXT NOT NULL,
    market_last_update TIMESTAMPTZ NOT NULL,
    outcomes JSONB NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW (),
    FOREIGN KEY (game_id, timestamp) REFERENCES nba_game_lines.games (game_id, timestamp),
    UNIQUE (game_id, bookmaker_key, market_key, timestamp)
  );
-- Create indexes
CREATE INDEX IF NOT EXISTS idx_function_monitoring_timestamp ON nba_game_lines.function_monitoring (timestamp);
CREATE INDEX IF NOT EXISTS idx_function_monitoring_name_type ON nba_game_lines.function_monitoring (function_name, event_type);
CREATE INDEX IF NOT EXISTS idx_games_timestamp ON nba_game_lines.games (timestamp);
CREATE INDEX IF NOT EXISTS idx_games_commence_time ON nba_game_lines.games (commence_time);
CREATE INDEX IF NOT EXISTS idx_game_odds_timestamp ON nba_game_lines.game_odds (timestamp);
CREATE INDEX IF NOT EXISTS idx_game_odds_market ON nba_game_lines.game_odds (bookmaker_key, market_key);
-- Enable RLS on all tables
ALTER TABLE nba_game_lines.function_monitoring ENABLE ROW LEVEL SECURITY;
ALTER TABLE nba_game_lines.games ENABLE ROW LEVEL SECURITY;
ALTER TABLE nba_game_lines.game_odds ENABLE ROW LEVEL SECURITY;
-- Create policies for function_monitoring
CREATE POLICY "Allow authenticated read access to function_monitoring" ON nba_game_lines.function_monitoring FOR
SELECT
  TO authenticated USING (true);
CREATE POLICY "Allow service role write access to function_monitoring" ON nba_game_lines.function_monitoring FOR INSERT TO service_role
WITH
  CHECK (true);
-- Create policies for games
CREATE POLICY "Allow authenticated read access to games" ON nba_game_lines.games FOR
SELECT
  TO authenticated USING (true);
CREATE POLICY "Allow service role write access to games" ON nba_game_lines.games FOR INSERT TO service_role
WITH
  CHECK (true);
-- Create policies for game_odds
CREATE POLICY "Allow authenticated read access to game_odds" ON nba_game_lines.game_odds FOR
SELECT
  TO authenticated USING (true);
CREATE POLICY "Allow service role write access to game_odds" ON nba_game_lines.game_odds FOR INSERT TO service_role
WITH
  CHECK (true);
-- Grant necessary permissions
GRANT USAGE ON SCHEMA nba_game_lines TO authenticated;
GRANT USAGE ON SCHEMA nba_game_lines TO service_role;
GRANT
SELECT
  ON nba_game_lines.function_monitoring TO authenticated;
GRANT INSERT ON nba_game_lines.function_monitoring TO service_role;
GRANT
SELECT
  ON nba_game_lines.games TO authenticated;
GRANT INSERT ON nba_game_lines.games TO service_role;
GRANT
SELECT
  ON nba_game_lines.game_odds TO authenticated;
GRANT INSERT ON nba_game_lines.game_odds TO service_role;
