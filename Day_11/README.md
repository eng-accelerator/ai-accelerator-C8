# Day 11 — LangGraph from Scratch

Learn the three core ideas behind [LangGraph](https://github.com/langchain-ai/langgraph)
— **State**, **Nodes**, and **Edges** — by running small, heavily commented examples
and watching data flow through a graph. Then see the same ideas *visually* in
LangGraph Studio. Verified on **LangGraph 1.x**.

## The core idea in one picture

```text
            input
              |
              v
   +--------- STATE (a TypedDict = shared memory) ---------+
   |   START -> node -> node -> (router?) -> node -> END    |
   +-------------------------------------------------------+
              |
              v
        final state
```

- **State** — a `TypedDict` that flows through the whole graph. Each node gets it and
  returns a **partial** dict that LangGraph **merges** back in.
- **Nodes** — plain functions `(state) -> partial state dict`. (An LLM node is just a node.)
- **Edges** — the wiring: `add_edge(A, B)`, the `START`/`END` sentinels, and
  **conditional edges** (a router function returns the name of the next node).
- **Lifecycle** — `StateGraph(State)` → `add_node` → `add_edge`/conditional → `compile()` → `invoke()`.

---

## What's in this folder

| File | What it is |
|---|---|
| `simple_graph.py` | **Start here.** The smallest complete graph: state, three nodes, a conditional edge (router), `START`/`END`, `compile()`, `invoke()`. The greeting branch is a plain node; the search branch calls an LLM via OpenRouter (works without a key too). |
| `state_flow_demo.py` | **Interactive.** A console tool that prints every hand-off as data moves through the graph — the state going **IN** to each node, the **partial** it returns **OUT**, the **MERGE** back into state, which **EDGE** was taken, and the **ROUTER**'s decision. Step through it one node at a time. |
| `memory_demo.py` | **Interactive.** How a graph *remembers*: a checkpointer (`InMemorySaver`) + a `thread_id` persist state across turns. Same `thread_id` resumes the saved memory; a different one starts fresh. With an API key it replies naturally using what it remembered. |
| `agent-eval.py` | **A real tool-using agent + LangSmith evaluations.** An `agent ⇄ tools` loop (add/multiply tools) plus three evaluators — exact-match, **LLM-as-a-judge**, and trajectory — run over a dataset. The agent runs with just an OpenRouter key; the evaluations need a (free) LangSmith key. |
| `langsmith-simple.py` | **The simplest LangSmith tracing demo.** Two `@traceable` steps form a pipeline (OpenAI → Claude, both via OpenRouter) that shows up as a trace tree at smith.langchain.com. Runs with an OpenRouter key; add a LangSmith key to see the trace. |
| `storygen.py` | **A bigger app (Streamlit).** A multi-node LangGraph that generates an interactive, choose-your-own-adventure story — shows how far the same State/Nodes/Edges idea scales. Needs an OpenRouter key; run with `streamlit run storygen.py`. |
| `studio/agent.py` | An **interactive storyteller** (same idea as `storygen.py`) built on `MessagesState`, designed to be **watched — and chatted with — in LangGraph Studio**: `START →(new or continue?)→ begin / continue → END`. Because the state has a `messages` key, Studio's **Chat tab works**. Runs with no API key (canned scene); set `OPENROUTER_API_KEY` in `studio/.env` for a real AI story. |
| `studio/langgraph.json` | The manifest that tells `langgraph dev` which graph to load. |
| `studio/.env.example` | Optional key template for the Studio graph's LLM branch. |
| `lesson.html` | A self-contained slide deck for the session. Just open it in any browser (arrow keys / space to navigate). |
| `requirements.txt` | The Python packages to install. |
| `.env.example` | Template for the optional OpenRouter API key. |

> **No API key required** to learn the concepts — `state_flow_demo.py`, `memory_demo.py`,
> and the Studio graph all run fully offline. An **OpenRouter** key enables the LLM replies
> (`simple_graph.py`'s search branch, `memory_demo.py`, `agent-eval.py`, `langsmith-simple.py`,
> `storygen.py`). The **LangSmith** demos (`agent-eval.py`, `langsmith-simple.py`) still run
> with just an OpenRouter key — add a free `LANGSMITH_API_KEY` only to see traces/evals at
> [smith.langchain.com](https://smith.langchain.com).

---

## Prerequisites

- **Python 3.11 required** (3.10+ works; **3.9 does NOT** — LangGraph 1.x needs 3.10+).
  Check what you have:
  - macOS/Linux: `python3.11 --version`  (and `python3 --version`)
  - Windows: `py -3.11 --version`
- ⚠️ **macOS ships an old `python3` (often 3.9).** If `python3 --version` is below 3.10,
  do **not** use plain `python3` below — use `python3.11` explicitly. Install it with
  [Homebrew](https://brew.sh): `brew install python@3.11`.
- Otherwise download 3.11 from [python.org](https://www.python.org/downloads/)
  (on Windows, tick **"Add Python to PATH"** in the installer).

---

## Setup — macOS / Linux

```bash
# 1. Go into this folder
cd Day_11

# 2. Create a virtual environment (isolated Python just for this project)
#    Use python3.11 explicitly — plain `python3` on macOS is often 3.9 (too old).
python3.11 -m venv .venv

# 3. Activate it
source .venv/bin/activate
#    (your prompt now starts with "(.venv)")

# 4. Install the packages
pip install --upgrade pip
pip install -r requirements.txt
```

## Setup — Windows

**PowerShell** (the default terminal in modern Windows):

```powershell
# 1. Go into this folder
cd Day_11

# 2. Create a virtual environment (pin 3.11 so you don't get an older Python)
py -3.11 -m venv .venv

# 3. Activate it
.venv\Scripts\Activate.ps1
#    If you get a "running scripts is disabled" error, run this once, then retry:
#    Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

# 4. Install the packages
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Command Prompt (cmd.exe)** — same, except the activate step is:
```cmd
.venv\Scripts\activate.bat
```

> After activating (either OS), your terminal uses this project's Python, so you can
> just type `python ...` and `langgraph ...` without any path prefix. Type `deactivate`
> to leave the environment.

---

## (Optional) Add an API key for the LLM parts

Only needed for `simple_graph.py`'s search branch and `memory_demo.py`'s natural replies.
Everything else runs without it.

1. Get a key from [openrouter.ai/keys](https://openrouter.ai/keys).
2. Copy the template to a real `.env` file:
   - macOS/Linux: `cp .env.example .env`
   - Windows (PowerShell): `Copy-Item .env.example .env`
3. Open `.env` and set:
   ```
   OPENROUTER_API_KEY=sk-or-...your-key...
   OPENROUTER_MODEL=openai/gpt-4.1-mini
   ```
The scripts read this automatically. **Never commit your real `.env`** — it's gitignored.

---

## Run the examples

Make sure your virtual environment is activated first (see Setup). Then:

```bash
# 1) Fundamentals — prints the final state after a run
python simple_graph.py

# 2) Watch state move through the graph, node by node (interactive)
python state_flow_demo.py
#    Controls: type a message; :step / :auto toggle stepping; :stream <msg>;
#    :q / quit / exit to leave.

# 3) Memory — a graph that remembers across turns (interactive)
python memory_demo.py
#    Controls: type messages; :user <name> switches memory thread;
#    :mem shows what's remembered; :q / quit / exit to leave.
```

On Windows, if you did **not** activate the venv, prefix with `.venv\Scripts\python.exe`
instead of `python` (macOS/Linux: `.venv/bin/python`).

> **Tip:** both interactive demos also run non-interactively (a scripted auto-demo) if
> you pipe empty input, e.g. `python memory_demo.py < /dev/null` (macOS/Linux) or
> `echo. | python memory_demo.py` (Windows).

---

## LangGraph Studio (the local visual builder)

Watch a graph execute node-by-node in your browser, inspect the state as it fills in,
and use threads / time-travel. Requires no API key for the demo graph.

```bash
# from inside Day_11, with the venv activated:
cd studio
langgraph dev
```
If the venv is **not** activated, use the full path to the CLI instead:
- macOS/Linux: `../.venv/bin/langgraph dev`
- Windows (PowerShell): `..\.venv\Scripts\langgraph dev`

This starts a local server at **http://127.0.0.1:2024** and opens the Studio UI in your
browser. Because the graph is built on `MessagesState`, the **Chat tab works** — open it
and **type your move** ("start a fantasy adventure", then "I take the forest path"), and
the narrator continues the story. Watch the `messages` list grow in the state inspector;
each turn is saved to the thread, so the story keeps going. (Set `OPENROUTER_API_KEY` in
`studio/.env` for a real AI-written story; without it you get a short canned scene.)

---

## The slide deck

`lesson.html` is a self-contained offline deck for the session. Open it in any browser:
- macOS: `open lesson.html`
- Windows: `start lesson.html`
- Linux: `xdg-open lesson.html`

Navigate with the **arrow keys** or **space**; press **f** for fullscreen.

---

## Troubleshooting

- **`python: command not found`** — on macOS/Linux use `python3`; on Windows use `py`.
- **Python is older than 3.10** — LangGraph 1.x needs 3.10+. Install a newer Python and
  recreate the `.venv`.
- **`langgraph: command not found`** — the CLI lives inside the venv. Activate the venv
  first, or use the full path (`.venv/bin/langgraph` on macOS/Linux,
  `.venv\Scripts\langgraph` on Windows).
- **PowerShell won't activate the venv** ("running scripts is disabled") — run
  `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then activate again.
- **LLM / network errors** on the search or memory replies — check that
  `OPENROUTER_API_KEY` is set in `.env` and that your OpenRouter account has credit. The
  scripts fall back to offline behavior if there's no key, so they never hard-fail.
