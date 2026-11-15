
import logging
from pathlib import Path

# Create a logs folder automatically
Path("logs").mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    filename="logs/pipeline.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    force=True
)

# Create a reusable logger
logger = logging.getLogger("retail_pipeline")
