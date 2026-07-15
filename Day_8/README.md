# EduTech LLM Evals
Built on [InspectAI](https://inspect.aisi.org.uk/)
Two Inspect AI evals comparing GPT-5.4, Sonnet 4.6, Gemini 3.1 Pro, and Grok across coding and critique tasks. All models accessed via OpenRouter.

## Setup

```bash
pip install inspect-ai openai
cp .env.example .env  # add your OpenRouter key
```

For Task 1 (landing page), you also need **one** of:
- **Docker**: Docker Desktop running
- **Modal**: `pip install modal && modal token new`

## Tasks

| Task | File | What it tests |
|---|---|---|
| Landing Page | `task_landing_page.py` | Build a full interactive landing page in a sandbox (bash + editor tools) |
| Code Critique | `task_code_critique.py` | Review a buggy Python agent against AGENTS.md guidelines |

## Run

```bash
# Single task, single model
inspect eval task_code_critique.py --model openai/anthropic/claude-sonnet-4-6 
inspect eval task_landing_page.py --model openai/openai/gpt-5.4 -T sandbox_type=docker

# All models, all tasks
./run_evals.sh docker           # or: ./run_evals.sh modal
./run_evals.sh docker code_critique  # one task only

# View results
inspect view
```

## Scoring

**Task 1** — LLM judge scores 6 criteria (HTML structure, design, content relevance, interactivity, responsiveness, code quality). Grade: CORRECT >= 8/12.

**Task 2** — LLM judge checks detection of 12 known issues (D1: identified, D2: explained why, D3: fix proposed) plus 4 quality criteria. Grade: CORRECT >= 0.7 overall.
