"""
Mortgage Broker Tools

Tools for mortgage brokers to query different lenders for rate quotes.
Each broker specializes in one or more lenders.
"""

import json
import random
from typing import Any, Dict


def query_lender_wellsfargo(loan_number: str) -> str:
    """
    Query Wells Fargo for mortgage rate quote.

    Args:
        loan_number: The loan application number

    Returns:
        Rate quote information from Wells Fargo
    """
    # Simulate rate quote from Wells Fargo
    base_rate = 6.5
    variance = random.uniform(-0.3, 0.3)
    rate = round(base_rate + variance, 3)

    points = random.uniform(0, 2)

    quote = {
        "lender": "Wells Fargo",
        "loan_number": loan_number,
        "interest_rate": rate,
        "points": round(points, 2),
        "lock_period_days": 45,
        "closing_cost_estimate": random.randint(3000, 5000),
        "quote_valid_until": "2024-02-15"
    }

    return json.dumps(quote, indent=2)


def query_lender_bankofamerica(loan_number: str) -> str:
    """
    Query Bank of America for mortgage rate quote.

    Args:
        loan_number: The loan application number

    Returns:
        Rate quote information from Bank of America
    """
    base_rate = 6.45
    variance = random.uniform(-0.3, 0.3)
    rate = round(base_rate + variance, 3)

    points = random.uniform(0, 2)

    quote = {
        "lender": "Bank of America",
        "loan_number": loan_number,
        "interest_rate": rate,
        "points": round(points, 2),
        "lock_period_days": 60,
        "closing_cost_estimate": random.randint(2800, 4800),
        "quote_valid_until": "2024-02-15"
    }

    return json.dumps(quote, indent=2)


def query_lender_chase(loan_number: str) -> str:
    """
    Query Chase for mortgage rate quote.

    Args:
        loan_number: The loan application number

    Returns:
        Rate quote information from Chase
    """
    base_rate = 6.55
    variance = random.uniform(-0.3, 0.3)
    rate = round(base_rate + variance, 3)

    points = random.uniform(0, 2)

    quote = {
        "lender": "Chase",
        "loan_number": loan_number,
        "interest_rate": rate,
        "points": round(points, 2),
        "lock_period_days": 45,
        "closing_cost_estimate": random.randint(3200, 5200),
        "quote_valid_until": "2024-02-15"
    }

    return json.dumps(quote, indent=2)


def query_lender_quicken(loan_number: str) -> str:
    """
    Query Quicken Loans (Rocket Mortgage) for mortgage rate quote.

    Args:
        loan_number: The loan application number

    Returns:
        Rate quote information from Quicken Loans
    """
    base_rate = 6.4
    variance = random.uniform(-0.3, 0.3)
    rate = round(base_rate + variance, 3)

    points = random.uniform(0, 1.5)

    quote = {
        "lender": "Quicken Loans",
        "loan_number": loan_number,
        "interest_rate": rate,
        "points": round(points, 2),
        "lock_period_days": 30,
        "closing_cost_estimate": random.randint(2500, 4500),
        "quote_valid_until": "2024-02-10"
    }

    return json.dumps(quote, indent=2)


def query_lender_usbank(loan_number: str) -> str:
    """
    Query US Bank for mortgage rate quote.

    Args:
        loan_number: The loan application number

    Returns:
        Rate quote information from US Bank
    """
    base_rate = 6.48
    variance = random.uniform(-0.3, 0.3)
    rate = round(base_rate + variance, 3)

    points = random.uniform(0, 2)

    quote = {
        "lender": "US Bank",
        "loan_number": loan_number,
        "interest_rate": rate,
        "points": round(points, 2),
        "lock_period_days": 45,
        "closing_cost_estimate": random.randint(2900, 4900),
        "quote_valid_until": "2024-02-15"
    }

    return json.dumps(quote, indent=2)
