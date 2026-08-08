import argparse
import asyncio
import logging
import subprocess
import sys
from pathlib import Path

from exit import run_exit
from init import run_init

root_dir = Path(__file__).parent.parent.resolve()
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from app.core.config import config  # noqa: E402

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

CWD = Path(__file__).parent.resolve()
LOCUSTFILE_PATH = "./benchmarking/locustfile.py"
HOST = "http://localhost:8000"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-doctors", default=5, choices=range(1, 11), help="Number of doctors to create", type=int)
    parser.add_argument("--num-slots", default=50, choices=[50, 100, 250, 500, 1000, 2000], help="Number of slots to create", type=int)
    parser.add_argument("--num-patients", default=5, choices=range(1, 11), help="Number of patients to create", type=int)
    parser.add_argument("--num-locusts", default=50, choices=range(10, 101, 10), help="Number of locusts to spawn", type=int)
    parser.add_argument("--spawn-rate", default=2, choices=range(1, 6), help="Spawn rate of locusts", type=int)
    parser.add_argument("--run-time", default="1m", help="Duration of the test (e.g., 30s, 1m, 5m)")
    args = parser.parse_args()

    # Sync mode with server config
    mode = config.CONFLICT_HANDLE_MODE
    num_doctors = args.num_doctors
    num_slots = args.num_slots
    num_patients = args.num_patients
    num_locusts = args.num_locusts
    spawn_rate = args.spawn_rate
    run_time = args.run_time
    output_file = CWD / "results" / mode

    # 1. Initialize Data (Async call)
    try:
        asyncio.run(run_init(num_doctors, num_slots, num_patients))
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        return

    # 2. Run Locust Benchmark
    try:
        logger.info(f"Launching Locust benchmark in {mode} mode...")

        cmd = (
            f"locust -f {LOCUSTFILE_PATH} --users {num_locusts} --host {HOST} --spawn-rate {spawn_rate} --headless -t {run_time} --csv {output_file}"
        )

        subprocess.run(cmd, shell=True)
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
