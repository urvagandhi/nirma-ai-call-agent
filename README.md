# Nirma AI Call Agent System

An enterprise-grade, automated multilingual outbound voice calling platform designed for college administration (Nirma University). The system places outbound calls to students and parents for fee reminders, examination schedules, attendance alerts, and official announcements in **English, Hindi, and Gujarati**.

---

## 🏛️ System Overview

The system operates on an on-premises local-first architecture deployed to the **Nirma University Supercomputer (HPC)**, combining local speech recognition (ASR), local large language models (LLM), and speech synthesis (TTS) with resilient cloud failovers.

```
+-----------------------------------------------------------------------+
|                         Staff Web Dashboard                           |
|            (Call Monitoring, Campaign Management, Transcripts)        |
+-----------------------------------|-----------------------------------+
                                    | REST / WebSockets
+-----------------------------------v-----------------------------------+
|                        FastAPI Gateway Layer                          |
|         (JWT Auth, Rate Limiting, Plivo Webhook Orchestration)        |
+----------+------------------------+-------------------+---------------+
           |                        |                   |
+----------v---------+   +----------v---------+   +-----v---------------+
|  Telephony Module  |   |  Scheduler Module  |   | AI Pipeline Module  |
|  (Plivo Adapter &  |   |  (Celery + Beat +  |   | (STT -> LLM -> TTS  |
|   State Machine)   |   |   Redis Broker)    |   |  Cascade Engine)    |
+--------------------+   +--------------------+   +---------------------+
```

---

## 📁 Repository Structure

```text
.
├── .agents/                    # Agent memory & workspace rules
│   └── rules/
│       └── engineering_standards.md
├── backend/                    # Core backend service package
│   ├── ai_pipeline/            # STT, LLM, TTS model adapters & cloud fallbacks
│   ├── api/                    # REST API endpoints (auth, campaigns, calls, analytics)
│   ├── database/               # SQLAlchemy models & Alembic migrations
│   │   └── migrations/
│   ├── scheduler/              # Celery tasks & periodic campaign dispatcher
│   ├── telephony/              # Plivo telephony adapter & webhook state machine
│   └── websocket/              # Real-time WebSocket connection manager
├── docker/                     # Container orchestration & reverse proxy configs
│   └── nginx/                  # Nginx TLS & Plivo IP whitelisting
├── docs/                       # Official system documentation & specifications
│   ├── AI_Build_Prompt.pdf     # Master build prompt & module specifications
│   ├── PRD_AI_Call_Agent.pdf   # Product Requirements Document
│   ├── SRS_AI_Call_Agent.pdf   # Software Requirements Specification (IEEE 830)
│   └── System_Design_AI_Call_Agent.pdf # Complete system architecture & schema
├── scripts/                    # Deployment & maintenance automation scripts
├── .env.example                # Configuration & environment variable template
├── .gitignore                  # Production Git exclusions
├── AGENTS.md                   # Agent memory & engineering guidelines
├── LICENSE                     # Project license
├── README.md                   # Project overview & documentation index
└── SYSTEM_ARCHITECTURE_AND_OPTIMIZATIONS.md # Technical optimizations & benchmarks
```

---

## 🛠️ Technology Stack

| Layer | Component | Technology | Role |
| :--- | :--- | :--- | :--- |
| **API & Webhooks** | Web Framework | FastAPI (Python 3.11) | Async REST API & Plivo Webhooks |
| **Database** | Relational DB | PostgreSQL 15 | Persistent ACID state & transcripts |
| **Queue / Cache** | Task Broker | Redis 7 | Celery broker, session cache (`TTL=600s`) |
| **Task Queue** | Background Jobs | Celery 5.x + Celery Beat | Scheduled call dispatch & retry logic |
| **Telephony** | PSTN Carrier | Plivo Voice API | Outbound dialing & call audio recording |
| **STT (Primary)** | Local ASR | IndicConformer 0.60B | Hindi, Gujarati, English recognition |
| **STT (Fallback)**| Cloud ASR | Sarvam AI API (`saaras:v4`) | Cloud speech-to-text fallback |
| **LLM (Primary)** | Local LLM | Qwen-14B (Ollama Q4_K_M) | Multilingual conversational reasoning |
| **LLM (Fallback)**| Cloud LLM | Groq API (`llama-3.3-70b`) | Ultra-low latency cloud inference |
| **TTS (Primary)** | Local TTS | IndicF5 0.40B | Voice synthesis for Indian languages |
| **TTS (Fallback)**| Cloud TTS | gTTS / Google Cloud | Fallback audio synthesis |

---

## 🚀 Deployment Lifecycle

1. **Stage 1 — Local Development**:
   - Developed, linted, and tested locally.
   - Webhook testing via secure tunnels (e.g., ngrok).
2. **Stage 2 — Nirma Supercomputer (HPC) Promotion**:
   - Deployed to Nirma University's high-performance supercomputing node via **SSH**.
   - Accessible via Nirma's institutional domain (e.g., `https://calls.nirmauni.ac.in`).
   - Hardware accelerated via the NVIDIA Container Toolkit (24 GB VRAM allocation).

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
