
import pandas as pd
import mysql.connector
from logger_setup import logger
from db_config import DB_CONFIG

CUSTOMERS_CSV = r"C:\Users\nihar\Downloads\data_engineering_sample_data\customers_source.csv"
ORDERS_CSV = r"C:\Users\nihar\Downloads\data_engineering_sample_data\orders_source.csv"

connection = None
cursor = None
failed_checks = 0


def normalize_dates(series, date_format=None, dayfirst=False):
    if date_format:
        parsed = pd.to_datetime(
            series, format=date_format, errors="coerce"
        )
    else:
        parsed = pd.to_datetime(
            series, format="mixed",
            dayfirst=dayfirst, errors="coerce"
        )

    return parsed.dt.strftime("%Y-%m-%d")


def compare_records(source, target, key, columns):
    merged = source.merge(
        target,
        on=key,
        how="outer",
        suffixes=("_source", "_target"),
        indicator=True
    )

    mismatch = merged["_merge"] != "both"

    for column in columns:
        source_values = merged[f"{column}_source"]
        target_values = merged[f"{column}_target"]

        different = (
            source_values.ne(target_values)
            & ~(source_values.isna() & target_values.isna())
        )

        mismatch = mismatch | different

    return merged[mismatch]


try:
    logger.info("Data quality checks started")

    # Connect to MySQL
    connection = mysql.connector.connect(**DB_CONFIG)

    cursor = connection.cursor(dictionary=True)

    # Read source files
    customers_source = pd.read_csv(CUSTOMERS_CSV)
    orders_source = pd.read_csv(ORDERS_CSV)

    # ------------------------------------------------
    # 1. Missing Email Check
    # ------------------------------------------------

    print("\n--- Missing Email Check ---")

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM customers
        WHERE email IS NULL OR TRIM(email) = ''
    """)

    missing_email = cursor.fetchone()["total"]

    if missing_email > 0:
        failed_checks += 1
        print("FAIL:", missing_email, "customers have missing emails.")
        logger.warning("Missing email check failed")
    else:
        print("PASS: All customers have email addresses.")
        logger.info("Missing email check passed")

    # ------------------------------------------------
    # 2. Missing Name Check
    # ------------------------------------------------

    print("\n--- Missing Name Check ---")

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM customers
        WHERE first_name IS NULL OR TRIM(first_name) = ''
        OR last_name IS NULL OR TRIM(last_name) = ''
    """)

    missing_names = cursor.fetchone()["total"]

    if missing_names > 0:
        failed_checks += 1
        print("FAIL:", missing_names, "customers have missing names.")
        logger.warning("Missing name check failed")
    else:
        print("PASS: All customers have first and last names.")
        logger.info("Missing name check passed")

    # ------------------------------------------------
    # 3. Invalid Quantity and Price Check
    # ------------------------------------------------

    print("\n--- Invalid Quantity and Price Check ---")

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM orders
        WHERE quantity IS NULL OR quantity <= 0
        OR unit_price IS NULL OR unit_price < 0
    """)

    invalid_orders = cursor.fetchone()["total"]

    if invalid_orders > 0:
        failed_checks += 1
        print("FAIL:", invalid_orders, "orders have invalid values.")
        logger.warning("Quantity and price check failed")
    else:
        print("PASS: All orders have valid quantities and prices.")
        logger.info("Quantity and price check passed")

    # ------------------------------------------------
    # 4. Customer Reference Check
    # ------------------------------------------------

    print("\n--- Customer Reference Check ---")

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM orders o
        LEFT JOIN customers c
        ON o.customer_id = c.customer_id
        WHERE c.customer_id IS NULL
    """)

    invalid_references = cursor.fetchone()["total"]

    if invalid_references > 0:
        failed_checks += 1
        print("FAIL:", invalid_references, "orders have invalid customer IDs.")
        logger.warning("Customer reference check failed")
    else:
        print("PASS: All orders reference existing customers.")
        logger.info("Customer reference check passed")

    # ------------------------------------------------
    # 5. Customer Record Reconciliation
    # ------------------------------------------------

    print("\n--- Customer Record Reconciliation ---")

    customers_source_compare = customers_source.copy()

    customers_source_compare["signup_date"] = normalize_dates(
        customers_source_compare["signup_date"],
        dayfirst=True
    )

    if customers_source_compare["signup_date"].isna().any():
        failed_checks += 1
        raise ValueError("Invalid customer signup dates in source CSV.")

    cursor.execute("""
        SELECT customer_id, first_name, last_name,
               email, city, signup_date
        FROM customers
    """)

    customers_target = pd.DataFrame(cursor.fetchall())

    customers_target["signup_date"] = normalize_dates(
        customers_target["signup_date"]
    )

    customer_columns = [
        "first_name", "last_name", "email", "city", "signup_date"
    ]

    customer_mismatches = compare_records(
        customers_source_compare,
        customers_target,
        "customer_id",
        customer_columns
    )

    if not customer_mismatches.empty:
        failed_checks += 1
        print("FAIL: Customer records do not match.")
        print(customer_mismatches.to_string(index=False))
        logger.warning(
            "Customer reconciliation failed: %s mismatches",
            len(customer_mismatches)
        )
    else:
        print("PASS: All customer records match.")
        logger.info("Customer reconciliation passed")

    # ------------------------------------------------
    # 6. Order Record Reconciliation
    # ------------------------------------------------

    print("\n--- Order Record Reconciliation ---")

    orders_source_compare = orders_source.copy()

    orders_source_compare["order_date"] = normalize_dates(
    orders_source_compare["order_date"],
    date_format="%d-%m-%Y"
    )

    if orders_source_compare["order_date"].isna().any():
        failed_checks += 1
        raise ValueError("Invalid order dates in source CSV.")

    cursor.execute("""
        SELECT order_id, customer_id, order_date,
               product, quantity, unit_price, order_status
        FROM orders
    """)

    orders_target = pd.DataFrame(cursor.fetchall())

    orders_target["order_date"] = normalize_dates(
        orders_target["order_date"]
    )

    orders_source_compare["quantity"] = pd.to_numeric(
        orders_source_compare["quantity"], errors="coerce"
    )

    orders_target["quantity"] = pd.to_numeric(
        orders_target["quantity"], errors="coerce"
    )

    orders_source_compare["unit_price"] = pd.to_numeric(
        orders_source_compare["unit_price"], errors="coerce"
    ).round(2)

    orders_target["unit_price"] = pd.to_numeric(
        orders_target["unit_price"], errors="coerce"
    ).round(2)

    order_columns = [
        "customer_id", "order_date", "product",
        "quantity", "unit_price", "order_status"
    ]

    order_mismatches = compare_records(
        orders_source_compare,
        orders_target,
        "order_id",
        order_columns
    )

    if not order_mismatches.empty:
        failed_checks += 1
        print("FAIL: Order records do not match.")
        print(order_mismatches.to_string(index=False))
        logger.warning(
            "Order reconciliation failed: %s mismatches",
            len(order_mismatches)
        )
    else:
        print("PASS: All order records match.")
        logger.info("Order reconciliation passed")

    # ------------------------------------------------
    # 7. Row Count Reconciliation
    # ------------------------------------------------

    print("\n--- Row Count Reconciliation ---")

    source_customer_count = len(customers_source)
    target_customer_count = len(customers_target)

    source_order_count = len(orders_source)
    target_order_count = len(orders_target)

    print("Source customers:", source_customer_count)
    print("Target customers:", target_customer_count)

    if source_customer_count != target_customer_count:
        failed_checks += 1
        print("FAIL: Customer row counts do not match.")
        logger.warning("Customer row count mismatch")
    else:
        print("PASS: Customer row counts match.")

    print("\nSource orders:", source_order_count)
    print("Target orders:", target_order_count)

    if source_order_count != target_order_count:
        failed_checks += 1
        print("FAIL: Order row counts do not match.")
        logger.warning("Order row count mismatch")
    else:
        print("PASS: Order row counts match.")

    # ------------------------------------------------
    # Final Result
    # ------------------------------------------------

    print("\n--- Final Data Quality Result ---")

    if failed_checks > 0:
        print("FAILED CHECKS:", failed_checks)
        logger.error(
            "Data quality validation failed: %s checks",
            failed_checks
        )
        raise RuntimeError("Data quality validation failed.")

    else:
        print("SUCCESS: All data quality checks passed!")
        logger.info("All data quality checks passed")

except Exception:
    if connection:
        connection.rollback()

    logger.exception("Unexpected problem during data quality checks")
    raise

finally:
    if cursor:
        cursor.close()

    if connection and connection.is_connected():
        connection.close()

    print("\nDatabase connection cleanup completed")
