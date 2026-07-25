import os

os.environ["ENV_FILE"] = "tests/.env"

import pytest
from app.core.config import config as test_config
from app.db.connection import Base, get_db
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

test_engine = create_engine(test_config.DATABASE_URL, echo=test_config.DEBUG)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    with test_engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))
        conn.commit()
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


# ----- Helper fixtures for test data -----
@pytest.fixture
def unique_user_data():
    from itertools import count
    from uuid import uuid4

    phone_counter = count()

    def _generate(role: str):
        unique = uuid4().hex
        n = next(phone_counter)

        # 7899 + six digits = 10-digit Indian mobile number.
        contact_number = f"+917899{n:06d}"

        return {
            "username": f"{role}_{unique}",
            "email": f"{role}_{unique}@example.com",
            "contact_number": contact_number,
        }

    return _generate


@pytest.fixture
def create_doctor(db_session, unique_user_data):
    from app.services.doctor import DoctorService
    from pydantic import SecretStr

    def _create_doctor(
        username=None,
        email=None,
        password="secret",
        contact_number=None,
        specialization="Cardiology",
    ):
        generated = unique_user_data("doctor")

        service = DoctorService(db_session)

        return service.create_doctor(
            username=username or generated["username"],
            email=email or generated["email"],
            password=SecretStr(password),
            contact_number=contact_number or generated["contact_number"],
            specialization=specialization,
        )

    return _create_doctor


@pytest.fixture
def create_patient(db_session, unique_user_data):
    from app.services.patient import PatientService
    from pydantic import SecretStr

    def _create_patient(
        username=None,
        email=None,
        password="secret",
        contact_number=None,
    ):
        generated = unique_user_data("patient")

        service = PatientService(db_session)

        return service.create_patient(
            username=username or generated["username"],
            email=email or generated["email"],
            password=SecretStr(password),
            contact_number=contact_number or generated["contact_number"],
        )

    return _create_patient


@pytest.fixture
def create_slot(db_session, create_doctor):
    from datetime import UTC, datetime, timedelta
    from itertools import count

    from app.services.slot import SlotService

    slot_counter = count()

    def _create_slot(
        doctor_id=None,
        start_time=None,
        end_time=None,
    ):
        service = SlotService(db_session)

        if doctor_id is None:
            doctor = create_doctor()
            doctor_id = doctor.id

        if start_time is None:
            offset = next(slot_counter)
            start_time = datetime.now(UTC) + timedelta(days=1) + timedelta(hours=offset * 2)

        if end_time is None:
            end_time = start_time + timedelta(hours=1)

        return service.create_slot(
            doctor_id=doctor_id,
            start_time=start_time,
            end_time=end_time,
        )

    return _create_slot
