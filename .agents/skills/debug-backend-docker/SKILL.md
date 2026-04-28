---
name: debug-backend-docker
description: Debugs backend applications running in Docker or Docker Compose by checking related container status and logs before editing code. Use when a web or API bug appears after the agent started containers, or when the user mentions Docker, docker compose, container logs, backend bug, lỗi backend, or log container.
---

# Debug Backend Docker

## When to use

Use this skill when the backend is running in Docker and the user reports a runtime bug from the browser, API client, or another service.

Typical triggers:
- "The app is up but this page/API is broken"
- "The agent already ran docker compose and now I see a bug"
- "Check container logs"
- "Debug backend in Docker"

## Core rule

Do not jump straight into code edits.

First inspect the running Docker services and their logs so the current runtime failure is grounded in evidence.

## Workflow

Copy this checklist and work through it:

```text
Debug Backend Docker
- [ ] Identify whether Docker Compose or plain Docker is running
- [ ] Find the backend-related containers and dependencies
- [ ] Inspect service status, health, restarts, and recent logs
- [ ] Correlate log errors with the reported bug
- [ ] Reproduce the failing action if logs are insufficient
- [ ] Fix the smallest root cause in code or config
- [ ] Rebuild/restart only the affected services
- [ ] Re-check logs and verify the bug is gone
```

### 1. Inspect the current runtime first

Before launching anything new:
- Check existing terminal output to see whether the stack was already started earlier in the session.
- Identify the command that launched the backend, such as `docker compose up`, `docker compose up -d`, or `docker-compose up`.
- Avoid starting duplicate containers if the stack is already running.

### 2. Identify relevant containers

Prefer Docker Compose when the repo uses it.

Start with commands like:

```bash
docker compose ps
```

Fallback if needed:

```bash
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
```

Mark the likely relevant services:
- backend app or API service
- background worker / queue consumer
- reverse proxy
- database
- cache / message broker

Focus on containers that participate in the failing user flow, but include dependencies when the app container shows connection or timeout errors.

### 3. Check logs before reading source code

Read recent logs for the relevant containers first.

Preferred Compose form:

```bash
docker compose logs --tail=200 <service>
```

For multiple suspect services:

```bash
docker compose logs --tail=200 <service-a> <service-b> <service-c>
```

Fallback for plain Docker:

```bash
docker logs --tail=200 <container-name>
```

Look for:
- uncaught exceptions and stack traces
- HTTP 500s, 502s, 504s
- migration or schema errors
- missing environment variables
- authentication failures
- connection refused / DNS / timeout errors
- serialization or validation errors
- worker crashes or restart loops
- proxy upstream errors

If the backend container logs look clean, check dependency containers instead of assuming the bug is in frontend code.

### 4. Correlate logs with the reported bug

Tie the bug report to concrete evidence:
- match timestamps around when the user triggered the failing action
- match request paths, job names, entity IDs, or user actions when visible
- if logs are noisy, narrow to the specific services involved in the failing flow

Search for the first real failure, not just downstream noise.

Examples:
- app returns 500 because database migration is missing
- worker fails because Redis hostname is wrong
- proxy shows 502 because API container is crash-looping

### 5. Reproduce while watching logs when needed

If recent logs are not enough, reproduce the bug while watching logs again.

Useful pattern:

```bash
docker compose logs --tail=50 <service>
```

Then trigger the failing action from the app or API and inspect the new error lines immediately.

### 6. Fix the smallest root cause

Only after log inspection should you move into code or config.

Priorities:
1. Fix the earliest confirmed root cause from logs
2. Prefer the smallest safe change
3. Avoid broad refactors unless logs prove the bug is architectural

When editing, verify related config too:
- compose file service names
- environment variables
- startup command / entrypoint
- ports and internal hostnames
- migrations and seed state

### 7. Rebuild and restart only what changed

After the fix, rebuild or restart the impacted services instead of resetting the whole stack unless required.

Typical commands:

```bash
docker compose up -d --build <service>
```

or, if only a restart is needed:

```bash
docker compose restart <service>
```

If the fix affects a dependency contract, restart the dependent service too.

### 8. Verify with logs again

After restarting:
- confirm the service is healthy and still running
- re-check recent logs for the same error signature
- reproduce the original bug
- confirm the failure no longer appears in logs

Do not stop at "containers are running". The skill is complete only when the runtime error has been explained and re-checked.

## Response format

When reporting back, use this structure:

```markdown
## Findings
- Reported bug:
- Affected containers/services:
- Root cause:
- Log evidence:

## Fix
- Files or config changed:
- Services rebuilt/restarted:

## Verification
- What was re-tested:
- Relevant post-fix log result:
- Remaining risks or follow-ups:
```

## Guardrails

- Do not skip log inspection just because the code "looks suspicious".
- Do not run a second copy of the stack if one is already active.
- Do not inspect only the app container when the symptoms suggest proxy, database, cache, or worker failures.
- Do not claim success without checking post-fix logs.

## Example prompts

- "Use `debug-backend-docker`. The agent already ran docker compose and now the login flow fails with a 500. Debug it from the container logs first."
- "Use `debug-backend-docker`. The page loads but submitting the form breaks the backend. Check the relevant containers and fix the issue."
- "Use `debug-backend-docker`. The web app shows a bug after startup; inspect Docker logs, identify the root cause, and verify the fix."
