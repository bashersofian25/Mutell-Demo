# Mutell — POS Interaction Evaluation Platform

Mutell is a **multi-tenant SaaS platform** for monitoring and evaluating Point-of-Sale (POS) terminal interactions. It captures customer-agent text conversations, runs AI-powered quality evaluations across 8 metrics, and presents actionable insights through a web dashboard.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [System Components](#system-components)
- [Data Flow](#data-flow)
- [Database Schema](#database-schema)
- [Authentication & Authorization](#authentication--authorization)
- [AI Evaluation Engine](#ai-evaluation-engine)
- [API Endpoints](#api-endpoints)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)

---

## Architecture Overview

```mermaid
graph TB
    subgraph "POS Terminals"
        T1["Terminal 1<br/>terminal-agent"]
        T2["Terminal 2<br/>terminal-agent"]
        T3["Terminal N<br/>terminal-agent"]
    end

    subgraph "Docker Compose"
        subgraph "Backend Services"
            API["FastAPI Server<br/>:8000"]
            WORKER["Celery Worker<br/>(evaluation, aggregation, report)"]
            BEAT["Celery Beat<br/>(scheduler)"]
        end

        subgraph "Frontend"
            PORTAL["Next.js Portal<br/>:3000"]
        end

        subgraph "Infrastructure"
            DB[("PostgreSQL 16<br/>:5432")]
            REDIS[("Redis 7<br/>:6379")]
            S3["RustFS / MinIO<br/>:9000"]
            MAIL["Mailpit<br/>:8025"]
        end
    end

    USER["👤 Platform User"]

    T1 -- "API Key Auth<br/>POST /slots" --> API
    T2 -- "API Key Auth<br/>POST /slots" --> API
    T3 -- "API Key Auth<br/>POST /slots" --> API
    USER -- "JWT Auth" --> PORTAL
    PORTAL -- "REST API" --> API
    API --> DB
    API --> REDIS
    API --> S3
    API --> MAIL
    API -- "dispatch tasks" --> REDIS
    REDIS -- "consume tasks" --> WORKER
    BEAT -- "schedule" --> REDIS
    WORKER --> DB
    WORKER --> S3
    WORKER --> MAIL
```

---

## System Components

| Component | Technology | Port | Purpose |
|---|---|---|---|
| **Backend API** | FastAPI + SQLAlchemy 2.0 + Alembic | 8000 | REST API, JWT auth, slot management |
| **Celery Worker** | Celery + Redis | — | Async evaluation, aggregation, report generation |
| **Celery Beat** | Celery Beat | — | Periodic task scheduling (every 15s eval, every 15min aggregation) |
| **Portal** | Next.js 16 + React 19 + Tailwind CSS 4 | 3000 | Web dashboard, analytics, admin UI |
| **Terminal Agent** | Python (scaffold) | — | Records POS interactions, uploads to backend |
| **PostgreSQL** | PostgreSQL 16 | 5432 | Primary database (13 models) |
| **Redis** | Redis 7 | 6379 | Celery broker, token blacklist, eval concurrency semaphore |
| **RustFS/MinIO** | S3-compatible storage | 9000 | PDF report storage |
| **Mailpit** | SMTP testing | 8025/1025 | Local email testing |

---

## Data Flow

### Slot Upload & Evaluation Pipeline

```mermaid
sequenceDiagram
    participant TA as Terminal Agent
    participant API as FastAPI Server
    participant DB as PostgreSQL
    participant R as Redis
    participant CW as Celery Worker
    participant AI as AI Provider
    participant AGG as Aggregation Worker

    TA->>API: POST /api/v1/slots<br/>(API Key Auth)
    API->>API: Validate plan quota
    API->>DB: INSERT Slot (status: pending)
    API->>R: Dispatch eval_scheduler
    API-->>TA: 202 Accepted

    Note over R,CW: Every 15 seconds
    R->>CW: schedule_pending_evaluations
    CW->>CW: Acquire Redis lock (dedup)
    CW->>CW: Check tenant concurrency limit
    CW->>CW: Check user concurrency limit
    CW->>R: Dispatch evaluate_slot task

    R->>CW: evaluate_slot(slot_id)
    CW->>DB: Load slot + tenant + AI config
    CW->>CW: Decrypt API key (Fernet)
    CW->>AI: POST /chat/completions (prompt)
    AI-->>CW: JSON evaluation response
    CW->>DB: INSERT Evaluation (8 scores, tags, flags)
    CW->>DB: UPDATE Slot (status: evaluated)
    CW->>R: Trigger aggregation
    CW->>AGG: compute_aggregations(tenant_id)
    AGG->>DB: UPSERT AggregatedEvaluation
```

### Report Generation Pipeline

```mermaid
sequenceDiagram
    participant U as User
    participant API as FastAPI
    participant R as Redis
    participant CW as Celery Worker
    participant S3 as MinIO/S3
    participant MAIL as Mailpit

    U->>API: POST /api/v1/reports
    API->>DB: INSERT Report (status: generating)
    API->>R: Dispatch generate_report task
    API-->>U: 202 Accepted

    R->>CW: generate_report(report_id)
    CW->>DB: Query slots + evaluations + notes
    CW->>CW: Render HTML table
    CW->>CW: Convert HTML → PDF (WeasyPrint)
    CW->>S3: Upload PDF
    CW->>DB: UPDATE Report (status: ready, file_url)
    CW->>MAIL: Send "Report Ready" email

    U->>API: GET /api/v1/reports/{id}
    API-->>U: Report metadata (status: ready)
    U->>API: GET /api/v1/reports/{id}/download
    API->>S3: Generate presigned URL (1h)
    API-->>U: 302 Redirect to S3 URL
```

---

## Database Schema

```mermaid
erDiagram
    Plan {
        uuid id PK
        string name
        int max_terminals
        int max_users
        int max_slots_per_day
        int retention_days
        string[] allowed_ai_providers
        boolean custom_prompt_allowed
        boolean report_export_allowed
        int api_rate_limit_per_min
        int max_concurrent_evaluations
    }

    Tenant {
        uuid id PK
        string name
        string slug UK
        string status
        uuid plan_id FK
        int slot_duration_secs
        int max_concurrent_evaluations
    }

    User {
        uuid id PK
        string email UK
        string full_name
        string role
        string status
        string password_hash
        uuid tenant_id FK
    }

    UserPermission {
        uuid id PK
        uuid user_id FK
        string permission
        boolean granted
    }

    NotificationSetting {
        uuid id PK
        uuid user_id FK
        boolean email_evaluations
        boolean email_failures
        boolean email_reports
    }

    Terminal {
        uuid id PK
        string name
        string api_key_hash
        string api_key_prefix
        string status
        uuid tenant_id FK
    }

    Slot {
        uuid id PK
        uuid terminal_id FK
        uuid tenant_id FK
        uuid triggered_by_user_id FK
        timestamp started_at
        timestamp ended_at
        string raw_text
        string language
        string status
        jsonb tags
        jsonb metadata
    }

    Evaluation {
        uuid id PK
        uuid slot_id FK
        uuid tenant_id FK
        string ai_provider
        string ai_model
        decimal score_overall
        decimal score_sentiment
        decimal score_politeness
        decimal score_compliance
        decimal score_resolution
        decimal score_upselling
        decimal score_response_time
        decimal score_honesty
        string sentiment_label
        string summary
        string[] strengths
        string[] weaknesses
        string[] recommendations
        string[] flags
        jsonb raw_response
    }

    AggregatedEvaluation {
        uuid id PK
        uuid tenant_id FK
        uuid terminal_id FK
        string period_type
        timestamp period_start
        timestamp period_end
        int slot_count
        decimal avg_score_overall
    }

    Note {
        uuid id PK
        uuid tenant_id FK
        uuid user_id FK
        uuid slot_id FK
        string content
    }

    Report {
        uuid id PK
        uuid tenant_id FK
        uuid generated_by FK
        string title
        timestamp period_start
        timestamp period_end
        string file_url
        string status
    }

    AIProvider {
        uuid id PK
        string slug UK
        string display_name
        string base_url
        string api_key_enc
        jsonb supported_models
    }

    TenantAIConfig {
        uuid id PK
        uuid tenant_id FK
        uuid provider_id FK
        string model_id
        string api_key_enc
        boolean is_default
        text custom_prompt
    }

    AuditLog {
        uuid id PK
        uuid tenant_id FK
        uuid user_id FK
        string action
        string resource_type
        string resource_id
        jsonb detail
    }

    Plan ||--o{ Tenant : "has"
    Tenant ||--o{ User : "has"
    Tenant ||--o{ Terminal : "owns"
    Tenant ||--o{ Slot : "owns"
    Tenant ||--o{ Report : "owns"
    Tenant ||--o{ TenantAIConfig : "configures"
    Tenant ||--o{ AggregatedEvaluation : "aggregates"
    User ||--o{ UserPermission : "has"
    User ||--|| NotificationSetting : "has"
    User ||--o{ Slot : "triggers re-eval"
    Terminal ||--o{ Slot : "records"
    Slot ||--o| Evaluation : "evaluated by"
    Slot ||--o{ Note : "annotated by"
    AIProvider ||--o{ TenantAIConfig : "used in"
```

---

## Authentication & Authorization

### Dual Authentication System

```mermaid
graph LR
    subgraph "User Authentication"
        U["👤 User"] --> LOGIN["Email/Password<br/>or Google OAuth"]
        LOGIN --> JWT["JWT Access Token<br/>(15 min) + Refresh (7 days)"]
        JWT --> API["API Requests<br/>Authorization: Bearer &lt;token&gt;"]
    end

    subgraph "Terminal Authentication"
        T["📟 Terminal"] --> KEY["API Key<br/>pk_live_&lt;token&gt;"]
        KEY --> API2["Slot Upload<br/>Authorization: Bearer pk_live_..."]
    end
```

### Role-Based Access Control

```mermaid
graph TD
    SA["super_admin<br/>Level 4"] --> TA["tenant_admin<br/>Level 3"]
    TA --> M["manager<br/>Level 2"]
    M --> V["viewer<br/>Level 1"]

    SA -- "Platform-wide access<br/>All tenants, no tenant_id" --> P1["Manage tenants, plans,<br/>AI providers, audit logs"]
    TA -- "Full tenant access" --> P2["Manage terminals, users,<br/>reports, settings"]
    M -- "Limited tenant access" --> P3["Users, reports, analytics<br/>No terminal management"]
    V -- "Read-only" --> P4["View dashboard, slots,<br/>analytics"]

    style SA fill:#dc2626,color:#fff
    style TA fill:#ea580c,color:#fff
    style M fill:#2563eb,color:#fff
    style V fill:#6b7280,color:#fff
```

### Key Auth Details

- **Users**: JWT (HS256) — access token (15 min) + refresh token (7 days). On logout, user ID is blacklisted in Redis.
- **Terminals**: API key (`pk_live_<random>`) — prefix stored in DB, full key bcrypt-hashed. Shown once on creation.
- **6 granular permissions**: `export_reports`, `view_analytics`, `manage_terminals`, `manage_users`, `create_notes`, `generate_reports`

---

## AI Evaluation Engine

### Supported Providers

```mermaid
graph LR
    subgraph "Mutell AI Engine"
        PB["Prompt Builder"] --> ADP["Adapter Factory"]
        ADP --> O["OpenAI<br/>gpt-4o, gpt-4o-mini"]
        ADP --> A["Anthropic<br/>claude-sonnet-4"]
        ADP --> G["Gemini<br/>gemini-2.0-flash"]
        ADP --> Z["ZAI (GLM)<br/>glm-4-flash"]
        ADP --> D["DeepSeek<br/>deepseek-chat"]
    end

    subgraph "Configuration Hierarchy"
        PP["Platform Provider<br/>(global API key)"]
        TC["Tenant AI Config<br/>(override key + model + custom prompt)"]
    end

    TC -.->|"overrides"> PP
    PP -.-> ADP
```

### Evaluation Process

Each conversation is scored across **8 metrics** (0–100 scale):

| Metric | Description |
|---|---|
| `score_overall` | Overall interaction quality |
| `score_sentiment` | Customer sentiment analysis |
| `score_politeness` | Agent politeness and courtesy |
| `score_compliance` | Adherence to business rules |
| `score_resolution` | Issue resolution effectiveness |
| `score_upselling` | Upselling attempts and quality |
| `score_response_time` | Response promptness assessment |
| `score_honesty` | Honesty and transparency |

The AI also extracts: **strengths**, **weaknesses**, **recommendations**, **flags**, **unavailable items**, **swearing instances**, **off-topic segments**, and **speaker identification**.

### Concurrency Control

```mermaid
graph TD
    S["Pending Slots in DB"] --> SCH["Eval Scheduler<br/>(every 15 seconds)"]
    SCH --> L["Acquire Redis Lock<br/>(deduplication)"]
    L --> TCL["Check Tenant<br/>Concurrency Limit"]
    TCL --> UCL["Check User<br/>Concurrency Limit"]
    UCL --> DSP["Dispatch evaluate_slot tasks"]
    DSP --> SEM["Redis Semaphore<br/>(sorted set with TTL)"]
    SEM --> REL["Release on completion"]
```

Tenant concurrency limits come from the **Plan** (or per-tenant override). The scheduler re-triggers itself if slots were skipped due to limits.

---

## API Endpoints

| Prefix | Purpose |
|---|---|
| `/api/v1/auth` | Login, register, Google OAuth, refresh, logout, forgot/reset password, accept invite |
| `/api/v1/slots` | Upload (terminal), list, detail, re-evaluate, bulk re-evaluate |
| `/api/v1/evaluations` | Get evaluation by slot_id |
| `/api/v1/aggregations` | Pre-computed score averages (hour/day/week/month) |
| `/api/v1/terminals` | CRUD, ping/heartbeat, regenerate API key |
| `/api/v1/users` | List, invite, update, delete, permissions |
| `/api/v1/tenants` | CRUD for tenant organizations |
| `/api/v1/notes` | CRUD annotations on slots |
| `/api/v1/reports` | Create, download (PDF), list, delete |
| `/api/v1/plans` | Subscription plan management |
| `/api/v1/settings/ai` | AI provider configuration per tenant |
| `/api/v1/settings` | Notification preferences |
| `/api/v1/dashboard` | KPI stats, trends |
| `/api/v1/analytics` | Comprehensive analytics summary |
| `/api/v1/admin` | Super admin: tenants, plans, users, AI providers, audit log, health |

---

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Copy `.env.example` to `.env` and fill in API keys

```bash
cp .env.example .env
# Edit .env — add AI provider keys, Google OAuth credentials, etc.
```

### Launch Everything

```bash
docker compose up --build
```

This starts all services:

| Service | URL |
|---|---|
| Portal (Dashboard) | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| MinIO Console | http://localhost:9001 |
| Mailpit (Email) | http://localhost:8025 |

### Default Seed Data

On first startup, the system creates:

- **3 Plans**: Starter (3 terminals, 5 users, 500 slots/day), Professional (15/25/5000), Enterprise (100/200/100000)
- **5 AI Providers**: OpenAI, Anthropic, Gemini, ZAI, DeepSeek
- **1 Super Admin**: `admin@platform.com` / `admin123`

---

## Project Structure

```
Mutell-Demo/
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── main.py          # FastAPI app setup, CORS, middleware
│   │   ├── core/            # Config, database, security, dependencies, crypto, middleware
│   │   ├── models/          # 13 SQLAlchemy models
│   │   ├── routes/          # API route handlers
│   │   ├── services/        # Business logic layer
│   │   ├── ai_engine/       # AI evaluation (prompt builder + 5 adapters)
│   │   └── workers/         # Celery tasks (eval, aggregation, report, scheduler)
│   ├── alembic/             # Database migrations
│   ├── scripts/             # Seed data, load tests, sample conversations
│   └── tests/               # Backend tests
│
├── portal/                  # Next.js frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── (auth)/      # Login, signup, forgot/reset password, invite
│   │   │   └── (app)/       # Dashboard, slots, analytics, terminals, team, reports, settings, admin
│   │   ├── components/      # Shared UI components
│   │   ├── context/         # React context providers
│   │   ├── hooks/           # TanStack React Query hooks
│   │   ├── services/        # API service modules
│   │   ├── lib/             # Axios client, formatters
│   │   └── types/           # TypeScript definitions
│   └── package.json
│
├── terminal-agent/          # Python POS terminal agent (scaffold)
│   ├── src/
│   │   ├── main.py         # Entry point
│   │   ├── recorder.py     # Conversation recorder
│   │   ├── uploader.py     # HTTP upload to backend
│   │   ├── retry.py        # Exponential backoff
│   │   ├── buffer.py       # Disk buffer for failed uploads
│   │   ├── slot.py         # Slot payload model
│   │   └── sync.py         # Config sync from API
│   └── tests/
│
├── postman/                 # Postman collection & environment
├── docker-compose.yml       # Full stack orchestration
├── .env.example             # Environment template
└── API_MANUAL.md            # Detailed API documentation
```

---

## License

Proprietary — All rights reserved.
