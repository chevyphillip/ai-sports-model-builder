import pytest
from src.data_collection.data_transformer import NBAGameDataTransformer


def test_data_transformation():
    """Test the data transformation pipeline with sample data"""

    # Sample data including different scenarios
    sample_data = [
        {
            # Regular game
            "Date": "[Sun, Dec 25, 2011](/boxscores/index.fcgi?month=12&day=25&year=2011)",
            "Start (ET)": "12:00p",
            "Visitor/Neutral": "[Boston Celtics](/teams/BOS/2012.html)",
            "PTS": 104,
            "Home/Neutral": "[New York Knicks](/teams/NYK/2012.html)",
            "PTS.1": 106,
            "": "",
            "Attend.": "19,763",
            "LOG": "2:47",
            "Arena": "Madison Square Garden (IV)",
            "Notes": "",
        },
        {
            # Overtime game
            "Date": "[Mon, Dec 26, 2011](/boxscores/index.fcgi?month=12&day=26&year=2011)",
            "Start (ET)": "7:30p",
            "Visitor/Neutral": "[Toronto Raptors](/teams/TOR/2012.html)",
            "PTS": 120,
            "Home/Neutral": "[Cleveland Cavaliers](/teams/CLE/2012.html)",
            "PTS.1": 115,
            "": "OT",
            "Attend.": "18,456",
            "LOG": "2:55",
            "Arena": "Quicken Loans Arena",
            "Notes": "",
        },
        {
            # Double overtime game
            "Date": "[Tue, Dec 27, 2011](/boxscores/index.fcgi?month=12&day=27&year=2011)",
            "Start (ET)": "8:00p",
            "Visitor/Neutral": "[Los Angeles Lakers](/teams/LAL/2012.html)",
            "PTS": 130,
            "Home/Neutral": "[Chicago Bulls](/teams/CHI/2012.html)",
            "PTS.1": 128,
            "": "2OT",
            "Attend.": "21,000",
            "LOG": "3:15",
            "Arena": "United Center",
            "Notes": "",
        },
    ]

    # Transform data
    transformer = NBAGameDataTransformer()
    df = transformer.transform_raw_data(sample_data)

    # Basic validation
    assert transformer.validate_transformed_data(df)

    # Print transformed data
    print("\nTransformed Data Sample:")
    print(
        df[
            [
                "game_date",
                "visitor_team_code",
                "visitor_team_points",
                "home_team_code",
                "home_team_points",
                "overtime_periods",
                "home_team_won",
                "visitor_team_won",
                "is_overtime",
            ]
        ]
    )

    # Verify specific transformations
    assert len(df) == 3  # Should have 3 games

    # Check regular game
    regular_game = df.iloc[0]
    assert regular_game["overtime_periods"] == 0
    assert regular_game["is_overtime"] == 0
    assert regular_game["home_team_won"] == 1
    assert regular_game["visitor_team_won"] == 0
    assert regular_game["visitor_team_points"] == 104
    assert regular_game["home_team_points"] == 106

    # Check overtime game
    ot_game = df.iloc[1]
    assert ot_game["overtime_periods"] == 1
    assert ot_game["is_overtime"] == 1
    assert ot_game["visitor_team_won"] == 1
    assert ot_game["home_team_won"] == 0
    assert ot_game["visitor_team_points"] == 120
    assert ot_game["home_team_points"] == 115

    # Check double overtime game
    double_ot_game = df.iloc[2]
    assert double_ot_game["overtime_periods"] == 2
    assert double_ot_game["is_overtime"] == 1
    assert double_ot_game["visitor_team_won"] == 1
    assert double_ot_game["home_team_won"] == 0
    assert double_ot_game["visitor_team_points"] == 130
    assert double_ot_game["home_team_points"] == 128

    # Verify data types
    print("\nData Types:")
    print(df.dtypes)

    # Get database-ready format
    db_data = transformer.get_database_ready_dict(df)
    print("\nDatabase-Ready Format (First Record):")
    print(db_data[0])


if __name__ == "__main__":
    test_data_transformation()
