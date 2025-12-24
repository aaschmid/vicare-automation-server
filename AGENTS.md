# AGENTS.md

This document provides information for AI agents working with this repository.

## Project Overview

**vicare-automation-server** is a lightweight FastAPI server for accessing and manipulating ViCare products. It provides REST API endpoints for controlling various ViCare heating system components including circuits, domestic hot water (DHW), heat pumps, and ventilation systems.

### Key Technologies
- **Framework**: FastAPI
- **Python Version**: 3.12+
- **Package Manager**: uv
- **Development Environment**: Nix (via `shell.nix`)

## Nix Environment

This project uses Nix for reproducible development environments. The `shell.nix` file defines the required dependencies and sets up the development environment automatically.

### Required Nix Packages
- `python312` - Python 3.12 interpreter
- `uv` - Fast Python package installer and resolver

### Environment Setup

The `shell.nix` file automatically:
1. Installs Python 3.12 and uv
2. Runs `uv sync --all-extras --dev` to install all dependencies (including dev dependencies)
3. Creates symlinks in `.direnv/bin` for easy access to tools

### Entering the Nix Shell

To enter the development environment, run:

```bash
nix-shell
```

Or if using direnv (recommended):

```bash
direnv allow
```

This will automatically activate the environment when you enter the directory.

### Verifying the Environment

Once in the nix shell, you can verify the setup:

```bash
python --version  # Should show Python 3.12.x
uv --version      # Should show uv version
```

## Running Commands

**Note**: All commands should be run within the nix shell environment. Either enter `nix-shell` first, or use `nix-shell --run "command"` to run commands directly.

### Installing Dependencies

Dependencies are automatically installed when entering the nix shell via the `shellHook`. If you need to manually sync dependencies:

```bash
nix-shell --run "uv sync --all-extras --dev"
```

Or within an active nix shell:
```bash
uv sync --all-extras --dev
```

### Running the Server

To start the FastAPI development server:

```bash
nix-shell --run "uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-config log-config.json"
```

Or within an active nix shell:
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-config log-config.json
```

### Running Tests

**Important**: Tests must be run within the nix shell environment. You can either:

1. Enter the nix shell first, then run tests:
```bash
nix-shell
uv run pytest
```

2. Or run tests directly with nix-shell:
```bash
nix-shell --run "uv run pytest"
```

With coverage:

```bash
nix-shell --run "uv run pytest --cov=app --cov-report=html"
```

To run specific test files:
```bash
nix-shell --run "uv run pytest tests/api/test_health.py -v"
```

### Code Quality Tools

The project uses several code quality tools (run within nix shell):

- **Black** (formatting): `nix-shell --run "uv run black ."`
- **Ruff** (linting): `nix-shell --run "uv run ruff check ."`
- **isort** (import sorting): `nix-shell --run "uv run isort ."`
- **mypy** (type checking): `nix-shell --run "uv run mypy app"`

### Running All Checks

You can run all code quality checks at once:

```bash
nix-shell --run "uv run black . && uv run ruff check . && uv run isort . && uv run mypy app"
```

## Configuration

The application requires the following environment variables (can be set via `.env` file or environment):

### ViCare Configuration
- `CLIENT_ID` - ViCare OAuth client ID
- `EMAIL` - ViCare account email
- `PASSWORD` - ViCare account password

### Loxone Configuration (if applicable)
- `LOXONE_URL` - Loxone server URL
- `LOXONE_USER` - Loxone username
- `LOXONE_PASSWORD` - Loxone password

For more information on obtaining ViCare credentials, see [PyViCare](https://github.com/somm15/PyViCare#prerequisites).

## Project Structure

```
vicare-automation-server/
├── app/                    # Main application code
│   ├── api/               # API route handlers
│   │   ├── circuit.py    # Circuit control endpoints
│   │   ├── dhw.py        # Domestic hot water endpoints
│   │   ├── health.py     # Health check endpoints
│   │   ├── heatpump.py   # Heat pump endpoints
│   │   ├── heating.py    # Heating endpoints
│   │   ├── types.py      # Type definitions
│   │   └── ventilation.py # Ventilation endpoints
│   ├── dependencies.py   # FastAPI dependencies
│   ├── main.py          # FastAPI application entry point
│   └── settings.py      # Application settings
├── tests/                # Test suite
├── shell.nix            # Nix development environment
├── pyproject.toml       # Python project configuration
└── uv.lock              # Locked dependencies
```

## Development Workflow

1. **Enter the nix shell**: `nix-shell` or `direnv allow`
2. **Dependencies are automatically installed** via the shell hook
3. **Set up environment variables** in `.env` file
4. **Run the development server**:
   - Within nix shell: `uv run uvicorn app.main:app --reload`
   - Or directly: `nix-shell --run "uv run uvicorn app.main:app --reload"`
5. **Make changes** and the server will auto-reload
6. **Run tests**:
   - Within nix shell: `uv run pytest`
   - Or directly: `nix-shell --run "uv run pytest"`
7. **Format code**: `nix-shell --run "uv run black . && uv run isort ."`
8. **Check code quality**: `nix-shell --run "uv run ruff check . && uv run mypy app"`

## API Endpoints

The server exposes the following main API routers:
- `/circuit/*` - Circuit control
- `/dhw/*` - Domestic hot water control
- `/health/*` - Health checks
- `/heatpump/*` - Heat pump control
- `/ventilation/*` - Ventilation control

## Error Handling

The application includes comprehensive error tracking and handling for various PyViCare exceptions:
- Rate limit errors (429)
- Invalid configuration errors (424)
- Authentication errors (401)
- Not supported feature errors (405)
- Internal server errors (500)

All errors are tracked via the `request_tracker` utility in `app/request_tracking.py`, which provides:
- Request statistics (success/failure counts by status code)
- Last failure message with timestamp
- Thread-safe request tracking middleware
- Integration with health endpoint for status monitoring

## Notes for AI Agents

- **Nix Environment**: All commands (including tests) must be run within the nix shell environment
  - Use `nix-shell` to enter the environment, or
  - Use `nix-shell --run "command"` to run commands directly
  - The `uv` command is only available within the nix shell
- Always use `uv run` prefix for Python commands when not in an activated virtual environment
- The nix shell automatically handles dependency installation via `shellHook`
- Python 3.12+ is required (strictly <3.14)
- All dependencies are managed via `uv` and locked in `uv.lock`
- The project uses type hints and mypy for type checking
- Code formatting follows Black with 120 character line length
- Tests use pytest with coverage support
- Request statistics and error tracking are handled via `request_tracking.py` module
