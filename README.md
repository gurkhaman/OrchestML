# OrchestML
LLM-based Continuous Integration Tool for Automated ML Service Compositions


## 1. Quick Start (Recommended)

### 1. Clone and setup
`git clone <repo-url>`

`cd OrchestML`

### 2. Start backend services

`cd orchestrator && uv sync`

`source .venv/bin/activate && uv run python main.py`

`cd ../repository-service && && uv sync`

`source .venv/bin/activate && uv run python main.py`


### 3. Start frontend
`cd ../composureboard && bun install && bun run dev`

Access UI at http://localhost:5173

## 2. Prerequisites

• uv package manager

• Node.js 18+ and bun (for frontend)

• Docker & Docker Compose (optional, for containerized deployment)

• OpenAI API Key (add .env file in both orchestrator and repository-service )


