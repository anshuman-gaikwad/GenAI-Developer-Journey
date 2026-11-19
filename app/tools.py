"""
tools.py - GrahakNyay Day 09

Finds the correct Consumer Commission, filing fee,
and indicative last date for filing a complaint.
"""

from datetime import date


def add_two_years(input_date):
    """Add two years, handling leap-day dates safely."""

    try:
        return input_date.replace(year=input_date.year + 2)
    except ValueError:
        # For example, 29 February becomes 28 February.
        return input_date.replace(year=input_date.year + 2, day=28)


def commission_and_fee_finder(amount_paid, cause_date):
    """
    Find commission, complaint fee and indicative filing deadline.

    amount_paid: value paid for goods or services, in rupees
    cause_date: date in YYYY-MM-DD format
    """

    try:
        amount_paid = float(amount_paid)

        if amount_paid <= 0:
            raise ValueError("Amount must be greater than zero.")

        cause_date = date.fromisoformat(cause_date)

        if cause_date > date.today():
            raise ValueError("Cause-of-action date cannot be in the future.")

        # Step 1: Find the Consumer Commission.
        if amount_paid <= 50_00_000:
            commission = "District Commission"
        elif amount_paid <= 2_00_00_000:
            commission = "State Commission"
        else:
            commission = "National Commission"

        # Step 2: Find the filing fee under Rule 7(2).
        if amount_paid <= 5_00_000:
            fee = 0
        elif amount_paid <= 10_00_000:
            fee = 200
        elif amount_paid <= 20_00_000:
            fee = 400
        elif amount_paid <= 50_00_000:
            fee = 1000
        elif amount_paid <= 1_00_00_000:
            fee = 2000
        elif amount_paid <= 2_00_00_000:
            fee = 2500
        elif amount_paid <= 4_00_00_000:
            fee = 3000
        elif amount_paid <= 6_00_00_000:
            fee = 4000
        elif amount_paid <= 8_00_00_000:
            fee = 5000
        elif amount_paid <= 10_00_00_000:
            fee = 6000
        else:
            fee = 7500

        # Step 3: Calculate the indicative two-year deadline.
        last_date = add_two_years(cause_date)

        return {
            "amount_paid": amount_paid,
            "commission": commission,
            "filing_fee": fee,
            "cause_date": cause_date.isoformat(),
            "last_date_to_file": last_date.isoformat(),
            "limitation_note": (
                "Indicative two-year period under Section 69. "
                "The Commission may condone delay for sufficient cause."
            ),
            "sources": [
                "Consumer Protection (Jurisdiction) Rules, 2021",
                (
                    "Consumer Protection (Consumer Disputes Redressal "
                    "Commissions) Rules, 2020, Rule 7(2), as amended in 2023"
                ),
                "Consumer Protection Act, 2019, Section 69",
            ],
        }

    except (ValueError, TypeError) as error:
        return {"error": str(error)}
