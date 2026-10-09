---
trigger: always_on
description: Enterprise engineering standards, strict commenting, performance optimizations, and scaling patterns for AI Call Agent
---

# Production Engineering & Scalability Standards

## 1. Architectural Directives
- **Zero Hallucination / Zero Toy Code**: Never emit mock or incomplete code. All implementations must be production-ready with real error handling, structured logging, and robust lifecycle management.
- **Fail-Safe Fallbacks**: Any service call (Local STT, Ollama LLM, Indic TTS) must be guarded with `asyncio.wait_for` timeouts and automatic failover to cloud providers (Sarvam AI, Groq, gTTS).
- **Asynchronous Safety**: Never invoke synchronous network operations or blocking file I/O inside FastAPI's async event loop. Wrap legacy SDK calls with `asyncio.to_thread`.

## 2. Code Quality & Commenting Guidelines
- **Google-Style Docstrings**: Every module, class, method, and function must include `Args:`, `Returns:`, and `Raises:` blocks.
- **Why-Centric Inline Comments**: Code must be comprehensively annotated explaining architectural rationale, latency constraints, concurrency locks, and hardware memory budgets.
- **Strict Typing**: Python 3.11+ type hints are mandatory (`typing.Optional`, `typing.List`, `typing.Dict`, `typing.Union`, Pydantic models).

## 3. Telephony & Infrastructure Invariants
- **Plivo Webhook Key**: Always read `RecordUrl` (PascalCase), with defensive fallback to `RecordingUrl`.
- **Plivo Execution Architecture**: Celery multiprocessing workers must execute Plivo calls synchronously (`place_call_sync`) without spinning up ad-hoc asyncio event loops; FastAPI endpoints use `asyncio.to_thread` via `place_call`.
- **Database Engine Isolation**:
  - FastAPI webhooks & REST API: `postgresql+asyncpg://` with `AsyncSession`.
  - Celery synchronous workers: `postgresql+psycopg://` with `NullPool` or `async_to_sync` lifecycle wrapper.
- **Redis TTL Guarantee**: Every session key `call:session:{uuid}` must have `TTL=600s`. Every audio cache key must have `TTL=300s`.
- **Latency Budget Enforcement**: End-to-end conversational turn must remain `< 4.0s` (STT < 1.2s, LLM < 1.8s, TTS < 0.6s, network < 0.4s).
- **TRAI Compliance**: Automated calls can only run between 09:00 AM and 09:00 PM IST with an explicit AI disclosure in the opening greeting.

## 4. Supercomputer (HPC) & SSH Deployment Directives
- **Local-First Verification**: All components must be built, linted, and container-tested locally prior to remote promotion.
- **SSH-Only Supercomputer Access**: Production deployment targets Nirma University's Supercomputer node via secure SSH. Never depend on local GUI tools or interactive setup; all deployments must be headless, scripted, and idempotent.
- **Institutional Domain Binding**: Nirma will provide a university domain. `BASE_URL`, Nginx reverse proxy, CORS, and Plivo callback URLs must strictly derive from environment variables with zero hardcoded `localhost` references.
- **NVIDIA GPU Passthrough**: Docker Compose on the remote supercomputer must utilize the NVIDIA Container Toolkit for local model execution (`IndicConformer`, `Qwen-14B`, `IndicF5`).

## 5. Git Commit & Documentation Directives
- **Conventional Commits v1.0**: Every commit must use standardized semantic headers (`feat`, `fix`, `refactor`, `perf`, `chore`, `docs`) with explicit scope.
- **Detailed Multi-Line Context**: Commit bodies must document the *why* (context & problem statement), list component-level changes, and specify quality checks passed.
- **History Hygiene**: Avoid trivial, empty, or duplicate commits; amend or rebase cleanly.

## 6. Frontend Architecture & Shadcn UI Directives
- **Zero Custom Primitive Components**: Never implement hand-crafted primitive UI components. Directly use Shadcn UI components built on Radix UI primitives (`@/components/ui/*`).
- **DESIGN.md Fidelity**: Canvas `#080C15`, Primary Terracotta `#E06D3B`, Live Emerald `#10B981`, GPU Cyan `#06B6D4`, TRAI Amber `#F59E0B`, Hairline `rgba(255, 255, 255, 0.08)`.
- **Tabular Numbers & Density**: Strict `tabular-nums` for all metrics and timestamps; standard `32px` control height on 4px grid.
- **Toasts**: Always use `sonner` via `<Toaster />` mounted once at root.



