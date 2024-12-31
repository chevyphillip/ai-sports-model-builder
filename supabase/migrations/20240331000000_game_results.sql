-- Create game_results table
CREATE TABLE
  IF NOT EXISTS nba_game_lines.game_results (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    away_team VARCHAR(255) NOT NULL,
    home_team VARCHAR(255) NOT NULL,
    away_score INTEGER NOT NULL,
    home_score INTEGER NOT NULL,
    attendance INTEGER,
    arena VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP
    WITH
      TIME ZONE DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP
    WITH
      TIME ZONE DEFAULT CURRENT_TIMESTAMP
  );

-- Create index on date for faster queries
CREATE INDEX IF NOT EXISTS game_results_date_idx ON nba_game_lines.game_results (date);

-- Create indexes on team names for faster lookups
CREATE INDEX IF NOT EXISTS game_results_away_team_idx ON nba_game_lines.game_results (away_team);

CREATE INDEX IF NOT EXISTS game_results_home_team_idx ON nba_game_lines.game_results (home_team);

-- Enable Row Level Security (RLS)
ALTER TABLE nba_game_lines.game_results ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all users to read game results
CREATE POLICY "Allow all users to read game results" ON nba_game_lines.game_results FOR
SELECT
  USING (true);

-- Create policy to allow authenticated users to insert game results
CREATE POLICY "Allow authenticated users to insert game results" ON nba_game_lines.game_results FOR INSERT
WITH
  CHECK (auth.role () = 'authenticated');

-- Create policy to allow authenticated users to update game results
CREATE POLICY "Allow authenticated users to update game results" ON nba_game_lines.game_results FOR
UPDATE USING (auth.role () = 'authenticated')
WITH
  CHECK (auth.role () = 'authenticated');

-- Create policy to allow authenticated users to delete game results
CREATE POLICY "Allow authenticated users to delete game results" ON nba_game_lines.game_results FOR DELETE USING (auth.role () = 'authenticated');

-- Grant access to authenticated users
GRANT
SELECT
  ON nba_game_lines.game_results TO authenticated;

GRANT INSERT ON nba_game_lines.game_results TO authenticated;

GRANT
UPDATE ON nba_game_lines.game_results TO authenticated;

GRANT DELETE ON nba_game_lines.game_results TO authenticated;

-- Grant access to anon users (read-only)
GRANT
SELECT
  ON nba_game_lines.game_results TO anon;