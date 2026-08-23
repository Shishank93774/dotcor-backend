# DESIGN.md

Technical design record for the Dotcor backend: what was built, the decisions behind it, and the trade-offs accepted. Sections written during active development of each phase; the concurrency section doubles as an engineering narrative.

## System overview

A doctor appointment booking backend with three shipped capability areas:

1. **Core booking** — doctors publish time slots; patients book them under hard correctness guarantees.
2. **Real-time chat** — patient↔doctor messaging scoped to a booking, with persistence and history replay.
3. **Token-based identity** — minimal session tokens securing WebSocket handshakes and protected reads.

Stack: Python 3.14, FastAPI, PostgreSQL 18, SQLAlchemy 2 (classic mapped models), psycopg2, uvicorn. Tooling: pytest, Locust, Docker/docker-compose, uv.

## Architecture

Three-layer separation with strict dependency direction:

```
api/v1 (routers) → services (domain logic + transactions) → db/models (persistence)
        ↑                    ↑
   core/services.py     core/exceptions.py
  (DI providers)      (domain error hierarchy)
```

- **Routers are thin**: parse/validate input via Pydantic schemas, delegate to a service, return it. No business logic, no DB access beyond what a service returns.
- **Services own transactions**: each service receives a `Session` via constructor injection (`core/services.py` providers) and commits per operation. Cross-entity checks (booking validates the patient exists, slot validates the doctor) are explicit service-to-service calls with local imports to break import cycles.
- **Errors are domain-typed**: services raise `DomainException` subclasses (`ResourceConflictError`, `InvalidInputError`, `ResourceNotFoundError`, `InvalidTokenError`, `UnauthorizedError`, `ServiceError`). A central handler map translates them to HTTP status codes once, so no router ever builds an error response by hand.
- **Schema layering**: `*Create` / `*ReadPublic` / `*ReadPrivate` Pydantic models. List endpoints serialize public views only (username/id/specialization); email and contact number appear solely on single-resource private views. Passwords are `SecretStr` until hashed (argon2 via pwdlib); phone numbers validated to E.164.

## Data model

| Table | Purpose | Key constraints |
|---|---|---|
| `users` | Base identity; polymorphic on `role` | unique username/email/contact_number |
| `doctors`, `patients` | Joined-table inheritance from `users` | FK to `users.id` |
| `slots` | Doctor availability windows | `CheckConstraint(start < end)`; GiST `ExcludeConstraint` on `tstzrange(start,end,'[)') && doctor_id` |
| `bookings` | Patient ↔ slot reservation | Partial unique index `(slot_id) WHERE status != 'cancelled'` |
| `chat_rooms` | One conversation per booking | `UniqueConstraint(booking_id)` |
| `messages` | Chat history | FK room + sender; typed (`text`/`document`) |
| `auths` | One session token per user | unique `user_id`, unique token |

Deliberate stance: **integrity lives in Postgres, not the application**. Overlapping slots are impossible by exclusion constraint, double-bookings by partial index — both hold even if application code regresses. The `btree_gist` extension is created at startup (lifespan).

Schema evolution currently uses `Base.metadata.create_all` at startup. No Alembic yet — acceptable while schema churn is low and pre-production; revisit before Phase 4 touches more tables.

## Concurrency-safe booking (the centerpiece)

The problem this phase exists for: two patients hitting "book" on the same hot slot within milliseconds must yield exactly one winner, deterministically, without tanking throughput for non-conflicting traffic.

**Approach: pessimistic row locking, chosen over OCC after benchmarking.** `create_booking` takes `SELECT ... FOR UPDATE` on the slot row; contenders queue on the lock instead of racing to a conflict. OCC (via SQLAlchemy `version_id_col`, retained on `Slot` for reference) was benchmarked first and lost under high contention: with N concurrent bookers of one slot, optimistic retries produce O(N) rollbacks and nondeterministic winner selection latency, while the pessimistic path serializes briefly on a single-row lock and lets losers exit immediately with a clean 409. Hot-slot contention here is narrow (one row per slot), so pessimistic locking's usual downside — broad lock scope hurting unrelated throughput — doesn't materialize.

**Defense in depth:** the lock alone is not trusted. The partial unique index on `(slot_id) WHERE status != 'cancelled'` makes a double-booking physically unwritable regardless of application bugs. If that safety net ever fires, the `IntegrityError` is disambiguated by SQLSTATE — `unique_violation` (23505) surfaces as 409 "Slot already booked"; any other violation maps to 422 invalid input. The system's last line of defense has a defined, correct API contract.

**Cancellation semantics:** idempotent by design — re-cancelling returns 200 unchanged so client retries are safe; cancelling a `completed` booking is rejected with 409 because it represents an event that already happened.

Proven under test: 75 concurrent ASGI requests on one slot produce exactly 1×201 and 74×409; database state verified afterward shows a single active booking; 50 requests across distinct slots all succeed independently.

## Real-time chat over WebSockets

Scope: exactly two parties per conversation (patient, doctor), keyed to a booking.

- **Transport/domain split.** `WebsocketManager` owns sockets, routing, presence frames, and failure cleanup; `ChatRoomService` owns persistence and orchestration. A process-level `WebsocketRegistry` guarantees one manager instance per room id. This separation kept connection plumbing unit-testable without a server.
- **Room creation race.** Double-checked locking: fast path reuses an existing room without locking; slow path takes `FOR UPDATE` on the booking row, re-checks inside the lock window, and relies on the `UniqueConstraint(booking_id)` as backstop. All racing callers converge on the same room id — proven by an 8-thread barrier test asserting a single row and identical returned ids.
- **Persist-before-route.** Messages are committed before delivery is attempted. An offline peer silently drops frames (no delivery queue — accepted limitation), and history remains complete. Replay is newest-first with offset/limit via `GET /bookings/{id}/messages`.
- **Failure handling.** A failed `send` forces disconnect of the dead socket and notifies the survivor with a presence frame; `close()` failures are swallowed (socket was already dead). Covered by unit tests using fake sockets with induced send/close failures.
- **Access control.** Handshake requires a valid token plus participant-of-active-booking verification; rejected handshakes use distinct close codes (1007 auth vs 1008 policy). History endpoint enforces the same rules.

## Identity

Stateful DB-backed tokens rather than JWT/OAuth2: login rotates a single 32-byte random token per user (old token dies instantly — immediate revocation for free), expiry is 30 minutes from last issuance. Chosen deliberately to keep the chat-phase identity problem small; the OAuth2 migration proposal was evaluated and closed as unjustified scope for current needs.

## Configuration & infrastructure

- **Config**: pydantic-settings `Config` accepts either a `POSTGRES_*` triple (container/compose style) or `DATABASE_*` set (managed-Postgres style), validated together into one URL — same image deploys against compose or Supabase/Neon without changes. Feature flags like `WRITE_LOG_TO_TERMINAL` (stdout mirror alongside file logging, required for container log sinks) follow the same env-driven pattern.
- **Packaging**: PEP 735 dependency-groups split runtime deps (8 packages, all directly imported) from dev tooling (pytest, pytest-asyncio, httpx2, locust); Docker builds sync with `--no-dev`. Dead dependencies removed aggressively — including migrating tests to `httpx2` (the Pydantic-maintained httpx continuation) ahead of the ecosystem deprecation curve.
- **Docker**: intentionally single-stage — every dependency ships prebuilt manylinux wheels for linux/py3.14, so compile-oriented multi-stage patterns solve nothing today. Digest-pinned base images and Postgres version; `uv sync --frozen` makes builds reproducible from the lockfile alone. A two-stage venv-carry variant is queued for production hardening if/when a dependency ever needs compilation.
- **Logging**: namespaced file logs per environment directory; terminal mirroring opt-in via config flag.

## Testing strategy

65 tests, structured around risk:

- CRUD/lifecycle tests run inside per-test transactions rolled back after each test, with the app's `get_db` dependency overridden to share the session — fast, fully isolated.
- **Concurrency tests deliberately bypass isolation**: they clear the dependency override, fire real parallel requests through `ASGITransport` against the real engine/pool, and assert on committed database state — because the entire point is behavior across independent sessions.
- Race-condition tests use thread barriers (chat rooms) and asyncio gathers (bookings).
- WebSocket manager tested headlessly with fake sockets, including forced-failure paths.

## Known limitations (accepted, tracked)

- **Single-replica assumption**: the in-memory `WebsocketRegistry` and manager-per-room state mean horizontal scaling needs Redis pub/sub or sticky sessions before Phase 6.
- **No offline delivery queue**: messages sent while a peer is disconnected are persisted but not pushed later.
- **Blocking DB calls inside async WS handler**: chat endpoints perform synchronous SQLAlchemy work on the event loop; fine at two-party scale, worth revisiting if fan-out grows.
- **Tokens travel in query strings** for WS handshake/history (log hygiene handled by never logging token material).
- **No migrations tooling yet** (see data model section).
