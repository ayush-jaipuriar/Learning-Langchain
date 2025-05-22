import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(module)s - %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)

def run_delivery_agent():
    logger.info("Food Delivery Agent started.")
    # TODO: Initialize and run the LangGraph agent
    logger.info("Food Delivery Agent finished.")

if __name__ == "__main__":
    run_delivery_agent() 