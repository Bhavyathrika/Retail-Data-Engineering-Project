
from logger_setup import logger

try:
    number = int("hello")
    print(number)

except ValueError as e:
    logger.error(f"Invalid number error: {e}")
    print("An error occurred. Check pipeline.log")

finally:
    print("Exception handling test completed.")
