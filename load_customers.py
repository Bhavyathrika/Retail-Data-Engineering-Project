
import os
from pipeline_metrics import save_pipeline_metrics
import pandas as pd
import mysql.connector
from datetime import date, datetime
from decimal import Decimal
from logger_setup import logger
from db_config import DB_CONFIG

CSV_PATH = r"C:\Users\nihar\Downloads\data_engineering_sample_data\customers_source.csv"

connection = None
cursor = None


def normalize(value):
    if value is None or pd.isna(value):
        return None

    if isinstance(value, (datetime, date)):
        return value.strftime("%Y-%m-%d")

    if isinstance(value, (int, float, Decimal)):
        return round(float(value), 2)

    return str(value).strip()


try:
    logger.info("Customer incremental loading started")

    # Read source CSV
    df = pd.read_csv(CSV_PATH)

    # Parse customer dates (DD-MM-YYYY)
    df["signup_date"] = pd.to_datetime(
        df["signup_date"],
        format="mixed",
        dayfirst=True,
        errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    if df["signup_date"].isna().any():
        raise ValueError("Invalid customer signup dates found.")

    print("Source customer records:", len(df))

    # Connect to MySQL
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()

    # Fetch existing customer records
    cursor.execute("""
        SELECT customer_id, first_name, last_name,
               email, city, signup_date
        FROM customers
    """)

    existing = {
        int(row[0]): row[1:]
        for row in cursor.fetchall()
    }

    new_records = []
    updated_records = []

    columns = [
        "customer_id", "first_name", "last_name",
        "email", "city", "signup_date"
    ]

    # Compare source and target
    for row in df[columns].itertuples(index=False, name=None):

        record = (
            int(row[0]),
            *[normalize(value) for value in row[1:]]
        )

        customer_id = record[0]

        if customer_id not in existing:
            new_records.append(record)

        elif tuple(
            normalize(value) for value in existing[customer_id]
        ) != record[1:]:
            updated_records.append(record)

    # Insert new and update changed records
    records_to_load = new_records + updated_records

    if records_to_load:
        query = """
            INSERT INTO customers
            (customer_id, first_name, last_name,
             email, city, signup_date)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                first_name = VALUES(first_name),
                last_name = VALUES(last_name),
                email = VALUES(email),
                city = VALUES(city),
                signup_date = VALUES(signup_date)
        """

        cursor.executemany(query, records_to_load)
        connection.commit()

    unchanged = len(df) - len(records_to_load)

    print("New customers:", len(new_records))
    print("Updated customers:", len(updated_records))
    print("Unchanged customers:", unchanged)

    logger.info(
        "Customer loading completed. New: %s, Updated: %s, Unchanged: %s",
        len(new_records), len(updated_records), unchanged
    )

    print("Customer incremental loading completed!")
    save_pipeline_metrics(
    run_id=os.getenv("PIPELINE_RUN_ID", "MANUAL-RUN"),
    step_name="load_customers.py",
    source_rows=len(df),
    inserted_rows=len(new_records),
    updated_rows=len(updated_records),
    unchanged_rows=unchanged,
    rejected_rows=0
    )

except Exception:
    if connection:
        connection.rollback()

    logger.exception("Customer incremental loading failed")
    raise

finally:
    if cursor:
        cursor.close()

    if connection and connection.is_connected():
        connection.close()

    logger.info("Customer connection cleanup completed")
