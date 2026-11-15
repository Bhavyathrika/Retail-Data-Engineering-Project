
import os
import mysql.connector
from logger_setup import logger
from db_config import DB_CONFIG

def save_pipeline_metrics(
    run_id,
    step_name,
    source_rows,
    inserted_rows,
    updated_rows,
    unchanged_rows,
    rejected_rows=0
):
    connection = None
    cursor = None

    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        query = """
            INSERT INTO pipeline_step_metrics (
                run_id, step_name, source_rows,
                inserted_rows, updated_rows,
                unchanged_rows, rejected_rows
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(query, (
            run_id, step_name, source_rows,
            inserted_rows, updated_rows,
            unchanged_rows, rejected_rows
        ))

        connection.commit()
        logger.info("Metrics saved for %s", step_name)

    except Exception:
        if connection:
            connection.rollback()
        logger.exception("Metrics saving failed")
        raise

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    save_pipeline_metrics(
        run_id="TEST-RUN-001",
        step_name="load_customers.py",
        source_rows=10,
        inserted_rows=2,
        updated_rows=1,
        unchanged_rows=7,
        rejected_rows=0
    )
