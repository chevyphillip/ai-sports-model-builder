import factory
from factory.faker import Faker
from src.models.team import Team, SportType


class TeamFactory(factory.Factory):
    """Factory for creating Team instances for testing."""

    class Meta:
        model = Team

    name = Faker("company")
    abbreviation = factory.LazyAttribute(lambda o: o.name[:3].upper())
    city = Faker("city")
    sport = factory.Iterator([SportType.NBA, SportType.NFL, SportType.NHL])
    division = Faker("word")
    conference = factory.Iterator(["Eastern", "Western"])
    venue = Faker("company")
