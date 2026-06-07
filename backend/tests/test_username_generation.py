"""
Unit tests for username and password generation utilities.
"""
from datetime import date
from app.utils.username import generate_username, ensure_unique_username, generate_default_password


class TestGenerateUsername:
    def test_standard_names(self):
        assert generate_username("John", "Doe") == "doejohn"
        assert generate_username("Alice", "Smith") == "smitalic"
        assert generate_username("Bob", "Johnson") == "johnbob"

    def test_short_names(self):
        assert generate_username("Jo", "Li") == "lijo"
        assert generate_username("Ann", "Wu") == "wuann"
        assert generate_username("A", "B") == "ba"

    def test_names_with_accents(self):
        assert generate_username("François", "Müller") == "mullfran"
        assert generate_username("José", "García") == "garcjose"

    def test_names_with_hyphens_and_spaces(self):
        # Hyphens become spaces after normalize — first 4 chars of "de la cruz" = "de l"
        result = generate_username("Jean-Pierre", "De La Cruz")
        assert len(result) <= 8
        assert result.islower()

    def test_case_insensitive(self):
        assert generate_username("JOHN", "DOE") == "doejohn"
        assert generate_username("JoHn", "DoE") == "doejohn"


class TestEnsureUniqueUsername:
    def test_unique_no_collision(self):
        result = ensure_unique_username("doejohn", set())
        assert result == "doejohn"

    def test_collision_adds_suffix(self):
        existing = {"doejohn"}
        result = ensure_unique_username("doejohn", existing)
        assert result == "doejohn01"

    def test_multiple_collisions(self):
        existing = {"doejohn", "doejohn01", "doejohn02"}
        result = ensure_unique_username("doejohn", existing)
        assert result == "doejohn03"

    def test_no_collision_returns_base(self):
        existing = {"other", "names"}
        result = ensure_unique_username("doejohn", existing)
        assert result == "doejohn"


class TestGenerateDefaultPassword:
    def test_password_with_birthdate(self):
        password = generate_default_password("doejohn", date(1990, 5, 15))
        assert password == "doejohn15051990"

    def test_password_without_birthdate(self):
        p1 = generate_default_password("doejohn", None)
        p2 = generate_default_password("doejohn", None)
        assert len(p1) >= 12
        assert p1 != p2  # random each time

    def test_date_format_ddmmyyyy(self):
        password = generate_default_password("test", date(2000, 1, 9))
        assert password == "test09012000"
