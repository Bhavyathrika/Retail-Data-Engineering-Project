
import os
from pipeline_metrics import save_pipeline_metrics
import pandas as pd
import mysql.connector
from datetime import date, datetime
from decimal import Decimal
from logger_setup import logger
from db_config import DB_CONFIG

CSV_PATH = r"C:\Users\nihar\Downloads\data_engineering_sample_data\orders_source.csv"

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
    logger.info("Order incremental loading started")

    # Read source CSV
    df = pd.read_csv(CSV_PATH)
    

    print("Order dates found in CSV:")
    print(df["order_date"].drop_duplicates().to_list())

    # Order dates are in YYYY-MM-DD format
    df["order_date"] = pd.to_datetime(
    df["order_date"],
    format="%d-%m-%Y",
    errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    if df["order_date"].isna().any():
        raise ValueError("Invalid order dates found.")

    invalid_dates = df[df["order_date"].isna()]

    if not invalid_dates.empty:
        print("Invalid order date records:")
        print(invalid_dates.to_string(index=False))
        raise ValueError("Invalid order dates found.")

    if df["order_date"].isna().any():
        raise ValueError("Invalid order dates found.")

    print("Source order records:", len(df))

    # Connect to MySQL
    connection = mysql.connector.connect(**DB_CONFIG)

    cursor = connection.cursor()

    # Fetch existing order records
    cursor.execute("""
        SELECT order_id, customer_id, order_date,
               product, quantity, unit_price, order_status
        FROM orders
    """)

    existing = {
        int(row[0]): row[1:]
        for row in cursor.fetchall()
    }

    new_records = []
    updated_records = []

    columns = [
        "order_id", "customer_id", "order_date",
        "product", "quantity", "unit_price", "order_status"
    ]

    # Compare source and target
    for row in df[columns].itertuples(index=False, name=None):

        record = (
            int(row[0]),
            *[normalize(value) for value in row[1:]]
        )

        order_id = record[0]

        if order_id not in existing:
            new_records.append(record)

        elif tuple(
            normalize(value) for value in existing[order_id]
        ) != record[1:]:
            updated_records.append(record)

    # Insert new and update changed records
    records_to_load = new_records + updated_records

    if records_to_load:
        query = """
            INSERT INTO orders
            (order_id, customer_id, order_date,
             product, quantity, unit_price, order_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                customer_id = VALUES(customer_id),
                order_date = VALUES(order_date),
                product = VALUES(product),
                quantity = VALUES(quantity),
                unit_price = VALUES(unit_price),
                order_status = VALUES(order_status)
        """

        cursor.executemany(query, records_to_load)
        connection.commit()

    unchanged = len(df) - len(records_to_load)

    print("New orders:", len(new_records))
    print("Updated orders:", len(updated_records))
    print("Unchanged orders:", unchanged)

    logger.info(
        "Order loading completed. New: %s, Updated: %s, Unchanged: %s",
        len(new_records), len(updated_records), unchanged
    )

    print("Order incremental loading completed!")
    save_pipeline_metrics(
    run_id=os.getenv("PIPELINE_RUN_ID", "MANUAL-RUN"),
    step_name="load_orders.py",
    source_rows=len(df),
    inserted_rows=len(new_records),
    updated_rows=len(updated_records),
    unchanged_rows=unchanged,
    rejected_rows=0
    )

except Exception:
    if connection:
        connection.rollback()

    logger.exception("Order incremental loading failed")
    raise

finally:
    if cursor:
        cursor.close()

    if connection and connection.is_connected():
        connection.close()

    logger.info("Order connection cleanup completed")
