## IT Discussion Checklist for Deployment Readiness

### Summary
Use this discussion to lock the infrastructure and policy decisions that will drive the final deployment changes for the Streamlit app. The goal is to leave the meeting with answers for hosting, access control, secrets, networking, observability, and support ownership.

### Key Decisions to Get from IT
- **Hosting platform**: Windows server, Linux server, or container platform.
- **Service model**: Windows Service, `systemd`, Docker, or existing internal app host.
- **Access control**: reverse proxy + SSO preferred; otherwise VPN-only or IP allowlist.
- **Network route**: internal DNS name, fixed port, TLS termination point, and whether direct app-port access will be blocked.
- **Outbound access**: confirm the server can make HTTPS requests to the OpenAI API.
- **Secrets management**: where `OPENAI_API_KEY` will live in production.
- **Log storage**: where app logs should be written, who can access them, and retention/rotation policy.
- **Operational ownership**: who restarts the service, rotates secrets, monitors failures, and handles user issues.

### Exact Topics to Discuss
- **Server and runtime**
  - Which host type will run the app?
  - Which Python version is approved for the server?
  - Can the app run from a dedicated virtual environment in the app directory?
  - Should deployment use pinned Python packages only?
- **Secrets and config**
  - How should production env vars be injected: system env vars, service config, vault, or another secret manager?
  - Can IT provide `OPENAI_API_KEY` securely without using a checked-in `.env`?
  - Should optional runtime knobs also be configurable via env vars?
  - Confirm writable path for `logs/`.
- **Security and access**
  - Will the app sit behind an internal reverse proxy?
  - Is SSO available for internal tools?
  - If not, will access be limited by VPN or internal network rules?
  - Should the raw Streamlit port be inaccessible except through the approved internal route?
- **Data handling**
  - Are uploaded review files allowed to be sent to OpenAI under company policy?
  - Are there any restrictions on review content, retention, or export?
  - Are app logs allowed to contain run metadata and model output summaries?
  - Do logs need shortened retention or extra access controls?
- **Operations**
  - What health check should monitoring use? Suggested: `/_stcore/health`.
  - What restart policy should be used on crash or reboot?
  - What is the rollback path: previous package set, previous folder, or previous container image?
  - How will dependency updates be approved and rolled forward later?
- **Capacity and usage**
  - Expected concurrent users.
  - Whether the current OpenAI budget cap per run is acceptable.
  - Maximum upload size IT wants enforced at the proxy or app layer.
  - Any CPU, memory, or disk quotas for the host.

### Changes Likely to Follow from the IT Answers
- Pin dependencies in `requirements.txt` or create a locked deploy requirements file.
- Add a committed `.env.example` with placeholders for required and optional env vars.
- Add deployment docs with the exact service command and runtime assumptions.
- Add platform-specific service config once the host type is known.
- Add access-control/reverse-proxy notes once the internal route is chosen.
- Potentially tighten logging or add upload-size limits if IT requires it.

### Test and Acceptance Criteria for the Final Deployment Work
- Service starts headlessly and survives restart.
- `OPENAI_API_KEY` is provided by server config, not a local checked-in secret.
- `logs/` is writable by the service account.
- Health endpoint responds through the intended internal route.
- Internal users can access the app only through the approved access-control path.
- One real end-to-end upload → classify → export run succeeds in the hosted environment.
- Rollback steps are written down and verified.

### Assumptions
- The app itself is already functionally validated with real datasets.
- Final deployment changes should be driven by IT’s hosting and security standards rather than guessed locally.
- Preferred default if IT has options: pinned dependencies, env-var based secrets, managed service, reverse proxy, and internal auth in front of Streamlit.
