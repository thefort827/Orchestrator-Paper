# Orchestrator: Multi-Agent LLM Software Development

A meta-cognitive dispatcher for multi-agent LLM software development with enforced role separation, parallel execution, and silent delivery protocol.

## 📄 Paper

| File | Description |
|------|-------------|
| `paper/Orchestrator_Paper.docx` | Formatted Word document |
| `paper/main.tex` | LaTeX source (arXiv format) |
| `paper/figures/` | 7 experiment figures |

## 🏗️ Orchestrator-Team System

A multi-agent framework where the Orchestrator analyzes requirements, generates API contracts, and dispatches specialized sub-agents in parallel.

### Architecture

```
User Request → Orchestrator → Architect (API Contract)
                              ↓
                    ┌─────────┴─────────┐
                    │                   │
              Frontend Dev        Backend Dev
              (parallel)          (parallel)
                    │                   │
                    └─────────┬─────────┘
                              ↓
                        QA Validation
```

### Key Features

- **Enforced Role Separation**: Orchestrator cannot write code
- **Parallel Execution**: `asyncio.gather()` for concurrent sub-agents
- **Silent Delivery Protocol**: JSON summaries instead of verbose reports
- **API Contract as Shared Specification**: Architect-first planning
- **Forced Executor Binding**: Each agent uses optimal tools

### Project Structure

```
orchestrator-team/
├── core/           # Agent system (agent.py, chat_room.py, task_scheduler.py)
├── agents/         # Role definitions (orchestrator, frontend_dev, backend_dev, ...)
├── tools/          # Tool implementations (code_executor, cline_runner, ...)
├── protocols/      # Message, Task, CompletionSummary protocols
├── config.py       # Agent configuration
└── run_benchmark.py
```

### Quick Start

```bash
cd orchestrator-team
pip install openai python-dotenv scikit-learn
cp ../.env.example .env
# Edit .env with your API key
python run_benchmark.py
```

## 🌆 Smart City Digital Twin

A graduation project demonstrating the Orchestrator system with a smart city digital twin featuring self-evolution capabilities.

### Features

- **3D City Visualization**: Three.js rendering (buildings, roads, sensors)
- **Real-time Dashboard**: Traffic, air quality, energy monitoring
- **Self-Evolution Engine**: Anomaly detection, traffic optimization, energy balancing
- **WebSocket**: Real-time sensor data streaming

### Tech Stack

- **Frontend**: HTML5 + Three.js + Chart.js + WebSocket
- **Backend**: Python FastAPI + SQLite
- **AI**: scikit-learn + numpy (Isolation Forest, K-Means)

### Quick Start

```bash
cd smart-city/src/backend
pip install -r requirements.txt
python main.py
# Open http://localhost:8000
```

## 📊 Benchmark Results

| Metric | Single Cline | Orchestrator (orig) | Orchestrator (opt) |
|--------|:------------|:-------------------|:-------------------|
| Status | failed | completed | completed |
| Time (s) | 302 | 474 | 575 |
| Total Tokens | 270,880 | 247,006 | 289,069 |
| Output Files | 5 | 16 | 10 |
| Token Efficiency | 0.081 B/t | 0.200 B/t | ~0.14 B/t |

## 🔧 API Configuration

Supports any OpenAI-compatible API. Configure via `.env`:

```bash
# DeepSeek
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com

# MiMo Token Plan
DEEPSEEK_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
```

## 📝 License

MIT License

## ✉️ Contact

- **GitHub**: [thefort827](https://github.com/thefort827)
- **Email**: 1759799340@qq.com
