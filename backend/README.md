# Nirma University AI Voice Agent — Backend Architecture & Service Engine

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Celery](https://img.shields.io/badge/Celery-5.4-37814A?logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![Redis](https://img.shields.io/badge/Redis-7.0-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Plivo](https://img.shields.io/badge/Plivo-Telephony_PSTN-00B0FF?logo=twilio&logoColor=white)](https://www.plivo.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](../LICENSE)

The **Nirma University AI Voice Agent Backend** is a distributed, high-concurrency voice telephony engine engineered to automate outbound phone calls (tuition fee reminders, examination schedules, attendance alerts) across **Hindi, Gujarati, and English**. It is built for local-first execution and scales to high-performance computing (HPC) nodes on the **Nirma University Supercomputer** accessed via SSH.

---

## Table of Contents

- [Architectural Overview](#architectural-overview)
- [Subsystem Breakdown](#subsystem-breakdown)
  - [1. AI Pipeline & Latency Engine (`backend/ai_pipeline/`)](#1-ai-pipeline--latency-engine-backendai_pipeline)
  - [2. Telephony Carrier Adapter & Webhooks (`backend/telephony/`)](#2-telephony-carrier-adapter--webhooks-backendtelephony)
  - [3. Celery Task Queue & Campaign Scheduler (`backend/scheduler/`)](#3-celery-task-queue--campaign-scheduler-backendscheduler)
  - [4. Database ORM & Migrations (`backend/database/`)](#4-database-orm--migrations-backenddatabase)
  - [5. Staff REST API & RBAC (`backend/api/`)](#5-staff-rest-api--rbac-backendapi)
  - [6. Real-Time WebSocket Telemetry (`backend/websocket/`)](#6-real-time-websocket-telemetry-backendwebsocket)
- [Strict Turn Latency Budget (< 4.0s)](#strict-turn-latency-budget--40s)
- [Dual-Engine Database Isolation Invariant](#dual-engine-database-isolation-invariant)
- [Indian Telecom Compliance (TRAI)](#indian-telecom-compliance-trai)
- [Environment Configuration (.env)](#environment-configuration-env)
- [Local Development Setup](#local-development-setup)
- [Supercomputer (HPC) Deployment Lifecycle](#supercomputer-hpc-deployment-lifecycle)

---

## Architectural Overview

The backend employs an asynchronous micro-monolith architecture separating real-time carrier signaling from background batch scheduling:

```mermaid
graph TD
    PSTN["Indian PSTN Telecom Network"] <--> |SIP / E.164 Voice| Plivo["Plivo Telephony Gateway"]
    Plivo <--> |HTTPS Answer / Hangup Webhooks| Webhooks["FastAPI Webhook Router (/webhook/plivo)"]
    
    subgraph "FastAPI ASGI Engine (Asyncio Event Loop)"
      Webhooks --> Pipeline["AI Pipeline Engine"]
      REST["Staff REST API (/api/v1/*)"] --> AsyncDB[("PostgreSQL (asyncpg Pool)")]
      WS["WebSocket Manager (/ws/calls)"] --> Clients["Frontend Dashboard"]
    end
    
    subgraph "AI Inference Pipeline"
      Pipeline --> ASR["STT: IndicConformer (Fallback: Sarvam AI)"]
      Pipeline --> LLM["LLM: Qwen-14B Ollama (Fallback: Groq 70B)"]
      Pipeline --> TTS["TTS: IndicF5 (Fallback: gTTS)"]
    end

    subgraph "Asynchronous Distributed Scheduler"
      Beat["Celery Beat (Periodic Dispatcher)"] --> RedisQ[("Redis 7 Task Broker")]
      RedisQ --> Worker["Celery Multiprocessing Worker"]
      Worker --> SyncDB[("PostgreSQL (Psycopg NullPool)")]
      Worker --> PlivoClient["Plivo SDK (Direct Sync / place_call_sync)"]
    end
```

---

## Subsystem Breakdown

### 1. AI Pipeline & Latency Engine (`backend/ai_pipeline/`)
Encapsulates all speech-to-text, reasoning, and speech-synthesis logic behind abstract fallback interfaces:

* **Speech-to-Text (`stt.py`)**:
  * **Primary**: `IndicConformerSTT` (NeMo 0.60B running locally on GPU, target budget `<1,200 ms`).
  * **Fallback**: `SarvamSTT` using model `saaras:v4` triggered on timeout (`>2.0s`) or local model exception. Sends raw audio bytes via `multipart/form-data`.
* **Language Model Inference (`llm.py`)**:
  * **Primary**: `OllamaLLM` serving quantized `Qwen-14B` (Q4_K_M, target budget `<1,800 ms`).
  * **Context Pruning**: Context is strictly constrained to the last 6 conversational turns (3 exchanges).
  * **Brevity Invariant**: System prompt forces replies strictly under 35 words and 2 sentences without markdown.
  * **Fallback**: `GroqLLM` utilizing `llama-3.3-70b` triggered on timeout (`>3.5s`).
* **Text-to-Speech Synthesis (`tts.py`)**:
  * **Primary**: `IndicF5TTS` local neural speech synthesis generating high-fidelity WAV audio (target `<600 ms`).
  * **Fallback**: `GoogleTTS` (gTTS) wrapped in `asyncio.to_thread` for non-blocking execution.
  * **Audio Caching**: Synthesized audio files cached with explicit TTL in `/tmp/audio_cache/`.
* **Pipeline Orchestrator (`pipeline.py`)**:
  * Cascades STT → LLM → TTS sequentially while tracking per-stage and total turn turnaround latency.

### 2. Telephony Carrier Adapter & Webhooks (`backend/telephony/`)
* **Telephony Adapter (`plivo_adapter.py`)**:
  * **Direct Synchronous Dispatch (`place_call_sync`)**: Celery background tasks run in dedicated multiprocessing worker processes. Plivo's official SDK client is invoked directly and synchronously (`place_call_sync`), eliminating unnecessary `asyncio.run()` event loop instantiation and event loop thrashing during mass outbound dialing.
  * **Non-Blocking Asynchronous Dispatch (`place_call`)**: For callers operating within FastAPI's asynchronous event loop, SDK calls are wrapped in `asyncio.to_thread` to maintain event-loop responsiveness.
* **Webhook Handler (`webhook_handler.py`)**:
  * **Plivo Parameter Invariant**: Webhook callback inspects `form.get("RecordUrl")` (PascalCase), with defensive fallback to `RecordingUrl`.
  * **XML Generation**: Constructs valid Plivo XML using `xml.etree.ElementTree` with `<Record>`, `<Play>`, and `<Wait>` elements.
  * Downloads recipient audio recording into memory, runs AI turn pipeline, saves synthesized TTS response, and returns Plivo XML to play back speech.

### 3. Celery Task Queue & Campaign Scheduler (`backend/scheduler/`)
* **Celery App (`celery_app.py`)**:
  * Redis-backed broker (`redis://redis:6379/0`) and result backend (`redis://redis:6379/1`).
  * Configured with `acks_late=True` and `task_reject_on_worker_lost=True` for zero lost calls during container restarts.
* **Dispatcher Task (`tasks.py`)**:
  * `place_call_task`: Strictly idempotent execution verifying task state is `pending` before dialing.
* **Campaign Runner (`campaign_runner.py`)**:
  * Filters students matching department/semester criteria.
  * Enforces **TRAI Operational Windows (09:00 - 21:00 IST)**. Calls outside this window are automatically deferred.
  * Enforces rate limiting (max 10 concurrent calls) to prevent carrier channel saturation.

### 4. Database ORM & Migrations (`backend/database/`)
* **SQLAlchemy 2.0 Models (`models.py`)**:
  * `StaffUser`: Portal administrators with bcrypt password hashing.
  * `Student`: Recipient profiles with E.164 phone numbers and preferred language (`hi`, `gu`, `en`).
  * `CallScript`: System prompts and opening AI disclosures.
  * `CallCampaign`: Outbound campaign schedule and retry policies.
  * `CallTask`: Individual call task states (`pending`, `ringing`, `in_progress`, `completed`, `failed`).
  * `CallLog`: Granular JSONB conversation transcripts and latency logs.
* **Database Session Layer (`session.py`)**:
  * Implements strict **Dual-Engine Isolation** (see section below).
* **Migrations (`migrations/`)**:
  * Asynchronous Alembic configuration (`001_initial_schema.py`) and seed script (`seeds.py`).

### 5. Staff REST API & RBAC (`backend/api/`)
* **`auth.py`**: OAuth2 Password Bearer flow, bcrypt password hashing, and signed JWT access/refresh token issuing.
* **`campaigns.py`**: Administrative endpoints to create, schedule, filter, monitor, and cancel campaigns.
* **`calls.py`**: Detailed task inspection, transcript viewer, and manual retry triggers.
* **`analytics.py`**: KPI calculations (connection rate, daily call volume time-series, disposition breakdown, and latency percentiles).

### 6. Real-Time WebSocket Telemetry (`backend/websocket/`)
* **`manager.py`**:
  * Thread-safe in-memory `ConnectionManager` broadcasting structured JSON events (`call_status`, `transcript_turn`, `call_alert`).
  * `/ws/calls` endpoint with query parameter JWT authentication (`?token=...`).

---

## Strict Turn Latency Budget (< 4.0s)

To maintain realistic voice conversation flow over PSTN networks, turn turnaround time is constrained:

```mermaid
flowchart TD
    AudioIn["Recipient Audio Buffer (WAV)"] --> STTNode{"STT Inference<br/>IndicConformer (Local GPU)"}
    STTNode -->|"Success (< 1,200ms)"| LLMNode{"LLM Reasoning<br/>Qwen-14B (Ollama)"}
    STTNode -->|"Timeout (> 2.0s) / Fail"| STTFallback["Fallback: Sarvam AI<br/>saaras:v4 (Cloud)"]
    STTFallback --> LLMNode

    LLMNode -->|"Success (< 1,800ms)"| TTSNode{"TTS Synthesis<br/>IndicF5 (Local GPU)"}
    LLMNode -->|"Timeout (> 3.5s) / Fail"| LLMFallback["Fallback: Groq API<br/>llama-3.3-70b (Cloud)"]
    LLMFallback --> TTSNode

    TTSNode -->|"Success (< 600ms)"| AudioOut["Synthesized Voice Output (< 4.0s total)"]
    TTSNode -->|"Timeout (> 2.5s) / Fail"| TTSFallback["Fallback: Google TTS<br/>gTTS (Cloud)"]
    TTSFallback --> AudioOut
```

| Pipeline Stage | Target Budget | Fallback Trigger | Primary Engine | Fallback Engine |
| :--- | :--- | :--- | :--- | :--- |
| **STT (Speech-to-Text)** | `< 1,200 ms` | Timeout `> 2.0s` or Exception | IndicConformer 0.60B (GPU) | Sarvam AI (`saaras:v4`) |
| **LLM (Reasoning)** | `< 1,800 ms` | Timeout `> 3.5s` or Exception | Qwen-14B (Ollama Q4_K_M) | Groq (`llama-3.3-70b`) |
| **TTS (Speech Synthesis)**| `< 600 ms` | Timeout `> 2.5s` or Exception | IndicF5 (Local GPU) | gTTS (Cloud via threadpool)|
| **Network Buffer** | `< 400 ms` | Fixed allowance | Local Nginx Cache | S3 / MinIO Archive |
| **Total Turnaround** | **`< 4,000 ms`** | Overall Turn Alert | Local HPC Stack | Cloud Provider Chain |

---

## Dual-Engine Database Isolation Invariant

FastAPI and Celery workers operate under separate concurrency lifecycles:

```mermaid
graph TD
    subgraph WebhookLayer["FastAPI Async Engine (Asyncio Event Loop)"]
        AsyncRoute["Webhook & REST Handlers"] --> AsyncEngine["create_async_engine('postgresql+asyncpg://...')"]
        AsyncEngine --> AsyncSessionPool["AsyncSession Connection Pool<br/>(pool_size=20, max_overflow=10)"]
    end

    subgraph CeleryLayer["Celery Worker Layer (Multiprocessing Fork)"]
        Task["Celery Idempotent Worker Tasks"] --> SyncEngine["create_engine('postgresql+psycopg://...')"]
        SyncEngine --> NullPool["NullPool (Zero Shared Socket Corruption)"]
    end

    AsyncSessionPool --> PostgresDB[("PostgreSQL 15 Database Server")]
    NullPool --> PostgresDB
```

1. **FastAPI Webhook & REST Layer**:
   * Uses `create_async_engine` with `asyncpg` driver.
   * Session: `AsyncSession` with connection pooling (`pool_size=20`, `max_overflow=10`).
2. **Celery Worker Layer**:
   * Celery runs synchronously in multiprocessing mode. Multiprocessing forks corrupt asyncpg event loop sockets.
   * Celery tasks **must exclusively use `get_sync_session()`** (`create_engine("postgresql+psycopg://...")`) with `NullPool` to guarantee dedicated per-task connection lifecycles.

---

## Indian Telecom Compliance (TRAI)

1. **Permitted Calling Hours**: Outbound automated campaigns execute strictly within **09:00:00 to 21:00:00 IST**. Tasks scheduled outside this window remain in `pending` state until 09:00 AM IST next morning.
2. **Mandatory AI Disclosure**: Every script template's opening spoken utterance identifies the caller as an automated AI system of Nirma University.
3. **PII Masking**: Cloud fallback providers (Sarvam, Groq) receive transcripts with student names and financial identifiers stripped.

---

## Environment Configuration (.env)

Configuration is managed via Pydantic `BaseSettings` in `backend/config.py`:

```bash
# Core Runtime
APP_NAME="Nirma AI Call Agent"
APP_ENV=development                       # 'development' | 'production'
DEBUG=false
LOG_LEVEL=INFO

# Institutional Domain & Networking (Nirma HPC)
BASE_URL=https://calls.nirmauni.ac.in
PORT=8000
ALLOWED_ORIGINS=http://localhost:3000,https://calls.nirmauni.ac.in

# Database Configuration (PostgreSQL 15)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_calls
SYNC_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/ai_calls

# Cache & Message Broker (Redis 7)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Telephony Carrier (Plivo)
PLIVO_AUTH_ID=your_plivo_auth_id
PLIVO_AUTH_TOKEN=your_plivo_auth_token
PLIVO_CALLER_ID=+917971600000

# AI Pipeline Engines
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen:14b
SARVAM_API_KEY=your_sarvam_api_key
GROQ_API_KEY=your_groq_api_key

# Security & JWT
JWT_SECRET_KEY=generate_secure_random_64_character_hex_string
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

---

## Local Development Setup

### 1. Prerequisites
- Python 3.11+
- PostgreSQL 15 & Redis 7 running locally or via Docker
- `ffmpeg` and `libsndfile1` installed:
  ```bash
  sudo apt-get update && sudo apt-get install -y ffmpeg libsndfile1
  ```

### 2. Environment & Dependencies
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Database Migrations & Seeds
```bash
# Run Alembic migrations
alembic upgrade head

# Seed admin account and call templates
python -m backend.seeds
```

### 4. Run Services
```bash
# Terminal 1: FastAPI ASGI server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Celery Worker
celery -A backend.scheduler.celery_app worker --loglevel=info --concurrency=4

# Terminal 3: Celery Beat Periodic Scheduler
celery -A backend.scheduler.celery_app beat --loglevel=info
```

---

## Supercomputer (HPC) Deployment Lifecycle

Production deployment targets Nirma University's high-performance computing node via SSH:

```mermaid
flowchart TD
    Start(["Remote SSH Session"]) --> SSH["ssh user@supercomputer.nirmauni.ac.in"]
    SSH --> Step1["1. Verify Production .env Secrets"]
    Step1 --> Step2["2. Check NVIDIA GPU via nvidia-smi"]
    Step2 --> Step3["3. Git Pull origin/main"]
    Step3 --> Step4["4. Build Multi-Stage Docker Images"]
    Step4 --> Step5["5. Launch Containers with GPU Passthrough"]
    Step5 --> Step6["6. Execute Alembic Schema Migrations"]
    Step6 --> Step7["7. Pull Quantized Weights (qwen:14b)"]
    Step7 --> Step8["8. Validate Health (curl /health)"]
    Step8 --> Ready(["Production System Live"])
```

### 1. Remote SSH Execution
```bash
ssh user@supercomputer.nirmauni.ac.in
cd /opt/nirma-ai-call-agent
bash scripts/deploy_supercomputer.sh
```

### 2. What `deploy_supercomputer.sh` Automates
1. Verifies production `.env` presence.
2. Audits NVIDIA GPU hardware access via `nvidia-smi`.
3. Synchronizes latest commit from Git (`git pull origin main`).
4. Builds multi-stage Docker images (`docker compose build`).
5. Launches containers with NVIDIA Container Toolkit passthrough (`docker compose up -d`).
6. Executes Alembic schema migrations and loads seed data.
7. Pulls local quantized LLM weights into the Ollama container (`qwen:14b`).
8. Validates endpoint health via `curl -f http://localhost:8000/health`.
