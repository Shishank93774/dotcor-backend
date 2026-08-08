import argparse
import asyncio
import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from random import randint

from aiohttp import ClientError, ClientSession, TCPConnector

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

HOST = "http://localhost:8000"
CWD = Path(__file__).parent.resolve() / "json_files"


async def create_doctor(session: ClientSession, count: int):
    try:
        url = HOST + "/users/doctors/"
        tasks = [
            session.post(
                url,
                json={
                    "username": f"conc_doctor_{i}",
                    "email": f"conc_doctor_{i}@example.com",
                    "password": "secret",
                    "contact_number": f"+91 7897{i:06d}",
                    "specialization": "General",
                },
            )
            for i in range(count)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        created = 0
        filepath = CWD / "doctors.json"
        CWD.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w") as f:
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Doctor creation request failed: {result}")
                    continue
                if result.status == 201:
                    created += 1
                    json.dump(await result.json(), f)
                    f.write("\n")
                else:
                    logger.warning(f"Doctor creation returned unexpected status: {result.status}")

        logger.info(f"{created} doctors created")
    except (ClientError, IOError) as e:
        logger.error(f"Critical error creating doctors: {e}")


async def create_slots(session: ClientSession, count: int):
    try:
        url = HOST + "/slots/"
        doctors = []
        filepath = CWD / "doctors.json"

        if not filepath.exists():
            logger.error("doctors.json not found; cannot create slots")
            return

        with open(filepath, "r") as f:
            for line in f:
                doctors.append(json.loads(line))

        if not doctors:
            logger.warning("No doctors were created; skipping slot creation")
            return

        current_time = datetime.now(UTC)
        tasks = [
            session.post(
                url,
                json={
                    "doctor_id": doctors[randint(0, len(doctors) - 1)]["id"],
                    "start_time": (current_time + timedelta(hours=i)).isoformat(),
                    "end_time": (current_time + timedelta(hours=i + 1)).isoformat(),
                },
            )
            for i in range(count)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        created = 0
        slot_filepath = CWD / "slots.json"
        with open(slot_filepath, "w") as f:
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Slot creation request failed: {result}")
                    continue
                if result.status == 201:
                    created += 1
                    json.dump(await result.json(), f)
                    f.write("\n")
                else:
                    logger.warning(f"Slot creation returned unexpected status: {result.status}")

        logger.info(f"{created} slots created")
    except (ClientError, IOError, json.JSONDecodeError) as e:
        logger.error(f"Critical error creating slots: {e}")


async def create_patients(session: ClientSession, count: int):
    try:
        url = HOST + "/users/patients/"
        tasks = [
            session.post(
                url,
                json={
                    "username": f"conc_patient_{i}",
                    "email": f"conc_patient_{i}@example.com",
                    "password": "secret",
                    "contact_number": f"+91 7895{i:06d}",
                },
            )
            for i in range(count)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        created = 0
        filepath = CWD / "patients.json"
        with open(filepath, "w") as f:
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Patient creation request failed: {result}")
                    continue
                if result.status == 201:
                    created += 1
                    json.dump(await result.json(), f)
                    f.write("\n")
                else:
                    logger.warning(f"Patient creation returned unexpected status: {result.status}")

        logger.info(f"{created} patients created")
    except (ClientError, IOError) as e:
        logger.error(f"Critical error creating patients: {e}")


async def run_init(num_doctors: int, num_slots: int, num_patients: int):
    """Entry point for the benchmarking initialization process."""
    logger.info(f"Initializing benchmark: {num_doctors} doctors, {num_slots} slots, {num_patients} patients...")

    connector = TCPConnector(
        limit=20,
        limit_per_host=20,
        force_close=True,
        enable_cleanup_closed=True,
    )
    async with ClientSession(connector=connector) as session:
        await create_doctor(session, num_doctors)
        await create_slots(session, num_slots)
        await create_patients(session, num_patients)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-doctors", default=5, type=int)
    parser.add_argument("--num-slots", default=50, type=int)
    parser.add_argument("--num-patients", default=50, type=int)
    args = parser.parse_args()

    await run_init(args.num_doctors, args.num_slots, args.num_patients)


if __name__ == "__main__":
    asyncio.run(main())
