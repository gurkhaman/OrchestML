FROM python:3.13.6-slim
WORKDIR /app

# Copy dependency files first for better layer caching
COPY repository-service/pyproject.toml ./
RUN pip install uv && uv sync --no-dev

# Copy source code (will be overridden by volume mount in development)
COPY repository-service/ .
CMD ["uv", "run", "python", "main.py"]