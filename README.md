
# Retail Data Engineering Project

## Project Overview

An end-to-end Retail Data Engineering Pipeline built
using Python, Pandas and MySQL.

The project extracts customer and order data from CSV
files, validates the data, performs incremental loading,
and stores the processed data in MySQL.

## Technologies Used

- Python
- Pandas
- MySQL
- SQL
- Git and GitHub
- Pytest

## Key Features

1. CSV data ingestion
2. Incremental data loading
3. Insert, update and unchanged record detection
4. Data quality validation
5. Source-to-target reconciliation
6. Rejected-record storage
7. Logging and exception handling
8. Pipeline orchestration
9. Pipeline audit tracking
10. Pipeline execution metrics
11. Data profiling
12. SQL indexing and query analysis
13. Automated testing

## Architecture

CSV Files
    |
    v
Python and Pandas
    |
    v
Data Quality Validation
    |
    v
Incremental ETL Loading
    |
    v
MySQL Database
    |
    v
Source-to-Target Reconciliation
    |
    v
Pipeline Audit and Metrics

## Database Tables

- customers
- orders
- pipeline_audit
- pipeline_step_metrics
- rejected_records

## Project Structure

- load_customers.py
- load_orders.py
- data_quality_checks.py
- data_profiling.py
- run_pipeline.py
- pipeline_metrics.py
- save_rejected_records.py
- db_config.py
- logger_setup.py
- validation_utils.py
- tests/

## How to Run

1. Clone this repository.
2. Create and activate a Python virtual environment.
3. Install dependencies:

   pip install -r requirements.txt

4. Create a MySQL database and required tables.
5. Create a local .env file with database credentials.
6. Run the pipeline:

   python run_pipeline.py

## Run Automated Tests

pytest -v

## Author

Your Name








