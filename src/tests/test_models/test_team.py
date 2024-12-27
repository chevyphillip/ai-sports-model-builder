import pytest
from sqlalchemy.exc import IntegrityError
from src.models.team import Team, SportType


def test_team_creation():
    """Test basic team creation with required fields."""
    team = Team(
        name="Lakers",
        abbreviation="LAL",
        city="Los Angeles",
        sport=SportType.NBA,
        division="Pacific",
        conference="Western",
    )

    assert team.name == "Lakers"
    assert team.abbreviation == "LAL"
    assert team.city == "Los Angeles"
    assert team.sport == SportType.NBA
    assert team.division == "Pacific"
    assert team.conference == "Western"


def test_team_string_representation():
    """Test string representation of team."""
    team = Team(
        name="Lakers", abbreviation="LAL", city="Los Angeles", sport=SportType.NBA
    )

    assert str(team) == "Los Angeles Lakers (NBA)"


def test_sport_type_enum():
    """Test SportType enumeration."""
    assert SportType.NBA.value == "NBA"
    assert SportType.NFL.value == "NFL"
    assert SportType.NHL.value == "NHL"

    # Test that we can create teams for all sport types
    for sport in SportType:
        team = Team(
            name=f"Test {sport.value}",
            abbreviation=f"T{sport.value}",
            city="Test City",
            sport=sport,
        )
        assert team.sport == sport


def test_required_fields():
    """Test that required fields raise appropriate errors when missing."""
    required_fields = ["name", "abbreviation", "city", "sport"]

    # Create a valid team dict
    valid_team = {
        "name": "Lakers",
        "abbreviation": "LAL",
        "city": "Los Angeles",
        "sport": SportType.NBA,
    }

    # Test omitting each required field
    for field in required_fields:
        team_data = valid_team.copy()
        del team_data[field]

        with pytest.raises(IntegrityError):
            Team(**team_data)


def test_team_to_dict():
    """Test conversion of team model to dictionary."""
    team = Team(
        name="Lakers",
        abbreviation="LAL",
        city="Los Angeles",
        sport=SportType.NBA,
        division="Pacific",
        conference="Western",
        venue="Crypto.com Arena",
    )

    team_dict = team.to_dict()
    assert team_dict["name"] == "Lakers"
    assert team_dict["abbreviation"] == "LAL"
    assert team_dict["city"] == "Los Angeles"
    assert team_dict["sport"] == SportType.NBA
    assert team_dict["division"] == "Pacific"
    assert team_dict["conference"] == "Western"
    assert team_dict["venue"] == "Crypto.com Arena"
