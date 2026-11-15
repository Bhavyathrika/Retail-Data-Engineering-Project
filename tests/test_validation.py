
import pandas as pd

from validation_utils import (
    find_missing_emails,
    find_missing_names,
    find_invalid_orders
)


def test_missing_email_detection():
    df = pd.DataFrame({
        "email": ["a@test.com", None, "b@test.com"]
    })

    result = find_missing_emails(df)

    assert len(result) == 1


def test_missing_name_detection():
    df = pd.DataFrame({
        "first_name": ["John", None],
        "last_name": ["Smith", "David"]
    })

    result = find_missing_names(df)

    assert len(result) == 1


def test_invalid_order_detection():
    df = pd.DataFrame({
        "quantity": [2, 0, 3],
        "unit_price": [100, 200, -50]
    })

    result = find_invalid_orders(df)

    assert len(result) == 2
