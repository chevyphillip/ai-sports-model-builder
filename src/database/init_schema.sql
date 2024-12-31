-- Teams table
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    abbreviation VARCHAR(3) NOT NULL UNIQUE,
    conference VARCHAR(20),
    division VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Games table
CREATE TABLE IF NOT EXISTS games (
    id SERIAL PRIMARY KEY,
    game_date DATE NOT NULL,
    home_team_id INTEGER REFERENCES teams(id),
    away_team_id INTEGER REFERENCES teams(id),
    home_team_score INTEGER,
    away_team_score INTEGER,
    season INTEGER NOT NULL,
    season_type VARCHAR(20) NOT NULL, -- 'Regular Season' or 'Playoffs'
    status VARCHAR(20) NOT NULL, -- 'Scheduled', 'In Progress', 'Final'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Team Game Stats table
CREATE TABLE IF NOT EXISTS team_game_stats (
    id SERIAL PRIMARY KEY,
    game_id INTEGER REFERENCES games(id),
    team_id INTEGER REFERENCES teams(id),
    is_home BOOLEAN NOT NULL,
    field_goals_made INTEGER,
    field_goals_attempted INTEGER,
    three_points_made INTEGER,
    three_points_attempted INTEGER,
    free_throws_made INTEGER,
    free_throws_attempted INTEGER,
    rebounds_offensive INTEGER,
    rebounds_defensive INTEGER,
    assists INTEGER,
    steals INTEGER,
    blocks INTEGER,
    turnovers INTEGER,
    personal_fouls INTEGER,
    points INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Betting Odds table
CREATE TABLE IF NOT EXISTS betting_odds (
    id SERIAL PRIMARY KEY,
    game_id INTEGER REFERENCES games(id),
    bookmaker VARCHAR(100) NOT NULL,
    market_type VARCHAR(50) NOT NULL, -- 'spread', 'moneyline', 'totals'
    price DECIMAL(10,2) NOT NULL,
    points DECIMAL(4,1), -- spread points or total points (null for moneyline)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Model Predictions table
CREATE TABLE IF NOT EXISTS model_predictions (
    id SERIAL PRIMARY KEY,
    game_id INTEGER REFERENCES games(id),
    model_version VARCHAR(50) NOT NULL,
    predicted_home_score DECIMAL(5,2),
    predicted_away_score DECIMAL(5,2),
    predicted_spread DECIMAL(4,1),
    predicted_total DECIMAL(5,2),
    confidence_score DECIMAL(4,3),
    features_used JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_games_date ON games(game_date);
CREATE INDEX IF NOT EXISTS idx_games_teams ON games(home_team_id, away_team_id);
CREATE INDEX IF NOT EXISTS idx_team_game_stats_game ON team_game_stats(game_id);
CREATE INDEX IF NOT EXISTS idx_betting_odds_game ON betting_odds(game_id);
CREATE INDEX IF NOT EXISTS idx_model_predictions_game ON model_predictions(game_id);

-- Create trigger function for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for all tables
CREATE TRIGGER update_teams_updated_at
    BEFORE UPDATE ON teams
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_games_updated_at
    BEFORE UPDATE ON games
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_team_game_stats_updated_at
    BEFORE UPDATE ON team_game_stats
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_betting_odds_updated_at
    BEFORE UPDATE ON betting_odds
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_model_predictions_updated_at
    BEFORE UPDATE ON model_predictions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column(); 