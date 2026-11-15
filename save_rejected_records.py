
import json
import mysql.connector
from logger_setup import logger
from db_config import DB_CONFIG


def save_rejected_records(source_table, records):
    if not records:
        print("No rejected records found.")
        return

    connection = None
    cursor = None

    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        query = """
            INSERT INTO rejected_records
            (source_table, record_id, rejection_reason, record_data)
            VALUES (%s, %s, %s, %s)
        """

        for record in records:
            cursor.execute(
                query,
                (
                    source_table,
                    str(record["record_id"]),
                    record["reason"],
                    json.dumps(record["data"], default=str)
                )
            )

        connection.commit()

        print(f"{len(records)} rejected records saved.")
        logger.info(
            "%s rejected records saved for %s",
            len(records),
            source_table
        )

    except Exception:
        if connection:
            connection.rollback()

        logger.exception("Failed to save rejected records.")
        raise

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


if __name__ == "__main__":

    sample_rejections = [
        {
            "record_id": 1005,
            "reason": "Missing email address",
            "data": {
                "customer_id": 1005,
                "first_name": "John",
                "last_name": "Smith",
                "email": None
            }
        },
        {
            "record_id": 1006,
            "reason": "Missing first name",
            "data": {
                "customer_id": 1006,
                "first_name": None,
                "last_name": "David",
                "email": "john@example.com"
            }
        }
    ]

    save_rejected_records("customers", sample_rejections)
