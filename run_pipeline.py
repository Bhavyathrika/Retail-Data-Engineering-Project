import os
import subprocess
import sys
import uuid
from datetime import datetime
from db_config import DB_CONFIG

import mysql.connector
from logger_setup import logger


# Database connection

pipeline_name = "Retail Data Pipeline"
run_id = str(uuid.uuid4())


env = os.environ.copy()
env["PIPELINE_RUN_ID"] = run_id

pipeline_steps = [
    "load_customers.py",
    "load_orders.py",
    "data_quality_checks.py"
]


def update_audit(status, end_time=None, error_message=None):
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()

    query = """
        UPDATE pipeline_audit
        SET status = %s,
            end_time = %s,
            error_message = %s
        WHERE run_id = %s
    """

    cursor.execute(
        query,
        (status, end_time, error_message, run_id)
    )

    connection.commit()
    cursor.close()
    connection.close()


try:
    # Create audit record
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()

    start_time = datetime.now()

    query = """
        INSERT INTO pipeline_audit
        (run_id, pipeline_name, start_time, status)
        VALUES (%s, %s, %s, %s)
    """

    cursor.execute(
        query,
        (run_id, pipeline_name, start_time, "RUNNING")
    )

    connection.commit()
    cursor.close()
    connection.close()

    logger.info("Pipeline started. Run ID: %s", run_id)

    # Execute pipeline steps
    for step in pipeline_steps:
        print(f"\nStarting: {step}")
        logger.info("Starting: %s", step)

        subprocess.run(
        [sys.executable, step],
        check=True,
        env=env
)

        print(f"Completed: {step}")
        logger.info("Completed: %s", step)

    # Mark pipeline as successful
    update_audit("SUCCESS", datetime.now())

    print("\nRetail pipeline completed successfully!")
    logger.info("Pipeline completed successfully.")

except Exception as error:
    error_message = str(error)

    print("\nPipeline failed!")
    print("Error:", error_message)

    logger.exception("Pipeline failed.")

    try:
        update_audit(
            "FAILED",
            datetime.now(),
            error_message
        )
    except Exception:
        logger.exception("Could not update audit table.")

    sys.exit(1)










# import subprocess
# import sys
# from logger_setup import logger

# # List of pipeline tasks in execution order
# pipeline_steps = [
#     "load_customers.py",
#     "load_orders.py",
#     "data_quality_checks.py"
# ]

# logger.info("========== RETAIL PIPELINE STARTED ==========")

# try:
#     for step in pipeline_steps:

#         print(f"\nStarting: {step}")
#         logger.info("Starting pipeline step: %s", step)

#         # Execute the Python script
#         subprocess.run(
#             [sys.executable, step],
#             check=True
#         )

#         print(f"Completed: {step}")
#         logger.info("Completed pipeline step: %s", step)

#     print("\nRetail pipeline completed successfully!")
#     logger.info("========== RETAIL PIPELINE COMPLETED SUCCESSFULLY ==========")

# except subprocess.CalledProcessError:
#     print("\nPipeline failed! Check pipeline.log for details.")
#     logger.exception("Retail pipeline failed.")
#     sys.exit(1)
