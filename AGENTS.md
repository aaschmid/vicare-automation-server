# AGENTS.md

## Project Overview

FastAPI server for controlling ViCare heating systems (circuits, DHW, heat pumps, ventilation).

**Tech Stack**: FastAPI, Python 3.12+, uv package manager, Nix dev environment.

## Essential Commands

All commands must run inside `nix-shell` or prefixed with `nix-shell --run "command"`:

```bash
# Virtual environment
uv sync --locked --all-extras --dev

# Development server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-config log-config.json

# Tests
uv run pytest                                   # All tests
uv run pytest tests/api/test_health.py          # Single file
uv run pytest tests/api/test_health.py -v       # Verbose
uv run pytest tests/api/test_health.py::test_name  # Specific test
uv run pytest --cov=app --cov-report=html      # With coverage

# Code quality (run all before committing)
uv run black .
uv run isort .
uv run ruff check app/ tests/
uv run mypy app
```

## Code Style Guidelines

Do minimal necessary changes and don't touch anything not required to fulfill the current task.

### Imports
- Standard library imports first, then third-party, then local (app.*)
- Use `import typing as t` for type-only imports
- Avoid `from typing import *` - use specific imports
- Group related imports, separate with blank line

### Formatting
- Black: 120 character line length
- isort: `profile = "black"` for consistent sorting
- No trailing whitespace

### Type Hints
- Always use explicit type hints on functions
- For FastAPI dependencies: `Annotated[Type, Depends(dependency)]`
- Use Pydantic models for request/response bodies
- Prefer `|` union syntax (Python 3.10+) over `Optional[]` and `Union[]`
- Use `t.Literal[]` for constrained string enums

### Naming Conventions
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`
- Route prefixes: `ROUTE_PREFIX_COMPONENT = "/path"`

### Error Handling
- Use `HTTPException` for route-level errors (4xx/5xx status codes)
- PyViCare exceptions handled centrally in `app/main.py` with status codes:
  - 401: Invalid credentials/OAuth timeout
  - 405: Not supported feature/invalid data/command error
  - 424: Invalid configuration
  - 429: Rate limit
  - 500: Internal server error
- Starlette `status` module for status constants

### FastAPI Patterns
- Use `APIRouter` for route organization, define `prefix` at module level
- Return Pydantic models or dict for responses
- Use `Annotated[Type, Path(...)]` for path parameters
- Use `Annotated[Type, Body()]` for request bodies
- Use `status_code=status.HTTP_204_NO_CONTENT` for PUT endpoints with no body return

### Testing
- Use pytest with fixtures in `tests/conftest.py`
- Use `@pytest.fixture` parametrized fixtures with `dependency_mocker` pattern and use provided mocks
- Use FastAPI dependency override via `app.dependency_overrides` only if necessary
- Test both success and error paths
- Use `record_requests()` helper from conftest for tracking tests

### Dependencies
- FastAPI dependencies in `app/dependencies.py`
- Use `@lru_cache()` for singleton dependencies (Settings, RequestTracker, PyViCare)
- Settings via pydantic-settings, load from `.env` file

## Project Structure

```
app/
  api/           # Route handlers (one router per module)
  dependencies.py # FastAPI dependency providers
  main.py        # App setup, exception handlers
  request_tracking.py # Middleware, RequestTracker
  settings.py    # Pydantic settings
tests/
  api/           # Test files mirror app/api/
  conftest.py    # Shared fixtures
```

## Environment Variables

Required in `.env`:
- `CLIENT_ID` - ViCare OAuth client ID
- `EMAIL` - ViCare account email
- `PASSWORD` - ViCare account password
- `APPLETV_HOST` - Apple TV device IPv4 address
- `APPLETV_COMPANION_IDENTIFIER` -Apple TV companion identifier
- `APPLETV_COMPANION_CREDENTIALS` - Apple TV companion credentials

## Special hints

Pairing with AppleTV is currently manually

## Commit Conventions

This project uses [Conventional Commits](https://www.conventionalcommits.org/) with a scope, e.g. `feat(appletv):`, `feat(ReqTracker):`, `chore(deps): Bump ...`.

Every commit must be signed off (`-s` / `--signoff`), adding a `Signed-off-by: <Name> <email>` trailer. This is required for all commits.

### Keep docs in sync with code
- When you add, remove, or rename a field in `app/settings.py`, **also update** this file's Environment Variables section and `readme.md` in the same change.
- Same applies to route prefixes, env var names, and CLI commands.
- Before finishing a task, grep the repo for the changed symbol to catch stale references.

### Run tests and linting, do not assume
- After any production code change, run the full linting and test suite (see "Essential Commands" above).
- Do not claim "tests pass" without having run them in this session.
- Only consider a test "green" if it passes in the current sandbox; if a failure is caused by the sandbox (e.g. `PermissionError` reading `.env`), say so explicitly and do not silently ignore it.
- Prefer fixing root causes over suppressing warnings (no `filterwarnings` to hide warnings you could fix).

### Dependency changes require a working venv
- Changing `pyproject.toml` dependencies requires re-locking (`uv lock`) **and** syncing (`uv sync --locked --all-extras --dev`) so the new package is actually installed.
- A dependency change is only complete when `uv sync --locked --all-extras --dev` succeeds and the tests pass with the new venv. A successful `uv lock` alone is NOT enough.
- If the sandbox blocks the wheel download, leave the change uncommitted and flag it to the user instead of committing a venv-breaking state.

### Commit hygiene
- Only commit what is staged. Check `git status` and `git diff --cached` before committing.
- Do not stage extra files "to be helpful"; if unrelated changes exist in the worktree, leave them unstaged and mention them.
- Keep commits focused: one logical change per commit (e.g. do not mix a feature rework with a dependency swap).
