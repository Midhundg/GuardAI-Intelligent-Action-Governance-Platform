# GuardAI System Architecture

This document outlines the high-level architecture of the GuardAI Action Governance Platform.

## 🏢 Core Components

### 1. The Gateway (NGINX)
- Serves the frontend static files (HTML, CSS, JS).
- Acts as a reverse proxy, routing API requests to the FastAPI backend.

### 2. The Policy Engine (FastAPI / Python)
- **Framework:** FastAPI for high-performance, asynchronous request handling.
- **Validation:** Uses Pydantic to strictly enforce the schema of incoming AI action payloads.
- **Logic:** Evaluates payloads against enterprise rules (e.g., blocking `record_count > 100`).
- **Explainability:** Generates human-readable reasons for why an action was blocked or flagged.

### 3. The Asynchronous Worker (Celery + Redis)
- **Message Broker:** Redis handles the queueing of heavy tasks.
- **Worker:** Celery processes background tasks such as sending notifications, generating analytics, and cleaning up old audit logs without blocking the main API response.

### 4. Persistence Layer (PostgreSQL)
- Stores all Audit Logs immutably.
- Maintains the Manager Approval Queue for human-in-the-loop actions.
- Stores configured enterprise policies and user roles (RBAC).

### 5. Observability (Prometheus)
- Captures system metrics like latency, API error rates, and total blocked actions over time.
