# Code Quality Report (Agent 1)

Date: 2026-03-06  
Repository: `macrocoach`

## Scope and approach

This report captures a **non-invasive quality assessment** (no production code changes) using linting, typing, and tests plus targeted source review.

## Tooling results

- **Ruff lint:** `ruff check src tests` ✅ passed.
- **Mypy typing:** `mypy src` ❌ failed due to missing third-party type stubs (`requests`).
- **Pytest run:** `pytest -q -o addopts=''` ❌ failed, mostly due to missing async test plugin support (`pytest-asyncio`), plus async marker/config warnings.
- **Dependency install attempt:** `pip install -r requirements-dev.txt` ⚠️ blocked by proxy/network restrictions while resolving `pytest-asyncio`.

## Key technical debt and risk hotspots

### 1) Broad exception handling and user-facing raw error messages (High)

- API endpoints often catch broad `Exception` and return `detail=str(e)` directly.
- This can leak internal implementation details to clients and makes incident triage noisier.

Examples:
- `chat_endpoint`, `create_or_update_profile`, `get_profile`, and `get_user_status` in `src/macrocoach/main.py`.
- Similar broad catches and silent fallbacks in agent flows.

**Recommendation**
- Introduce a shared error-mapping layer (domain errors → HTTP status + stable error codes).
- Replace `detail=str(e)` with sanitized messages and structured server logs.

### 2) Monolithic methods with mixed responsibilities (Medium)

Several methods are large enough to hinder readability/testing and increase regression risk:

- `MealGenAgent.__init__` (data bootstrapping + config setup)
- `MealGenAgent._generate_single_meal` (prompt construction + model call + parsing + nutrition calculations)
- `show_dashboard` (UI rendering + API transport + formatting)
- `PlannerAgent.generate_daily_plan` (business rules + summarization + target allocation)

**Recommendation**
- Extract pure helper functions for:
  - prompt payload construction,
  - API response parsing/validation,
  - nutrition math,
  - Streamlit view-model assembly.
- Add unit tests around the extracted pure functions before deeper refactors.

### 3) Observability inconsistencies (`print` and silent `pass`) (Medium)

- Some modules still use `print(...)` for runtime faults.
- One nested logger failure path intentionally swallows exceptions with `pass`.

This weakens structured telemetry and makes production debugging harder.

**Recommendation**
- Standardize on module-level logger usage.
- Replace silent `pass` with at least debug-level logging (while preserving user response flow).

### 4) Dev-quality pipeline fragility in current environment (Medium)

- Tests rely on `pytest-asyncio`, but current environment couldn’t install it due to network/proxy constraints.
- `pytest` default config assumes `pytest-cov`; when plugin is unavailable, command fails before tests run.

**Recommendation**
- Keep `pytest-asyncio` and `pytest-cov` pinned in lock/constraints used by CI.
- Add a lightweight fallback test command in docs for constrained environments:
  - `pytest -q -o addopts=''`
- Ensure CI enforces full plugin-enabled test matrix.

### 5) Type-check completeness gap (Low)

- `mypy` stops on missing stubs for `requests` in the Streamlit dashboard.

**Recommendation**
- Ensure `types-requests` is installed in CI/dev images.
- Keep `mypy src` as required status check once environment parity is fixed.

## Prioritized refactoring queue for Agent 3

1. **Error handling hardening:** sanitize HTTP errors and centralize exception mapping.
2. **Meal generation decomposition:** split prompt builder, LLM adapter, and result mapper.
3. **Dashboard separation:** isolate API client + view-model mapping from Streamlit rendering.
4. **Logging unification:** replace `print`/silent paths with structured logging.
5. **Quality pipeline stabilization:** enforce plugin availability and deterministic local/CI commands.

## Suggested measurable quality targets

- 0 raw `detail=str(e)` responses on public endpoints.
- 0 `print(...)` statements in runtime paths.
- 100% async tests executed under `pytest-asyncio` in CI.
- `mypy src` passes in CI with pinned dev dependencies.
- Reduce top-5 largest functions by at least 30% LOC each through extraction.
