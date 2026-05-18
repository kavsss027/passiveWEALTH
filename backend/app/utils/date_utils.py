from datetime import date, datetime

def parse_iso_date(date_str: str) -> date:
    """Parse YYYY-MM-DD string to date."""
    return datetime.strptime(date_str, "%Y-%m-%d").date()

def format_iso_date(d: date) -> str:
    """Format date to YYYY-MM-DD string."""
    return d.strftime("%Y-%m-%d")
