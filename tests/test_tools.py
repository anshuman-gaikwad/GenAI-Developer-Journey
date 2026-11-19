from datetime import date

from app.tools import (
    add_two_years,
    commission_and_fee_finder,
)


def test_add_two_years():
    result = add_two_years(date(2024, 1, 10))
    assert result == date(2026, 1, 10)


def test_add_two_years_leap_year():
    result = add_two_years(date(2024, 2, 29))
    assert result == date(2026, 2, 28)


def test_district_commission_and_fee():
    result = commission_and_fee_finder(38000, "2024-01-10")

    assert result["commission"] == "District Commission"
    assert result["filing_fee"] == 0
    assert result["last_date_to_file"] == "2026-01-10"


def test_state_commission():
    result = commission_and_fee_finder(6000000, "2024-01-10")

    assert result["commission"] == "State Commission"
    assert result["filing_fee"] == 2000


def test_invalid_amount():
    result = commission_and_fee_finder(0, "2024-01-10")

    assert "error" in result
    assert result["error"] == "Amount must be greater than zero."


def test_invalid_date():
    result = commission_and_fee_finder(38000, "invalid-date")

    assert "error" in result
