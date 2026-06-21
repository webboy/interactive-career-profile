# Interactive Career Profile

Interactive Career Profile (ICP) is a planned self-hosted, open-source AI career profile for one candidate/profile owner. It turns a static CV or portfolio into a grounded AI assistant that recruiters, hiring managers, CTOs, founders, and technical evaluators can query about verified career data.

The project is currently in bootstrap. The local Docker monorepo foundation exists, but real FastAPI, Quasar, database models, and MVP features are still planned for later tasks.

## What This Is

ICP is not a generic chatbot over a CV. The goal is a controlled, admin-managed AI career assistant with:

- Public chat for career, skills, projects, leadership, language, availability, and role-fit questions.
- Strict RAG over public records and document chunks only.
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
- MCP: FastMCP internal tool server
- Storage: local and S3-compatible drivers
- Email: SMTP, with Mailpit planned for local development

## Local Development Target

The MVP must run locally through Docker Compose. Each runtime service should have its own Docker image/container:

- `ui`
- `api`
- `mcp`
- `postgres`
- optional `mailpit`
- optional reverse proxy

Planned local URLs:

- UI: `http://localhost:9000`
- API: `http://localhost:8000`
- MCP: `http://localhost:8100`
- OpenAPI: planned in backend foundation task at `http://localhost:8000/docs`

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

4. Verify service placeholders:

- UI health: `http://localhost:9000/health`
- API health: `http://localhost:8000/health`
- MCP health: `http://localhost:8100/health`
- Mailpit UI (when enabled): `http://localhost:8025`

## Repository Layout

```text
apps/
  api/      FastAPI backend placeholder
  mcp/      internal MCP placeholder
  ui/       Quasar UI placeholder
packages/
  shared/   shared schemas/types (future)
data/
  demo/     demo seed assets (future)
storage/    local uploads (gitignored except .gitkeep)
docker/     service Dockerfiles
```

## MVP Roadmap

The local Docker MVP is planned as these implementation tasks:

1. Bootstrap monorepo and Docker Compose stack.
2. Add backend foundation, config, database, Alembic, pgvector, and API versioning.
3. Add admin auth, settings, and legal backend.
4. Add profile and career records backend.
5. Add file storage and document ingestion.
6. Add embeddings, custom retrieval, and logging.
7. Add LLM adapter and LangGraph agent.
8. Add internal MCP tools and email workflows.
9. Add public API and chat contract.
10. Add UI shell, routing, i18n, and API client.
11. Add public chat, legal, and lead UX.
12. Add admin UI for MVP workflows.
13. Add demo seed, tests, and local verification.

## Versioning

The backend/API owns the application version. The initial API version will be `0.0.1`, and every project change should bump the smallest semantic version increment, normally a patch bump.

Version storage is planned as part of the backend foundation task.

## Commit Messages

This project uses [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).

```text
<type>[optional scope]: <description>
```

Common types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.

Example:

```text
feat(profile): add interactive timeline section
```

### Git Hooks (Optional)

Enable local commit-message validation:

```bash
git config core.hooksPath .githooks
chmod +x .githooks/commit-msg
```
