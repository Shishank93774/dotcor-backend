import asyncio
import json
import logging
from pathlib import Path

from aiohttp import ClientError, ClientSession

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

HOST = "http://localhost:8000"
CWD = Path(__file__).parent.resolve() / "json_files"


async def delete_doctor(session: ClientSession):
    try:
        url = HOST + "/users/doctors"
        doctors = []
        filepath = CWD / "doctors.json"

        if not filepath.exists():
            logger.warning("doctors.json not found; nothing to delete")
            return

        with open(filepath, "r") as f:
            for line in f:
                doctors.append(json.loads(line))

        tasks = [session.delete(url + f"/{doctors[i]['id']}") for i in range(len(doctors))]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        deleted = 0

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Doctor deletion request failed: {result}")
                continue
            if result.status == 204:
                deleted += 1
            else:
                logger.warning(f"Doctor deletion returned unexpected status: {result.status}")

        logger.info(f"{deleted} doctors deleted")
    except (ClientError, IOError, json.JSONDecodeError) as e:
        logger.error(f"Critical error deleting doctors: {e}")


async def delete_patients(session: ClientSession):
    try:
        url = HOST + "/users/patients"
        patients = []
        filepath = CWD / "patients.json"

        if not filepath.exists():
            logger.warning("patients.json not found; nothing to delete")
            return

        with open(filepath, "r") as f:
            for line in f:
                patients.append(json.loads(line))

        tasks = [session.delete(url + f"/{patients[i]['id']}") for i in range(len(patients))]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        deleted = 0

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Patient deletion request failed: {result}")
                continue
            if result.status == 204:
                deleted += 1
            else:
                logger.warning(f"Patient deletion returned unexpected status: {result.status}")

        logger.info(f"{deleted} patients deleted")
    except (ClientError, IOError, json.JSONDecodeError) as e:
        logger.error(f"Critical error deleting patients: {e}")


async def run_exit():
    """Entry point for the benchmarking cleanup process."""
    async with ClientSession() as session:
        await delete_doctor(session)
        await delete_patients(session)


async def main():
    await run_exit()


if __name__ == "__main__":
    asyncio.run(main())
