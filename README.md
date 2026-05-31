# Orchestrator: Multi-Agent LLM Software Development

A meta-cognitive dispatcher for multi-agent LLM software development with enforced role separation, parallel execution, and silent delivery protocol.

## Overview

Orchestrator is a research framework that addresses the fundamental limitation of single-agent LLM systems: the inability to handle full-stack software development tasks spanning multiple domains. By decomposing abstract requirements into domain-specific tasks, generating API contracts as shared specifications, and orchestrating parallel execution of specialized sub-agents, Orchestrator achieves 100% task completion across three benchmark tasks while single-agent baselines fail entirely.

### Key Innovation

The Orchestrator itself **cannot write code**. It serves as a meta-cognitive dispatcher that:
1. Analyzes requirements and identifies required domains
2. Generates API contracts as shared specifications via an Architect sub-agent
3. Dispatches Frontend and Backend developers in parallel
4. Validates output completeness and contract compliance

This enforced role separation ensures clean separation of planning and execution, preventing the coordination failures common in free-form multi-agent systems.

## System Architecture

```
User Request → Orchestrator (Meta-Cognitive Dispatcher)
                    ↓
              Architect (API Contract Generation)
                    ↓
        ┌───────────┴───────────┐
        │                       │
  Frontend Dev              Backend Dev
  (cline_runner)           (code_executor)
  [PARALLEL EXECUTION]
        │                       │
        └───────────┬───────────┘
                    ↓
            QA Validation + File Checking
```

### Three-Phase Execution Model

| Phase | Description | Duration |
|-------|-------------|----------|
| **Phase A: Planning** | Orchestrator dispatches Architect to generate API contract | ~2 min |
| **Phase B: Parallel Dev** | Frontend and Backend execute simultaneously via `asyncio.gather()` | ~2 min |
| **Phase C: Verification** | System validates file completeness and contract compliance | ~1 min |

### Five Key Innovations

1. **Abstract Requirement Decomposition**: High-level requirements → domain-specific task packages
2. **API Contract as Shared Specification**: Formal interface definition before development
3. **Parallel Execution**: `asyncio.gather()` for concurrent sub-agents (26% time savings)
4. **Silent Delivery Protocol**: JSON summaries only (25% token reduction)
5. **Enforced Role Separation**: Orchestrator cannot call file-operation tools

## Project Structure

```
Orchestrator-Paper/
├── paper/                          # Research paper and figures
│   ├── main.tex                    # LaTeX source (arXiv format)
│   ├── Orchestrator_Paper.docx     # Formatted Word document
│   ├── generate_figures.py         # Figure generation (12 figures + 2 tables)
│   ├── figures/                    # Generated experiment figures
│   │   ├── fig1_architecture.png
│   │   ├── fig2_execution_flow.png
│   │   ├── fig3_token_comparison.png
│   │   ├── fig4_token_efficiency.png
│   │   ├── fig5_time_breakdown.png
│   │   ├── fig6_file_comparison.png
│   │   ├── fig7_ablation_parallel.png
│   │   ├── fig8_ablation_silent.png
│   │   ├── fig9_ablation_contract.png
│   │   ├── fig10_scaling.png
│   │   ├── table1_benchmark.png
│   │   └── table2_ablation.png
│   ├── to_word.py                  # LaTeX → Word converter
│   └── write_sections.py           # Section writer utility
├── orchestrator-team/              # Core multi-agent framework
│   ├── core/                       # Agent system
│   │   ├── agent.py                # BaseAgent with parallel execution
│   │   ├── chat_room.py            # Inter-agent communication
│   │   ├── llm.py                  # LLM client wrapper
│   │   ├── memory.py               # Shared and private memory
│   │   ├── task_queue.py           # Task queue management
│   │   └── task_scheduler.py       # Task assignment and tracking
│   ├── agents/                     # Role definitions
│   │   ├── orchestrator.py         # Meta-cognitive dispatcher
│   │   ├── architect.py            # API contract generator
│   │   ├── frontend_dev.py         # Frontend specialist
│   │   ├── backend_dev.py          # Backend specialist
│   │   ├── qa_engineer.py          # Quality assurance
│   │   └── devops.py               # Deployment and CI/CD
│   ├── tools/                      # Tool implementations
│   │   ├── code_executor.py        # Code execution tool
│   │   ├── cline_runner.py         # Cline CLI integration
│   │   ├── doc_generator.py        # Document generation
│   │   ├── task_manager.py         # Task management tool
│   │   └── validators.py           # Output validation
│   ├── protocols/                  # Data structures
│   │   ├── message.py              # Message protocol
│   │   ├── task.py                 # Task protocol
│   │   ├── completion_summary.py   # Completion summary
│   │   └── role_library.py         # Role definitions
│   ├── benchmarks/                 # Benchmark suite
│   │   ├── task_definitions.py     # 3 benchmark tasks
│   │   └── runner.py               # Experiment runner with ablation configs
│   ├── config.py                   # Agent configuration
│   └── tests/                      # Test suite
├── smart-city/                     # Demo application
│   └── src/backend/                # Smart city digital twin
├── .env.example                    # Environment variables template
└── README.md                       # This file
```

## Benchmark Tasks

We evaluate Orchestrator on three full-stack benchmarks of increasing complexity:

| Task | Complexity | Files | Domains | Endpoints |
|------|:----------:|:-----:|:-------:|:---------:|
| **Blog System** | 3/10 | 8 | 4 | 10 |
| **E-commerce Store** | 6/10 | 15 | 5 | 15 |
| **Real-time Chat App** | 9/10 | 19 | 7 | 14 |

### Blog System (Simple)
- Personal blog with authentication, CRUD posts, comments, tag filtering
- Frontend: responsive HTML/CSS/JS
- Backend: Flask REST API with SQLite
- 8 required files, 10 API endpoints

### E-commerce Store (Medium)
- Product catalog, shopping cart, checkout, admin dashboard
- Frontend: React-like SPA with product grid, cart sidebar, admin panel
- Backend: FastAPI with PostgreSQL, JWT authentication
- 15 required files, 15 API endpoints

### Real-time Chat App (Complex)
- WebSocket messaging, group chats, file sharing, message search, user presence
- Frontend: HTML5 with WebSocket client, chat UI, admin panel
- Backend: FastAPI + WebSocket, SQLAlchemy, Redis for presence
- 19 required files, 14 API endpoints

## Experimental Results

### Task Completion

| Configuration | Blog | E-commerce | Chat App |
|---------------|:----:|:----------:|:--------:|
| Single Agent | failed (5/8 files) | failed (7/15) | failed (8/19) |
| **Orchestrator (Full)** | **100% (8/8)** | **100% (15/15)** | **100% (19/19)** |
| No Parallel | 100% (8/8) | 100% (15/15) | 100% (19/19) |
| No Silent | 100% (8/8) | 100% (15/15) | 100% (19/19) |
| No Contract | 80% (7/8) | 60% (12/15) | 40% (15/19) |

### Ablation Study Results (Blog System, n=5)

| Configuration | Time (s) | Tokens | Token Efficiency | Success Rate |
|---------------|:--------:|:------:|:----------------:|:------------:|
| Full Orchestrator | 575±18 | 289k±7k | 0.138 B/t | 100% |
| − Parallel Exec | 780±22 | 275k±7k | 0.145 B/t | 100% |
| − Silent Delivery | 610±20 | 385k±10k | 0.104 B/t | 100% |
| − API Contract | 620±25 | 310k±9k | 0.129 B/t | 80% |
| Single Agent | 302±12 | 270k±8k | 0.081 B/t | 0% |

### Key Findings

1. **Parallel Execution**: 26% time savings (575s → 780s) with no quality degradation
2. **Silent Delivery**: 25% token reduction (289k → 385k) with identical output
3. **API Contract**: 43% improvement in endpoint matching accuracy
4. **Scaling**: Orchestrator advantage grows with task complexity

### Figures

| Figure | Description |
|--------|-------------|
| Fig 1 | System architecture diagram |
| Fig 2 | Three-phase execution flow |
| Fig 3 | Token consumption comparison (with error bars) |
| Fig 4 | Token efficiency comparison |
| Fig 5 | Time breakdown by task complexity |
| Fig 6 | Output file completeness comparison |
| Fig 7 | Ablation: parallel execution impact |
| Fig 8 | Ablation: silent delivery impact |
| Fig 9 | Ablation: API contract impact |
| Fig 10 | Task complexity scaling behavior |
| Table 1 | Full benchmark results |
| Table 2 | Ablation study summary |

## Quick Start

### Prerequisites

- Python 3.10+
- OpenAI-compatible API key (DeepSeek, MiMo, etc.)

### Installation

```bash
git clone https://github.com/thefort827/Orchestrator-Paper.git
cd Orchestrator-Paper/orchestrator-team
pip install openai python-dotenv scikit-learn
```

### Configuration

```bash
cp ../.env.example .env
# Edit .env with your API key
```

### Running the System

```python
import asyncio
from core.agent import BaseAgent, run_parallel
from core.memory import Memory
from core.chat_room import ChatRoom
from core.task_scheduler import TaskScheduler
from agents.orchestrator import create_orchestrator
from agents.architect import create_architect
from agents.frontend_dev import create_frontend_dev
from agents.backend_dev import create_backend_dev

async def main():
    memory = Memory()
    chat_room = ChatRoom(memory)
    task_scheduler = TaskScheduler(memory, chat_room)

    # Create agents
    orchestrator = create_orchestrator(llm_config, memory, chat_room, task_scheduler)
    architect = create_architect(llm_config, memory, chat_room, task_scheduler)
    frontend = create_frontend_dev(llm_config, memory, chat_room, task_scheduler)
    backend = create_backend_dev(llm_config, memory, chat_room, task_scheduler)

    # Register agents
    for agent in [orchestrator, architect, frontend, backend]:
        chat_room.register(agent)

    # Send request to orchestrator
    orchestrator.receive(Message(
        sender="user",
        content="Build a personal blog with authentication and CRUD posts"
    ))

    # Execute three-phase workflow
    orchestrator.reply()

asyncio.run(main())
```

### Generating Figures

```bash
cd paper
python generate_figures.py
```

## API Configuration

Supports any OpenAI-compatible API. Configure via `.env`:

```bash
# DeepSeek
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com

# MiMo Token Plan
DEEPSEEK_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
```

### Model Configuration

Each agent uses optimized LLM parameters:

| Agent | Temperature | Max Tokens |
|-------|:-----------:|:----------:|
| Orchestrator | 0.3 | 4096 |
| Architect | 0.2 | 8192 |
| Frontend Dev | 0.4 | 8192 |
| Backend Dev | 0.3 | 8192 |
| QA Engineer | 0.2 | 4096 |
| DevOps | 0.3 | 4096 |

## Reproducing Experiments

To reproduce the benchmark results:

1. Configure your API key in `.env`
2. Run the benchmark suite:
```bash
cd orchestrator-team
python -m benchmarks.runner
```
3. Results are exported to `results/` as CSV and JSON files
4. Generate figures:
```bash
cd paper
python generate_figures.py
```

## Citation

If you use Orchestrator in your research, please cite:

```bibtex
@article{thefort2026orchestrator,
  title={Orchestrator: A Meta-Cognitive Dispatcher for Multi-Agent LLM Software Development},
  author={thefort},
  journal={arXiv preprint},
  year={2026}
}
```

## License

MIT License

## Contact

- **GitHub**: [thefort827](https://github.com/thefort827)
- **Email**: 1759799340@qq.com
