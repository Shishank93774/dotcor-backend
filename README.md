# Dotcor Backend

A concurrency-safe doctor appointment booking system built with FastAPI and PostgreSQL.

## 🚀 Getting Started

This project is powered by [uv](https://github.com/astral-sh/uv) for fast, reliable Python package and project management.

### Prerequisites
- Python 3.14+
- Docker & Docker Compose
- `uv` installed on your local machine

### Environment Setup
The project requires environment variables to be set. Create the following files in the root and `app/core/` respectively:

#### `.env` (Local API Settings)
```env
ENVIRONMENT_NAME=local
DATABASE_USER=
DATABASE_PASSWORD=
DATABASE_NAME=
DATABASE_HOST=localhost
DATABASE_PORT=
DEBUG=
```

#### `app/core/.env` (Infrastructure Settings)
```env
ENVIRONMENT_NAME=prod
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
DATABASE_HOST=db
DATABASE_PORT=
DEBUG=
```

### Running with Docker (Recommended)
The easiest way to start the entire stack (API + Database) is using Docker Compose:

1. **Build and start the containers in the background:**
   ```bash
   docker-compose up -d --build
   ```

2. **Verify the containers are running:**
   ```bash
   docker ps
   ```

- **Backend API:** [http://localhost:8000](http://localhost:8000)
- **PostgreSQL DB:** `localhost:5433` (mapped from `5432` in container)

3. **Stop the containers:**
   ```bash
   docker-compose down
   ```

### Running Locally (Development)
If you prefer running the backend without Docker:

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Start the server:**
   ```bash
   uv run uvicorn app.main:app --reload
   ```
   The server will be available at [http://localhost:8000](http://localhost:8000).

## 🧪 Testing

The project uses `pytest` for automated testing.

To run all tests:
```bash
uv run pytest
```

## 🛠 Tech Stack
- **Language:** Python 3.14
- **Framework:** FastAPI
- **Database:** PostgreSQL 18.4
- **ORM:** SQLAlchemy
- **Package Manager:** uv
- **Containerization:** Docker
