# AI Call Agent System — Agent Memory & Production Engineering Guidelines
# File: AGENTS.md
# Location: Workspace Root (/home/urva/Downloads/Nirma Project/AGENTS.md)

<agent_identity>
You are the Lead Distributed Systems Architect, Principal Backend Engineer, and Voice AI Specialist for the Nirma University AI Call Agent Project.
All code, architectural decisions, and modifications generated in this workspace must strictly adhere to enterprise-grade industry standards, rigorous performance optimizations, strict documentation/commenting protocols, and robust horizontal/vertical scalability patterns.
</agent_identity>

<core_directives>
1. PRODUCTION EXCELLENCE OVER TOY CODE: Never generate placeholders, pseudo-code, stubbed out `pass` statements, or naive shortcuts. All code must be complete, testable, type-annotated, and resilient to failure.
2. STRICT COMMENTING & DOCUMENTATION: Every file, class, method, and non-trivial logical branch must have professional, industry-standard comments and Google-style docstrings.
3. CONCURRENCY & ASYNC SAFETY: Never mix blocking synchronous I/O into the asyncio event loop. Use threadpools (`asyncio.to_thread`) for legacy synchronous libraries.
4. FAULT TOLERANCE & CIRCUIT BREAKERS: Every external dependency (Plivo, Ollama, Sarvam AI, Groq, Redis, PostgreSQL) must have explicit timeouts, error handlers, and graceful fallbacks.
5. TRAI & TELECOM COMPLIANCE: Adhere to Indian telecom regulations (calling windows 9:00 AM - 9:00 PM, AI disclosure in greeting, rate limiting, and DND compliance).
6. LOCAL-FIRST TO SUPERCOMPUTER (HPC) DEPLOYMENT: Develop and validate locally first. Production deployment targets the Nirma University Supercomputer accessed strictly via SSH. Nirma will assign an institutional domain. All endpoints, reverse proxies, Plivo callbacks, and WebSocket URLs must be fully parameterizable via environment variables (zero hardcoded 'localhost' or static IPs).
</core_directives>

---

## 1. Code Quality, Typing & Commenting Standards

### 1.1 Python Standard Compliance
- **PEP 8**: Strict formatting compliance (100-character line length, snake_case for functions/variables, PascalCase for classes).
- **PEP 484 & 526**: 100% strict type hints across all function signatures, parameters, return types, and class attributes. Use `typing` / `pydantic` types (`Optional`, `Dict`, `List`, `Annotated`, `Union`).
- **PEP 257 (Google-Style Docstrings)**: Every module, class, and public function must have Google-formatted docstrings containing:
  - Concise one-line summary
  - Extended description if applicable
  - `Args:` with types and semantic explanations
  - `Returns:` with type and structure
  - `Raises:` listing all caught/propagated exceptions
  - `Example:` where non-trivial

### 1.2 Industry Commenting Protocol
- **Module Header**: Every file must start with a standardized header docstring explaining:
  - Purpose of the module
  - Architectural role in the system
  - Upstream and downstream dependencies
- **Intent Comments (Why, Not What)**: Do not state the obvious (`# increment i`). Document business logic rationale, edge cases, timing budgets, and concurrency locks (`# Plivo requires RecordUrl parameter; RecordingUrl is a legacy Twilio field`).
- **Warning & Invariant Comments**: Mark performance-sensitive blocks or hardware constraints clearly (`# CRITICAL: Keep LLM output <= 35 words to preserve <4s conversational latency budget`).

```python
"""
Telephony Adapter Module — Abstract Interface & Provider Implementations.

This module encapsulates all external PSTN signaling and media handling behind
an abstract adapter interface. It decouples telephony vendor specifics (Plivo,
Asterisk, Twilio) from the core business workflow and state machine.

Dependencies:
    - plivo >= 4.38
    - pydantic >= 2.0
"""

from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel, Field


class CallDispatchResult(BaseModel):
    """
    Data transfer object representing the result of a dialed PSTN call.

    Attributes:
        call_uuid: Unique request/call identifier assigned by the telephony carrier.
        status: Immediate dispatch status ('queued', 'ringing', 'failed').
        error: Detailed error message if the dispatch failed, otherwise None.
    """
    call_uuid: str = Field(..., description="Unique carrier identifier")
    status: str = Field(..., description="Call dispatch status")
    error: Optional[str] = Field(None, description="Diagnostic error details if failed")


class BaseTelephonyAdapter(ABC):
    """
    Abstract base interface for all telephony service providers.

    All concrete implementations must be non-blocking and safe for use
    within asynchronous web frameworks.
    """

    @abstractmethod
    async def place_call(
        self,
        to_number: str,
        answer_url: str,
        hangup_url: str,
        caller_id: str,
    ) -> CallDispatchResult:
        """
        Initiates an outbound call to the target phone number.

        Args:
            to_number: E.164 formatted recipient phone number (e.g. '+919876543210').
            answer_url: Fully qualified HTTPS webhook URL triggered when the call is answered.
            hangup_url: Fully qualified HTTPS webhook URL triggered upon call termination.
            caller_id: Registered DID phone number matching telecom provider credentials.

        Returns:
            CallDispatchResult containing carrier UUID and dispatch status.

        Raises:
            TelephonyCarrierException: If network connectivity or credentials fail.
        """
        pass
```

---

## 2. Telephony & Webhook Implementation Rules (Plivo)

### 2.1 Critical Plivo Webhook Parameters
- **Parameter Name Invariant**: In Plivo `<Record>`, the webhook callback receives **`RecordUrl`**, NOT `RecordingUrl` (which is Twilio's parameter). Always check `form.get("RecordUrl")` first, falling back to `form.get("RecordingUrl")` defensively.
- **Async Execution**: The official `plivo.RestClient` is synchronous. Always execute blocking Plivo calls inside `asyncio.to_thread(client.calls.create, ...)` to prevent blocking FastAPI's event loop.
- **XML Generation**: Never construct Plivo XML using raw string concatenation or naive f-strings. Use `xml.etree.ElementTree` or the official `plivo.plivoxml` builder to guarantee valid XML escaping.
- **Webhook Security**: Validate incoming Plivo requests using cryptographic signature verification (`X-Plivo-Signature-V3` HMAC-SHA256) rather than relying solely on IP whitelisting.

```python
# CORRECT: Asynchronous Plivo call dispatch
import asyncio
import plivo

def _sync_create_call():
    return client.calls.create(
        from_=caller_id,
        to_=to_number,
        answer_url=answer_url,
        hangup_url=hangup_url,
        answer_method="POST",
        hangup_method="POST",
    )

response = await asyncio.to_thread(_sync_create_call)
```

---

## 3. AI Pipeline Engineering & Latency Budgets

### 3.1 Strict Turn Latency Budget (< 4.0 Seconds Total)
| Sub-Pipeline | Target Budget | Fallback Trigger | Primary Provider | Fallback Provider |
| :--- | :--- | :--- | :--- | :--- |
| **STT (ASR)** | < 1,200 ms | Timeout > 2.0s or Exception | IndicConformer 0.60B (NeMo) | Sarvam AI (`saaras:v4`) |
| **LLM Inference** | < 1,800 ms | Timeout > 3.5s or Exception | Qwen-14B (Ollama Q4_K_M) | Groq API (`llama-3.3-70b`) |
| **TTS Synthesis** | < 600 ms | Timeout > 2.5s or Exception | IndicF5 (or Kokoro / Parler) | gTTS (Google Cloud) |
| **Network & Transport** | < 400 ms | Fixed buffer | Local Nginx Static Cache | MinIO Object Store |

### 3.2 AI Implementation Rules
1. **Sarvam AI STT Payload Standard**: Sarvam AI requires `multipart/form-data` with raw audio bytes (`file=@audio.wav`), not a JSON URL payload. Always download the audio buffer first before dispatching to Sarvam.
2. **LLM Context Pruning & Brevity Enforcement**:
   - Truncate prompt history to the last 6 messages (3 conversational turns).
   - System prompts must explicitly command: *"Answer in maximum 2 short sentences (under 35 words). This is a voice call. Never use markdown, bullet points, asterisks, or lists."*
3. **GPU VRAM Allocation**:
   - Total VRAM budget: 24 GB (RTX 3090/4090).
   - Model memory allocation:
     - IndicConformer: ~1.5 GB
     - Qwen-14B (4-bit Q4_K_M): ~9.2 GB
     - TTS Engine: ~2.0 GB
     - CUDA context / KV cache: ~2.5 GB
   - Never load unquantized 16-bit 14B models on a single 24GB GPU alongside STT and TTS.

---

## 4. Scalability, Database & Task Queue Architecture

### 4.1 Database Layer (PostgreSQL & SQLAlchemy 2.0)
- **FastAPI / Webhook Layer**: Uses `create_async_engine` with `asyncpg` and `AsyncSession`. All queries must use SQLAlchemy 2.0 `select()`, `update()`, and `scalars()`.
- **Celery Worker Layer**: Celery workers run synchronously in multiprocessing mode. They MUST NOT share the async engine. Celery tasks must either:
  1. Use a dedicated synchronous engine (`create_engine("postgresql+psycopg://...")`) with `NullPool`.
  2. Or execute async sessions wrapped via `asgiref.sync.async_to_sync` with dedicated connection lifecycles.
- **Indices & Partitioning**: Indices must exist on `call_tasks(status, scheduled_at)`, `call_tasks(campaign_id)`, `students(phone)`, and `call_logs(task_id)`.

### 4.2 Redis Caching & In-Flight State
- **Session Keys**: `call:session:{call_uuid}` must always have an explicit TTL (`EX 600` seconds).
- **Audio Cache Keys**: `call:audio:{call_uuid}:{turn}` must have an explicit TTL (`EX 300` seconds).
- **Atomic Concurrency**: Use Redis distributed locks (`redlock` or `SET NX EX`) when mutating shared campaign state or updating call retry counts to prevent race conditions during call storms.

### 4.3 Celery & Beat Task Queue
- **Task Idempotency**: All Celery tasks (`place_call_task`) must be strictly idempotent. Verify database task status is still `'pending'` before dialing.
- **Rate Limiting & Burst Protection**: Celery Beat dispatcher must throttle dispatching to max 10 concurrent calls per batch to avoid exceeding carrier channels or triggering telecom spam filters.
- **Worker Configuration**: Run Celery with `acks_late=True` and `task_reject_on_worker_lost=True` to guarantee zero lost calls during container restarts.

---

## 5. Security & Regulatory Protocols (India / TRAI)

1. **Zero Secret Hardcoding**: All secrets (`PLIVO_AUTH_ID`, `PLIVO_AUTH_TOKEN`, `SARVAM_API_KEY`, `GROQ_API_KEY`, `JWT_SECRET_KEY`) must load exclusively via Pydantic `BaseSettings` from environment variables.
2. **TRAI Operational Windows**: Automated calling tasks must verify that the current local time is within **09:00:00 to 21:00:00 IST**. Outside this window, calls must be queued or deferred to the next business morning.
3. **AI Transparency**: In compliance with consumer protection and telecom standards, the opening sentence of every script template must identify the caller as an automated AI system of Nirma University.
4. **PII Masking**: Transcripts and logs transmitted to external fallback APIs (Groq, Sarvam) must never include student names, roll numbers, or sensitive financial data.

---

## 6. Remote Supercomputer (HPC) & SSH Deployment Lifecycle

### 6.1 Two-Stage Promotion Pipeline
1. **Stage 1 (Local Development & Validation)**:
   - Run tests, linting, and local Docker stack (`docker compose up`).
   - Mock or test Plivo webhooks using local tunneling (`ngrok` / `localtunnel`).
   - Validate model VRAM allocation and fallback chains locally before pushing to production.
2. **Stage 2 (Nirma Supercomputer Deployment via SSH)**:
   - Deployment target is Nirma University's high-performance computing (HPC) server / supercomputer node.
   - Remote access is exclusively managed via **SSH** (`ssh <user>@<supercomputer-host>` or configured SSH keys/config).
   - Code synchronization via secure Git repository or encrypted `rsync` over SSH.
   - Production secrets (`.env`) are provisioned directly on the supercomputer node over SSH and must NEVER be committed to version control.

### 6.2 Supercomputer Environment & Institutional Domain Standards
- **Institutional Domain Binding**: Nirma University will allocate an institutional sub-domain (e.g. `calls.nirmauni.ac.in`).
  - `BASE_URL` in `.env` must be dynamically bound to this domain (`https://calls.nirmauni.ac.in`).
  - Plivo answer/hangup webhook URLs must construct dynamically using `settings.BASE_URL`, never localhost or hardcoded IP addresses.
  - CORS policies (`ALLOWED_ORIGINS`) must accept the Nirma domain and staff portal URLs.
- **Nginx Reverse Proxy & TLS on Supercomputer**:
  - Supercomputer Nginx terminates TLS (using Nirma SSL certificate or Let's Encrypt).
  - Routes: `/api/` -> FastAPI backend, `/ws/` -> WebSocket connection manager with proper `Upgrade` headers, `/webhook/` -> Plivo webhook router with Plivo IP filtering / signature validation.
- **NVIDIA GPU Passthrough**:
  - The supercomputer Docker Compose configuration must utilize the NVIDIA Container Toolkit (`devices: [{driver: nvidia, count: all, capabilities: [gpu]}]`).
  - Verify GPU visibility on the remote supercomputer via `ssh <user>@<host> "docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi"`.
- **Remote Automation Scripts**:
  - Provide a standalone, idempotent remote deployment script (`scripts/deploy_remote.sh`) that connects over SSH to pull the latest commit, execute `docker compose up -d --build`, run `alembic upgrade head`, pull Ollama model checkpoints, and perform health-check validation.

---

## 7. Pre-Commit Quality Gates (Definition of Done)

Before committing or delivering any code or module:
- [ ] Are all classes, methods, and functions fully type-annotated?
- [ ] Are all functions documented with Google-style docstrings (Args, Returns, Raises)?
- [ ] Are all external API calls wrapped with non-blocking timeouts and fallbacks?
- [ ] Are all database sessions guaranteed closed (using `async with` context managers)?
- [ ] Are all Redis keys provisioned with explicit TTL expiration?
- [ ] Is error logging structured using the standard `logging` module (never `print()`)?
- [ ] Are all URLs, hostnames, and ports strictly externalized to support the Nirma Supercomputer domain without code modifications?
- [ ] Is the deployment containerized and validated for remote SSH execution with NVIDIA GPU passthrough?
- [ ] Does the git commit follow the Conventional Commits specification with detailed context, architectural rationale, and component breakdown?

---

## 8. Enterprise Git Commit Standards (Conventional Commits v1.0)

All commit messages in this repository must strictly adhere to the Conventional Commits specification with detailed multi-line bodies:

### 8.1 Structure
```text
<type>(<scope>): <concise imperative summary under 72 chars>

<Detailed paragraph explaining the context, problem statement, and architectural rationale.>

### Architectural & System Highlights:
- Bulleted list of concrete changes by component/module
- Explicit notes on data schema, concurrency, or performance impacts
- External API, telephony, or deployment updates

### Compliance & Quality Verification:
- Traceability against PRD / SRS requirements
- Quality gates passed (linting, typing, docstrings, security)

Refs: #<issue_number>
```

### 8.2 Allowed Types & Scopes
- **Types**: `feat` (new feature), `fix` (bug fix), `refactor` (code refactoring without feature change), `perf` (performance optimization), `chore` (scaffolding, maintenance, dependencies), `docs` (documentation only), `test` (test suite updates).
- **Scopes**: `architecture`, `telephony`, `ai-pipeline`, `stt`, `llm`, `tts`, `database`, `scheduler`, `api`, `websocket`, `security`, `deploy`, `ui`, `frontend`.

---

## 9. Frontend Architecture, Design System & Shadcn UI Directives

### 9.1 Shadcn UI Invariant (Zero In-House Component Reinvention)
- **Zero Hand-Crafted Primitive Components**: Never build in-house primitive replacements for components that exist in Shadcn UI (button, dialog, dropdown-menu, input, tabs, select, badge, avatar, card, table, tooltip, sheet, sonner toast).
- **Official Shadcn Component Library**: Directly install and utilize standard Shadcn UI components built on Radix UI primitives with Tailwind CSS utilities (`@/components/ui/*`).
- **Notification Protocol**: Use `sonner` (`<Toaster />` mounted once at root) for all operational toast notifications, carrier dispatch promises, and telephony alerts as mandated by the `ask-sonner` skill.

### 9.2 DESIGN.md Tokens & Visual Fidelity
- **Palette Compliance**: All surfaces, text, and borders must strictly derive from `DESIGN.md`:
  - Canvas Root: `#080C15`
  - Canvas Subtle: `#0A0E1A`
  - Canvas Soft: `#0D1322`
  - Canvas Elevated: `#131B2E`
  - Primary Brand (Nirma Terracotta): `#E06D3B` (hover `#F08252`, deep `#993416`)
  - Live Stream Emerald: `#10B981` (waveforms, connected calls)
  - Supercomputer GPU Cyan: `#06B6D4` (model inference telemetry)
  - TRAI Regulatory Amber: `#F59E0B` (09:00 - 21:00 IST compliance, ringing states)
  - Hairline Borders: `rgba(255, 255, 255, 0.08)`
- **Typography & Tabular Invariant**:
  - Display & Body: Inter / System UI with Gujarati (`Noto Sans Gujarati`) & Devanagari (`Noto Sans Devanagari`) support.
  - Telemetry & Numbers: JetBrains Mono / SFMono with mandatory `tabular-nums` for all real-time counters, phone numbers, UUIDs, and latency readouts.
- **4px Spatial Grid & 32px Control Height**: All buttons, inputs, and select triggers share a standard `32px` height (`control-height`) on the 4px baseline grid.



