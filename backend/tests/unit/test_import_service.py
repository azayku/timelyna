"""Unit tests for import service."""
import pytest
from app.services.import_service import parse_csv


def test_parse_csv_valid():
    """Test parsing valid CSV content."""
    content = b"email,first_name,last_name\njohn@example.com,John,Doe\njane@example.com,Jane,Smith"
    rows, errors = parse_csv(content, ["email", "first_name", "last_name"])
    
    assert len(errors) == 0
    assert len(rows) == 2
    assert rows[0]["email"] == "john@example.com"
    assert rows[0]["first_name"] == "John"
    assert rows[1]["email"] == "jane@example.com"


def test_parse_csv_missing_columns():
    """Test CSV with missing required columns."""
    content = b"email,first_name\njohn@example.com,John"
    rows, errors = parse_csv(content, ["email", "first_name", "last_name"])
    
    assert len(errors) == 1
    assert "Colonnes manquantes" in errors[0]
    assert "last_name" in errors[0]


def test_parse_csv_utf8_bom():
    """Test CSV with UTF-8 BOM."""
    content = b"\xef\xbb\xbfemail,name\ntest@example.com,Test"
    rows, errors = parse_csv(content, ["email", "name"])
    
    assert len(errors) == 0
    assert len(rows) == 1
    assert rows[0]["email"] == "test@example.com"


def test_parse_csv_empty():
    """Test empty CSV file."""
    content = b""
    rows, errors = parse_csv(content, ["email"])
    
    assert len(errors) == 1
    assert "vide" in errors[0].lower()


def test_parse_csv_strips_whitespace():
    """Test that CSV parser strips whitespace from values."""
    content = b"email,name\n  john@example.com  ,  John Doe  "
    rows, errors = parse_csv(content, ["email", "name"])
    
    assert len(errors) == 0
    assert rows[0]["email"] == "john@example.com"
    assert rows[0]["name"] == "John Doe"
