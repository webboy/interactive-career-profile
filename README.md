# Interactive Career Profile

Interactive Career Profile (ICP) is a planned self-hosted, open-source AI career profile for one candidate/profile owner. It turns a static CV or portfolio into a grounded AI assistant that recruiters, hiring managers, CTOs, founders, and technical evaluators can query about verified career data.

The project is in early implementation. Admin auth, settings, legal backend, profile/career records CRUD, document ingestion, hybrid retrieval, a grounded LangGraph agent, internal MCP lead/email workflows, the public async chat/settings API contract, the Quasar UI shell, and the public chat/legal/lead UX are in place; admin UI workflows remain planned.

## What This Is

ICP is not a generic chatbot over a CV. The goal is a controlled, admin-managed AI career assistant with:

- Public chat for career, skills, projects, leadership, language, availability, and role-fit questions.
- Hybrid retrieval over public structured records and public document chunks only.
- Admin-managed knowledge base with visibility controls.
- Document ingestion, chunking, embeddings, and retrieval logs.
- Full public conversation logging.
- Internal MCP tools for meeting requests, job submissions, follow-up questions, skill evidence, and project case studies.
- Privacy and Terms pages that clearly explain stored conversations and submitted data.

## Hard Requirements

- The public assistant must not hallucinate or invent facts.
- Public answers may use only records/chunks marked `public`.
- `private`, `draft`, and `archived` data must never be used in public answers.
- Salary and compensation questions must be refused.
- Phone numbers must not be exposed through public chat.
- Unsupported questions must produce a safe fallback and be logged as unanswered prompts.
- MCP is internal only; public users talk to the FastAPI backend, not directly to MCP.
- Demo seed data must never run automatically in production.

## Planned Stack

- Frontend: Quasar, Vue 3, TypeScript, Pinia, Vue Router, `vue-i18n`
- Backend API: Python 3.12+, FastAPI, Pydantic, SQLAlchemy, Alembic, psycopg
- Agent: LangGraph with provider-agnostic LLM adapters
- Retrieval: custom application retriever, PostgreSQL, pgvector
- Background jobs: Celery worker with Redis broker
- MCP: FastMCP internal tool server
- Storage: local and S3-compatible drivers
- Email: SMTP, with Mailpit for local development (`docker compose --profile mail up`)

## Local Development Target

The MVP must run locally through Docker Compose. Each runtime service should have its own container; the Celery worker intentionally reuses the API image:

- `ui`
- `api`
- `worker`
- `mcp`
- `postgres`
- `redis`
- optional `mailpit`
- optional reverse proxy

Planned local URLs:

- UI: `http://localhost:9000`
- API: `http://localhost:8000`
- MCP: `http://localhost:8100`
- OpenAPI: `http://localhost:8000/docs`
- Redis broker: `localhost:6379` for local access when needed

## Local Bootstrap

1. Copy environment defaults:

```bash
cp .env.example .env
```

2. Start the containerized stack:

```bash
docker compose up --build
```

3. Optional: include Mailpit for local SMTP testing:

```bash
docker compose --profile mail up --build
```

4. Verify services:

- UI health: `http://localhost:9000/health`
- API health: `http://localhost:8000/health` (includes API version and DB status)
- OpenAPI docs: `http://localhost:8000/docs`
- MCP health: `http://localhost:8100/health`
- Redis health: `docker compose exec redis redis-cli ping`
- Worker process: `docker compose ps worker`
- Mailpit UI (when enabled): `http://localhost:8025`

## API Backend

The API container runs migrations on startup, then starts FastAPI with Uvicorn. The Celery `worker` service uses the same API image/module code and processes public chat jobs from Redis. Job status and final public-safe responses are stored in Postgres `chat_jobs`; Redis is only the broker.

Run backend tests:

```bash
docker compose run --rm api pytest
```

Run UI tests:

```bash
cd apps/ui && npm test -- --run
```

Run migrations manually:

```bash
docker compose run --rm api alembic upgrade head
```

Create the first admin user:

```bash
docker compose run --rm api python -m app.cli create-admin \
  --email admin@example.com \
  --password 'change-me'
```

Auth endpoints:

- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`

Public endpoints:

- `GET /api/public/settings`
- `POST /api/public/chat`
- `GET /api/public/chat/jobs/{job_id}`
- `GET /api/public/privacy`
- `GET /api/public/terms`

Admin endpoints (require auth cookie):

- `GET /api/admin/settings`
- `PUT /api/admin/settings/{key}`
- `GET /api/admin/legal-pages/{slug}`
- `PUT /api/admin/legal-pages/{slug}`
- `GET /api/admin/profile-items`
- `POST /api/admin/profile-items`
- `GET /api/admin/profile-items/{id}`
- `PUT /api/admin/profile-items/{id}`
- `DELETE /api/admin/profile-items/{id}`
- `GET /api/admin/career-records`
- `POST /api/admin/career-records`
- `GET /api/admin/career-records/{id}`
- `PUT /api/admin/career-records/{id}`
- `DELETE /api/admin/career-records/{id}`
- `GET /api/admin/documents`
- `POST /api/admin/documents/upload`
- `POST /api/admin/documents/text`
- `GET /api/admin/documents/{id}`
- `PUT /api/admin/documents/{id}`
- `DELETE /api/admin/documents/{id}`
- `POST /api/admin/documents/{id}/extract`
- `POST /api/admin/documents/{id}/chunk`
- `POST /api/admin/documents/{id}/retry-ingestion`
- `POST /api/admin/documents/{id}/request-embedding`
- `GET /api/admin/documents/{id}/chunks`
- `PUT /api/admin/document-chunks/{chunk_id}`
- `POST /api/admin/document-chunks/{chunk_id}/embed`
- `POST /api/admin/embeddings/document-chunks/run-pending`
- `POST /api/admin/retrieval/debug`
- `GET /api/admin/retrieval-logs`
- `GET /api/admin/retrieval-logs/{id}`
- `GET /api/admin/unanswered-prompts`
- `POST /api/admin/agent/debug`
- `GET /api/admin/conversations/{id}/messages`
- `GET /api/admin/leads/meeting-requests`
- `GET /api/admin/leads/follow-up-requests`
- `GET /api/admin/leads/job-submissions`
- `GET /api/admin/tool-calls`

Hybrid retrieval (ICP-013): public `profile_items` and `career_records` are selected deterministically as canonical facts. Public `document_chunks` with ready embeddings are searched through pgvector as supporting evidence. Structured records take precedence when sources conflict. Admin debug retrieval persists retrieval logs, source items, and unanswered prompts for later agent and admin UI work.

Grounded agent (ICP-014): LangGraph workflow runs policy checks, hybrid retrieval, grounded answer generation, and grounding verification. Salary and phone/contact questions are refused deterministically. Conversations and messages are persisted. Admin debug agent endpoint validates the workflow, and the public chat API now invokes it through persisted Celery-backed jobs. Career records also support optional `record_type` filtering. Document uploads default to `draft` visibility and are limited to 10 MB.

Internal MCP and email workflows (ICP-015): the `mcp` service runs FastMCP with HTTP tool bridge endpoints. The API agent calls MCP tools for meeting requests, follow-up questions, job submissions, CV/profile recommendations, skill evidence, and project case studies. Lead records persist in Postgres and plain-text notification emails go through SMTP/Mailpit. Internal MCP API routes under `/api/internal/mcp/*` are protected by `X-MCP-Internal-Token` and are not public. Configure `ADMIN_NOTIFICATION_EMAIL`, `MCP_INTERNAL_API_TOKEN`, and SMTP settings in `.env`.

Public API and chat contract (ICP-016/ICP-016A): `POST /api/public/chat` validates the public session/conversation, creates a persisted chat job, dispatches grounded agent execution through Celery with Redis as broker, and returns `job_id`, `conversation_id`, `session_id`, and status. Clients poll `GET /api/public/chat/jobs/{job_id}?session_id=...` until the job is `completed` or `failed`. Completed jobs include assistant text, language, refusal/grounding flags, and source-safe labels (`source_type`, `title` only). Internal retrieval log ids, unanswered prompt ids, source ids, snippets, scores, and internal failure details are not exposed. `GET /api/public/settings` returns minimal app metadata for the UI shell.

UI shell (ICP-017): the `ui` service is a Quasar/Vue 3/TypeScript SPA with Vue Router, Pinia, vue-i18n, typed API clients, public/admin layouts, and admin auth state. The browser uses `VITE_API_URL=http://localhost:8000` at build time. API CORS allows the UI origin with credentials for admin cookie auth via `CORS_ALLOWED_ORIGINS`.

Public chat UX (ICP-018): the home page at `/` provides the public chat experience on top of the async job contract. Visitors see a persistent disclaimer, guided lead prompts (meeting request, job description, follow-up question), message history, queued/processing status while polling, refusal styling, collapsible evidence labels, and recoverable failed-job errors. `session_id` and `conversation_id` persist in browser storage, and the header language dropdown feeds the chat `language` field. Privacy and Terms pages render loading, error, and Markdown-ish legal content.

Public chat job statuses:

- `queued` - API accepted the message and enqueued Celery work.
- `processing` - worker picked up the job and is running the agent.
- `completed` - final source-safe response is available on the polling endpoint.
- `failed` - processing failed; polling returns a generic public error message.

Supported upload types: PDF, DOCX, TXT, Markdown. Custom pasted text is also supported.

Current API version is stored in `system_metadata.api_version` and exposed on `GET /health`.

## Repository Layout

```text
apps/
  api/      FastAPI backend foundation and Celery worker module
  mcp/      internal FastMCP tool server
  ui/       Quasar/Vue UI shell
packages/
  shared/   shared schemas/types (future)
data/
  demo/     demo seed assets (future)
storage/    local uploads (gitignored except .gitkeep)
docker/     service Dockerfiles
```

## MVP Roadmap

The local Docker MVP is planned as these implementation tasks:

1. Bootstrap monorepo and Docker Compose stack. **Done**
2. Add backend foundation, config, database, Alembic, pgvector, and API versioning. **Done**
3. Add admin auth, settings, and legal backend. **Done**
4. Add profile and career records backend. **Done**
5. Add file storage and document ingestion. **Done**
6. Add embeddings, custom retrieval, and logging. **Done**
7. Add LLM adapter and LangGraph agent. **Done**
8. Add internal MCP tools and email workflows. **Done**
9. Add public API and chat contract. **Done**
9a. Convert public chat to async job polling with Celery/Redis. **Done**
10. Add UI shell, routing, i18n, and API client. **Done**
11. Add public chat, legal, and lead UX. **Done**
12. Add admin UI for MVP workflows.
13. Add demo seed, tests, and local verification.

## Versioning

The backend/API owns the application version. The current API version is `0.0.11`, exposed on `GET /health`. Every project change should bump the smallest semantic version increment, normally a patch bump.

Version storage is implemented in the API backend (`system_metadata.api_version`).

## Task Completion Workflow

After every completed task:

1. Update local Memory Bank and task handoff files.
2. Review and update this `README.md` when the task changed public-facing project status, setup commands, architecture summary, roadmap progress, versioning notes, or workflow conventions.
3. Bump the API version when backend version storage applies to the change.
4. Create a git commit. Include the task ID in the subject when the commit belongs to a tracked task, for example `(ICP-010)`.

## Commit Messages

This project uses [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).

```text
<type>[optional scope]: <description>
```

When a commit belongs to a tracked task, include the task ID at the end of the subject line:

```text
<type>[optional scope]: <description> (ICP-###)
```

Common types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.

Examples:

```text
feat(infra): bootstrap monorepo and docker compose stack (ICP-007)
feat(profile): add interactive timeline section (ICP-011)
chore: update gitignore
```

### Git Hooks (Optional)

Enable local commit-message validation:

```bash
git config core.hooksPath .githooks
chmod +x .githooks/commit-msg
```
