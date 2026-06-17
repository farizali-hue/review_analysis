# AGENTS.md

## Purpose

This repository uses `agent-skills` as a Codex workflow layer, not as an application dependency.

- Do not import anything from `agent-skills` into Python code.
- Use the skills to guide planning, implementation, review, and deployment work in this repo.
- Keep the active skill set small and task-specific instead of loading the full pack every session.

## Project Context

- Primary app entrypoint: `review_classifier_python.py`
- Pure/testable logic module: `review_classifier_core.py` (imported by the entrypoint; covered by `tests/`)
- Legacy prototypes (`streamlit_app.py`, `neg_issue.py`, `review_classifier_python_v1.py`) were removed from the working tree; recoverable from git history (initial commit) if needed
- Runtime shape: Streamlit review-classification app with file upload/download, OpenAI API calls, `.env`-based local configuration, and local run logs under `logs/`
- Deployment target: internal server running the Streamlit app as a service

Unless a task explicitly targets a prototype file, prefer the main app in `review_classifier_python.py`.

## Installed Core Skills

Use these installed skills by default:

- `using-agent-skills`
- `spec-driven-development`
- `test-driven-development`
- `code-review-and-quality`
- `security-and-hardening`
- `shipping-and-launch`

Optional later, if installed:

- `ci-cd-and-automation`
- `debugging-and-error-recovery`
- `frontend-ui-engineering`
- `api-and-interface-design`

## Default Workflow

For any non-trivial change, follow this order:

1. Start with `using-agent-skills` if the correct workflow is unclear.
2. Use `spec-driven-development` before changing behavior or structure.
3. Use `test-driven-development` while implementing logic changes or refactors.
4. Use `code-review-and-quality` before considering the change complete.
5. Use `shipping-and-launch` for anything that affects deployment, operability, or release readiness.

## Task Routing

- Streamlit UI changes in `review_classifier_python.py`: use `frontend-ui-engineering` when available.
- Refactors that separate business logic from Streamlit UI: use `api-and-interface-design` when available.
- File uploads, `.env`, `OPENAI_API_KEY`, OpenAI requests, user input validation, and logging: use `security-and-hardening`.
- Deployment work such as Docker, service scripts, reverse proxy config, environment config, and internal hosting: use `shipping-and-launch` and `ci-cd-and-automation` when available.
- Failures in parsing, batching, JSON responses, response validation, or logs: use `debugging-and-error-recovery` when available.

## Repo-Specific Guardrails

- Never hardcode secrets, API keys, or sample credentials in code, docs, logs, or tests.
- Preserve writability of the `logs/` directory.
- Keep `agent-skills` out of the runtime dependency graph for the Streamlit app.
- Preserve the main user flow: upload CSV/XLS/XLSX, map columns, classify reviews, and export CSV results.
- Prefer environment-based configuration for server deployment.

## Verification Expectations

- Smoke test the app with `py -m streamlit run review_classifier_python.py` or the active environment's equivalent.
- For future logic changes, add or update tests covering:
  - negative review filtering
  - review-date window handling
  - JSON parsing and response-shape fallbacks
  - fallback behavior when categories or justifications are missing or malformed
- For security-sensitive changes, verify that secret handling remains environment-based and no sensitive data is exposed in logs or UI.
- For deployment changes, verify headless/server startup and confirm the logs path still works.

## Working Style

- For non-trivial tasks, explicitly mention the relevant skill in the prompt or rely on this file to steer the session.
- If a task spans several areas, load only the few skills needed for that task.
- When in doubt, choose the smallest workflow that still gives clear verification steps.
