# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:0.8.17-python3.8-alpine

# Copy the application into the container.
COPY . /app

# Install the application dependencies.
WORKDIR /app
RUN uv sync --locked --no-cache

# Run the application.
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80", "--log-config", "log-config.json"]
