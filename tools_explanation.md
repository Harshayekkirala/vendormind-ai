# 🛠️ VendorMind AI — Tools & Technologies Explained

A comprehensive breakdown of every tool, library, and technology used across the **backend** and **frontend** of the VendorMind AI procurement automation platform.

---

## 🔧 Backend Tools & Libraries

### 📦 Framework & Server

#### [FastAPI](https://fastapi.tiangolo.com/)
- **What it is**: A modern, high-performance Python web framework for building REST APIs.
- **Why it's used**: Powers all the backend API endpoints (document upload, vendor management, procurement sessions, audit trails, etc.).
- **Where used**: [`backend/app/main.py`](file:///c:/Users/harsh/Documents/vendormind-ai/backend/app/main.py)
- **Key feature**: Auto-generates interactive API docs (Swagger UI), supports `async/await` natively.

#### [Uvicorn](https://www.uvicorn.org/)
- **What it is**: A lightning-fast ASGI (Asynchronous Server Gateway Interface) server.
- **Why it's used**: Runs the FastAPI application in production/development mode.
- **How**: Started via `uvicorn app.main:app --reload`

---

### 🤖 AI / LLM Providers

#### [Groq](https://groq.com/) (`groq` SDK)
- **What it is**: An ultra-fast LLM inference provider.
- **Why it's used**: Default LLM provider for structured data extraction via **Llama 3.3 70B Versatile** model.
- **Where used**: [`backend/app/core/llm.py`](file:///c:/Users/harsh/Documents/vendormind-ai/backend/app/core/llm.py#L41-L44)
- **Key feature**: Returns `json_object` responses for strict schema-compliant outputs. Async via `AsyncGroq`.

#### [Google Generative AI (`google-generativeai`)](https://ai.google.dev/)
- **What it is**: Google's AI Python SDK for Gemini models.
- **Why it's used**: Used for **two purposes**:
  1. **Gemini Developer API** — alternative LLM provider (Gemini 1.5 Flash)
  2. **Text Embeddings** — `gemini-embedding-001` model generates vector embeddings for RAG (policy semantic search)
- **Where used**: [`backend/app/core/llm.py`](file:///c:/Users/harsh/Documents/vendormind-ai/backend/app/core/llm.py#L9), [`backend/app/core/rag_store.py`](file:///c:/Users/harsh/Documents/vendormind-ai/backend/app/core/rag_store.py#L54-L59)

#### [Vertex AI (Google Cloud)](https://cloud.google.com/vertex-ai)
- **What it is**: Google Cloud's enterprise-grade AI platform.
- **Why it's used**: Optional premium LLM provider — uses `genai.Client(vertexai=True)` for enterprise deployments.
- **Where used**: [`backend/app/core/llm.py`](file:///c:/Users/harsh/Documents/vendormind-ai/backend/app/core/llm.py#L29-L38)
- **Config**: Requires `VERTEX_PROJECT_ID` and `VERTEX_LOCATION` env vars.

> **LLM Priority**: Vertex AI → Gemini Developer → Groq (fallback)

---

### 🗄️ Database

#### [PostgreSQL + psycopg](https://www.psycopg.org/)
- **What it is**: PostgreSQL is a powerful relational database; `psycopg` is its Python driver (v3).
- **Why it's used**: Stores vendors, purchase history, procurement sessions, audit trails, users, and policy embeddings.
- **Where used**: [`backend/app/core/database.py`](file:///c:/Users/harsh/Documents/vendormind-ai/backend/app/core/database.py)
- **Tables created**:
  | Table | Purpose |
  |-------|---------|
  | `vendors` | Vendor profiles & status |
  | `purchase_history` | Past transactions |
  | `vendor_catalog` | Product/service offerings |
  | `audit_trail` | Review action logs |
  | `procurement_sessions` | Active workflow states |
  | `policies` | Semantic policy library with vector embeddings |
  | `users` | Authentication |
  | `user_sessions` | Session tokens |

#### [pgvector](https://github.com/pgvector/pgvector)
- **What it is**: A PostgreSQL extension for storing and querying vector embeddings.
- **Why it's used**: Enables **semantic similarity search** on procurement policies using cosine distance (`<=>`).
- **Where used**: [`backend/app/core/rag_store.py`](file:///c:/Users/harsh/Documents/vendormind-ai/backend/app/core/rag_store.py#L66-L71)
- **How**: Policy texts are embedded (3072-dim vectors) and stored; queries find closest-match policies.

---

### 📄 Document Processing

#### [PyPDF (`pypdf`)](https://pypdf.readthedocs.io/)
- **What it is**: A pure Python PDF reading library.
- **Why it's used**: Extracts text content from uploaded vendor PDFs (emails, quotations, contracts, meeting notes).
- **Where used**: [`backend/app/core/pdf.py`](file:///c:/Users/harsh/Documents/vendormind-ai/backend/app/core/pdf.py)

#### [FPDF2 (`fpdf2`)](https://py-fpdf2.readthedocs.io/)
- **What it is**: A library for generating PDF documents programmatically.
- **Why it's used**: Generates PDF reports/summaries of procurement decisions for download.
- **Where used**: Report generation endpoints in `main.py`

#### [python-multipart](https://andrew-d.github.io/python-multipart/)
- **What it is**: Streaming multipart form data parser.
- **Why it's used**: Required by FastAPI to handle file uploads (`UploadFile` / `multipart/form-data`).

---

### 🔗 AI Orchestration

#### [LangChain](https://www.langchain.com/)
- **What it is**: A framework for building LLM-powered applications with chains and agents.
- **Why it's used**: Provides orchestration utilities, prompt chaining, and text processing helpers used in agent pipelines.
- **Listed in**: [`requirements.txt`](file:///c:/Users/harsh/Documents/vendormind-ai/backend/requirements.txt)

---

### ✅ Data Validation

#### [Pydantic](https://docs.pydantic.dev/)
- **What it is**: Python's go-to data validation library using type hints.
- **Why it's used**:
  1. Defines request/response schemas for all API endpoints
  2. Defines structured output schemas for LLM responses (JSON parsing)
  3. Settings management via `pydantic-settings`
- **Where used**: [`backend/app/schemas/`](file:///c:/Users/harsh/Documents/vendormind-ai/backend/app/schemas/), [`backend/app/core/config.py`](file:///c:/Users/harsh/Documents/vendormind-ai/backend/app/core/config.py), all agent files

#### [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- **What it is**: Extension of Pydantic for loading settings from environment variables and `.env` files.
- **Why it's used**: Manages `GROQ_API_KEY`, `GEMINI_API_KEY`, `DATABASE_URL`, etc. from the `.env` file.
- **Where used**: [`backend/app/core/config.py`](file:///c:/Users/harsh/Documents/vendormind-ai/backend/app/core/config.py)

---

## 🎨 Frontend Tools & Libraries

### ⚛️ UI Framework

#### [React 19](https://react.dev/)
- **What it is**: A JavaScript library for building user interfaces with a component-based architecture.
- **Why it's used**: Powers the entire frontend SPA (Single Page Application) for VendorMind's dashboard, vendor management, procurement workflows, etc.
- **Where used**: [`frontend/src/App.jsx`](file:///c:/Users/harsh/Documents/vendormind-ai/frontend/src/App.jsx)

#### [React DOM](https://react.dev/reference/react-dom)
- **What it is**: React's companion library for rendering to the browser DOM.
- **Why it's used**: Mounts the React app to the `<div id="root">` in `index.html`.
- **Where used**: [`frontend/src/main.jsx`](file:///c:/Users/harsh/Documents/vendormind-ai/frontend/src/main.jsx)

---

### 🌐 HTTP Client

#### [Axios](https://axios-http.com/)
- **What it is**: A promise-based HTTP client for making API requests.
- **Why it's used**: Handles all REST API calls from frontend to the FastAPI backend (vendor CRUD, file uploads, session management, etc.).
- **Key features used**: Request interceptors, async/await pattern, multipart form data for PDF uploads.

---

### 🎨 Icons

#### [Lucide React](https://lucide.dev/)
- **What it is**: A clean, consistent icon library with React components.
- **Why it's used**: Provides all the UI icons throughout the dashboard (menu icons, status icons, action buttons, etc.).

---

### ⚡ Build & Dev Tools

#### [Vite](https://vitejs.dev/)
- **What it is**: An extremely fast modern frontend build tool and development server.
- **Why it's used**: Bundles the React app for production and provides instant hot-module-reloading (HMR) during development.
- **Config**: [`frontend/vite.config.js`](file:///c:/Users/harsh/Documents/vendormind-ai/frontend/vite.config.js)
- **Scripts**: `npm run dev` (dev server), `npm run build` (production bundle)

#### [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react)
- **What it is**: Official Vite plugin for React support.
- **Why it's used**: Enables JSX transformation and React Fast Refresh in Vite.

---

### 🧹 Linting

#### [Oxlint](https://oxc.rs/docs/guide/usage/linter)
- **What it is**: A blazing-fast JavaScript/TypeScript linter written in Rust.
- **Why it's used**: Enforces code quality and style rules across the frontend codebase.
- **Config**: [`frontend/.oxlintrc.json`](file:///c:/Users/harsh/Documents/vendormind-ai/frontend/.oxlintrc.json)
- **Script**: `npm run lint`

---

## 🏗️ Architecture Summary

```
VendorMind AI
│
├── Frontend (React + Vite)
│   ├── React 19 — UI Components
│   ├── Axios — API Communication  
│   └── Lucide React — Icons
│
└── Backend (FastAPI + Python)
    ├── FastAPI + Uvicorn — REST API Server
    ├── PostgreSQL + psycopg — Database
    ├── pgvector — Semantic Policy Search
    ├── PyPDF — PDF Text Extraction
    ├── FPDF2 — PDF Report Generation
    ├── Pydantic — Data Validation & Schemas
    │
    └── AI Layer
        ├── Groq (Llama 3.3 70B) — Default LLM
        ├── Gemini Developer API — Alt LLM + Embeddings
        ├── Vertex AI — Enterprise LLM Option
        └── LangChain — Orchestration Utilities
```

---

## 🤖 Multi-Agent Pipeline (Key Agents)

| Agent | Role |
|-------|------|
| **PlannerAgent** | Orchestrates all sub-agents in sequence |
| **EmailAgent** | Extracts data from vendor emails |
| **QuoteAgent** | Parses quotation documents |
| **ContractAgent** | Analyzes contract terms |
| **MeetingAgent** | Processes meeting notes |
| **PolicyComplianceAgent** | RAG-based policy rule checking |
| **MemoryAgent** | Retrieves vendor history from DB |
| **RiskAgent** | Calculates vendor risk score |
| **MissingInfoAgent** | Identifies information gaps |
| **ReasoningAgent** | Synthesizes all signals |
| **RecommendationExplainabilityAgent** | Generates final human-readable recommendation |
