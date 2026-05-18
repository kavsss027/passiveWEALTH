from datetime import date
from app.utils.date_utils import parse_iso_date, format_iso_date

def test_parse_iso_date():
    assert parse_iso_date("2024-01-01") == date(2024, 1, 1)

def test_format_iso_date():
    assert format_iso_date(date(2024, 1, 1)) == "2024-01-01"
