# AGENTS.md

## Project Overview

FastAPI server for controlling ViCare heating systems (circuits, DHW, heat pumps, ventilation).

**Tech Stack**: FastAPI, Python 3.12+, uv package manager, Nix dev environment.

## Essential Commands

All commands must run inside `nix-shell` or prefixed with `nix-shell --run "command"`:

```bash
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
uv run ruff check .
uv run mypy app
```

## Code Style Guidelines

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
- Use `@pytest.fixture` parametrized fixtures with `dependency_mocker` pattern
- Mock FastAPI dependencies via `app.dependency_overrides`
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
- `LOXONE_URL`, `LOXONE_USER`, `LOXONE_PASSWORD` - Optional Loxone config