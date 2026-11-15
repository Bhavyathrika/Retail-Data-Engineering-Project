
def find_missing_emails(df):
    return df[df["email"].isna() | (df["email"].astype(str).str.strip() == "")]


def find_missing_names(df):
    invalid = (
        df["first_name"].isna()
        | df["last_name"].isna()
        | (df["first_name"].astype(str).str.strip() == "")
        | (df["last_name"].astype(str).str.strip() == "")
    )
    return df[invalid]


def find_invalid_orders(df):
    invalid = (
        pd_numeric_invalid(df["quantity"])
        | pd_numeric_invalid(df["unit_price"])
    )
    return df[invalid]


def pd_numeric_invalid(series):
    import pandas as pd

    values = pd.to_numeric(series, errors="coerce")
    return values.isna() | (values <= 0)
