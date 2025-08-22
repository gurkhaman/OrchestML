FROM python:3.13.6-slim
WORKDIR /app
COPY repository-service/ .
RUN pip install uv && uv sync
CMD ["uv", "run", "python", "main.py"]