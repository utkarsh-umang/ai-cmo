<div align="center">
  <img src="assets/logo.png" alt="AI-CMO Logo" width="120" />
</div>

<h1 align="center">AI-CMO</h1>

<p align="center">
  <strong>AI-CMO is a growth system that unifies SEO, GEO, SERP, and community monitoring.</strong><br/>
  <sub>See where your project is discovered, discussed, and compared — then turn those signals into reports, briefs, approvals, and actions.</sub>
</p>


---

## 📖 Documentation

- **[Agent Orchestration Guide](AGENT_ORCHESTRATION.md)** — Learn how the 6-stage pipeline works and meet our specialist agents.

---

## 🚀 Quick Start

### Using Docker (Recommended)

The easiest way to run AI-CMO is using Docker, which automatically builds and runs both the React frontend and the Python backend in a single unified container.

1. Configure your environment:
   ```bash
   cp .env.example .env
   ```
2. Add your API keys to the `.env` file (e.g., `OPENAI_API_KEY`).
3. Start the application:
   ```bash
   docker-compose up --build -d
   ```
4. Access the web dashboard at `http://localhost:8080/app`.

### Local Development

**1. Backend Setup**
```bash
# Install dependencies
pip install -e ".[all]"
crawl4ai-setup

# Configure environment
cp .env.example .env

# Start the backend server
aicmo-web
```
*Note: You can also use the interactive CLI chatbot by running `aicmo`.*

**2. Frontend Setup**
```bash
cd frontend
npm install
npm run dev
```
The frontend dev server will start at `http://localhost:5173`.

---

## 🏗️ System Design

AI-CMO is built as a modular monolithic application designed for rapid iteration and high observability.

### Current Architecture

```mermaid
graph TD
    subgraph Frontend
        React["React 19 SPA"]
        Query["TanStack Query"]
    end

    subgraph Backend
        FastAPI["FastAPI Web Server"]
        Router["API v1 Routes"]
        Worker["In-Process Worker"]
        LLM["Unified LLM Client"]
    end

    subgraph Storage
        SQLite["SQLite + WAL"]
        FS["Local Filesystem"]
    end

    React <--> Router
    Router <--> SQLite
    Worker <--> SQLite
    Worker --> LLM
    Worker --> FS
    LLM --> Providers["OpenAI / DeepSeek / Anthropic"]
```

#### Core Components
- **FastAPI Core**: Handles RESTful API requests, SSE (Server-Sent Events) for real-time progress, and BYOK (Bring Your Own Key) middleware.
- **In-Process Worker**: A task execution engine that polls the `background_tasks` table. It manages concurrency using `asyncio.Semaphore` and handles task recovery on startup.
- **6-Stage Monitoring Pipeline**:
    1. **Context Build**: Multi-agent debate (Product, SEO, Community) to extract brand DNA.
    2. **Signal Collect**: Parallel scanning of SEO, GEO (AI Search), Community (Reddit/HN), and SERP.
    3. **Normalize**: Deduplication and standardization of cross-platform signals.
    4. **Domain Review**: Independent AI analysis for each marketing vertical.
    5. **Strategy Synthesis**: Strategic Director agent synthesizes findings into actions.
    6. **Persist & Publish**: Final results saved to DB and reports generated.
- **Unified LLM Client**: Centralized client in `llm.py` providing automatic retries, exponential backoff, and strict ContextVar isolation for API keys.

---

## 🚀 Scaling to 100k DAU

The current design is optimized for single-node deployment and low-to-medium usage. To handle **100,000 Daily Active Users**, we must address several architectural bottlenecks.

### 🔍 Current Gaps & Bottlenecks
1. **SQLite Contention**: While WAL mode helps, SQLite's single-writer model will cause significant latency under high concurrent writes from thousands of users and workers.
2. **In-Process Workers**: Background tasks (especially crawls) share CPU and Memory with the web server. A spike in scans can crash the entire API service.
3. **Headless Browser Overhead**: Running Playwright/Crawl4AI locally is resource-intensive. Scaling this linearly on one machine is impossible.
4. **State Isolation**: The current system lacks a distributed cache (like Redis). State is tied to local memory or a local file, making horizontal scaling difficult.
5. **Artifact Persistence**: Reports and lead data are stored on the local disk, which is not suitable for multi-instance cloud deployments.

### 🛠️ Proposed High-Scale Architecture

To reach 100k DAU, AI-CMO would move to a **Distributed Micro-Worker Architecture**.

```mermaid
graph TD
    LB["Load Balancer"] --> WebCluster["API Web Cluster"]
    
    subgraph Compute
        WebCluster
        WorkerCluster["Distributed Worker Cluster"]
    end

    subgraph Queue_Cache ["Queue & Cache"]
        Redis["Redis Cache / Broker"]
        Temporal["Temporal / Celery"]
    end

    subgraph Persistent_Storage ["Persistent Storage"]
        Postgres["PostgreSQL Managed"]
        S3["Object Storage / S3"]
    end

    subgraph Specialized_Services ["Specialized Services"]
        Browserless["Browserless.io / Headless Grid"]
        LLMProxy["LLM Proxy / Rate Limiter"]
    end

    WebCluster <--> Redis
    WebCluster <--> Postgres
    Temporal <--> Postgres
    WorkerCluster <--> Temporal
    WorkerCluster --> Browserless
    WorkerCluster --> S3
    WorkerCluster --> LLMProxy
```

#### Key Changes for Scale:
1. **Database Migration**: Move from SQLite to a managed **PostgreSQL** instance (e.g., RDS, Supabase) to handle high-concurrency connections and complex relational queries.
2. **Distributed Task Queue**: Replace the internal polling worker with **Temporal** or **Celery + Redis**. This allows workers to run on dedicated, auto-scaling nodes.
3. **Headless Browser Fleet**: Offload all crawling work to a dedicated fleet like **Browserless.io** or a Playwright Grid running in Kubernetes.
4. **Global Caching**: Use **Redis** for session management, rate limiting, and caching hot signals (e.g., SERP results) to reduce LLM and Database load.
5. **Stateless Artifacts**: Store all generated reports, PDFs, and lead data in **S3-compatible object storage**.
6. **LLM Gateway**: Implement an internal LLM proxy to handle global rate limits, token budget management, and semantic caching for common marketing queries.
7. **Observability**: Move from local logs to a centralized stack (**Prometheus/Grafana** for metrics, **ELK/Loki** for logs, and **OpenTelemetry** for tracing multi-agent pipelines).
8. **Enhanced Security**: Transition from `.env` files to a secure secrets manager (e.g., **AWS Secrets Manager** or **HashiCorp Vault**) and implement **OAuth2/OpenID Connect** for enterprise-grade user authentication.

---
