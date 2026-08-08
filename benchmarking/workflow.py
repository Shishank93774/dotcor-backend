import argparse
import asyncio
import logging
import subprocess
from pathlib import Path

from exit import run_exit
from init import run_init

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

CWD = Path(__file__).parent.resolve()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-doctors", default=5, choices=range(1, 11), help="Number of doctors to create", type=int)
    parser.add_argument("--num-slots", default=50, choices=[50, 100, 250, 500, 1000, 2000], help="Number of slots to create", type=int)
    parser.add_argument("--num-patients", default=5, choices=range(1, 11), help="Number of patients to create", type=int)
    parser.add_argument("--num-locusts", default=50, choices=range(10, 101, 10), help="Number of locusts to spawn", type=int)
    parser.add_argument("--spawn-rate", default=2, choices=range(1, 6), help="Spawn rate of locusts", type=int)
    args = parser.parse_args()

    # 1. Initialize Data (Async call)
    try:
        asyncio.run(run_init(args.num_doctors, args.num_slots, args.num_patients))
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        return

    # 2. Run Locust Benchmark
    # Locust is a CLI tool that launches its own process and web server,
    # so we keep this as a subprocess call.
    try:
        logger.info("Launching Locust benchmark...")
        subprocess.run(
            f"locust -f ./benchmarking/locustfile.py --users {args.num_locusts} --host http://localhost:8000 --spawn-rate {args.spawn_rate}",
            shell=True,
            check=True,
        )
    except KeyboardInterrupt:
        logger.info("Locust interrupted by user, cleaning up...")
    except subprocess.CalledProcessError as e:
        logger.error(f"Locust execution failed: {e}")
    finally:
        # 3. Cleanup Data (Async call)
        try:
            logger.info("Cleaning up benchmark data...")
            asyncio.run(run_exit())
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


if __name__ == "__main__":
    main()
