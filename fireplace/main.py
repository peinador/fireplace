#!/usr/bin/env python3
"""
Standalone entry point for running the fireplace directly.

Usage:
    sudo python fireplace/main.py                    # Run for 60 minutes (default)
    sudo python fireplace/main.py --duration 30     # Run for 30 minutes
"""

import argparse
import logging
import signal
import sys

from fireplace.controller import Fireplace

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Run the fireplace animation",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=60,
        help="Duration to run the fireplace in minutes",
    )
    args = parser.parse_args()

    fireplace = Fireplace()

    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, stopping...")
        fireplace.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info(f"Starting fireplace for {args.duration} minutes")
    fireplace.start(duration_minutes=args.duration)

    # Block until fireplace stops (either naturally or via signal)
    fireplace.wait()
    logger.info("Fireplace finished")


if __name__ == "__main__":
    main()
