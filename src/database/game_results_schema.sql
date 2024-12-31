-- Game Results table
CREATE TABLE
  IF NOT EXISTS nba_game_lines.game_results (
    id SERIAL PRIMARY KEY,
    game_id INTEGER NOT NULL REFERENCES nba_game_lines.games (id),
    home_team_score INTEGER,
    away_team_score INTEGER,
    home_team_won BOOLEAN GENERATED ALWAYS AS (
      CASE
        WHEN home_team_score > away_team_score THEN true
        WHEN home_team_score < away_team_score THEN false
        ELSE null
      END
    ) STORED,
    point_spread DECIMAL(4, 1) GENERATED ALWAYS AS (
      CASE
        WHEN home_team_score IS NOT NULL
        AND away_team_score IS NOT NULL THEN home_team_score - away_team_score
        ELSE null
      END
    ) STORED,
    total_points INTEGER GENERATED ALWAYS AS (
      CASE
        WHEN home_team_score IS NOT NULL
        AND away_team_score IS NOT NULL THEN home_team_score + away_team_score
        ELSE null
      END
    ) STORED,
    created_at TIMESTAMP
    WITH
      TIME ZONE DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP
    WITH
      TIME ZONE DEFAULT CURRENT_TIMESTAMP,
      CONSTRAINT unique_game_id UNIQUE (game_id)
  );

-- Create index for better query performance
CREATE INDEX IF NOT EXISTS idx_game_results_game_id ON nba_game_lines.game_results (game_id);

-- Create trigger for updating timestamps
CREATE TRIGGER update_game_results_updated_at BEFORE
UPDATE ON nba_game_lines.game_results FOR EACH ROW EXECUTE FUNCTION update_updated_at_column ();