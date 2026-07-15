# Day 10 — LangChain: Basics to Advanced

Five scripts, in increasing order of complexity: legacy chain classes → modern LCEL → a tool-using agent → a full RAG+agent Streamlit app → a multi-tool agentic RAG Streamlit app. All five call an LLM through [OpenRouter](https://openrouter.ai), so one API key covers the whole folder.

## Contents

| File | What it demonstrates |
|---|---|
| `simple_without_lcel-1.py` | Legacy chain classes — `LLMChain`, `SequentialChain`, `SimpleSequentialChain` |
| `simple_lcel (1).py` | The same three patterns rewritten with LCEL (`prompt \| llm \| parser`), plus a small blog-post pipeline example |
| `agent-simple-updated.py` | A minimal ReAct-style agent with a calculator tool and a text-length tool |
| `csv_1.py` | A Streamlit app: chat with a CSV (RAG + memory + structured output), summarize a CSV (map-reduce), analyze a CSV (pandas agent) |
| `updated-arag.py` | A Streamlit app: PDF RAG with fallback to a multi-tool agent (Wikipedia, ArXiv, Tavily web search) |
| `requirements.txt` | Pinned dependency list for this folder |
| `.env.example` | Template for the API keys below — copy to `.env` and fill in |
| `Colab Notebooks/README.md` | Links to companion notebooks if you'd rather run things in Colab |

## Prerequisites

- **Python 3.11 or 3.12.** Avoid whatever Python ships pre-installed on your OS (macOS's system Python is often 3.9, too old for these packages) and avoid installing the very newest Python release the day it comes out (heavy packages like `torch` and `faiss-cpu` usually take a few weeks to publish wheels for a new version, which forces a slow source build). 3.11 or 3.12 is the safe zone.
- An **OpenRouter** API key — [openrouter.ai](https://openrouter.ai) — required by all five scripts.
- A **Tavily** API key — [tavily.com](https://tavily.com) — required only by `updated-arag.py`'s web search tool.
- Optional: a **LangSmith** API key — [smith.langchain.com](https://smith.langchain.com) — only needed if you want request tracing.

## Setup

### macOS

1. Install Python 3.11 if you don't have it:
   ```bash
   brew install python@3.11
   ```
2. From the **project root** (one level up from this `Day_10` folder), create and activate a virtual environment:
   ```bash
   cd ai-accelerator-C7-main
   python3.11 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies from this folder:
   ```bash
   cd Day_10
   pip install -r requirements.txt
   ```
   This pulls in ~125 packages including PyTorch and Streamlit — expect a few minutes on first run.

   > If this step fails with a `pyexpat`, `libexpat`, or `ensurepip` error, that's a known Homebrew Python issue on some Macs, not a problem with this project — see [Troubleshooting](#troubleshooting).

4. Set up your API keys:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and fill in `OPENROUTER_API_KEY` and `TAVILY_API_KEY`. `LANGSMITH_API_KEY` is optional.

### Windows

1. Install Python 3.11 or 3.12 from [python.org/downloads](https://www.python.org/downloads/) — during install, check **"Add python.exe to PATH"**. (Or, if you use winget: `winget install Python.Python.3.11`.)
2. From the **project root** (one level up from this `Day_10` folder), create and activate a virtual environment.

   **PowerShell:**
   ```powershell
   cd ai-accelerator-C7-main
   py -3.11 -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
   **Command Prompt:**
   ```cmd
   cd ai-accelerator-C7-main
   py -3.11 -m venv .venv
   .venv\Scripts\activate.bat
   ```
   > If PowerShell refuses to run `Activate.ps1` with an execution-policy error, either use Command Prompt instead, or run once: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

3. Install dependencies:
   ```powershell
   cd Day_10
   pip install -r requirements.txt
   ```
4. Set up your API keys:
   ```powershell
   copy .env.example .env
   ```
   Open `.env` in a text editor and fill in the same keys as above.

> The macOS steps were run and verified end-to-end while writing this. The Windows steps follow standard Python tooling conventions but weren't run on an actual Windows machine — if a command doesn't match what you see, say so and it'll get fixed.

## Running & testing each file

Run these from inside `Day_10/`, with the virtual environment active (you'll see `(.venv)` in your prompt).

| # | File | Command |
|---|---|---|
| 1 | `simple_without_lcel-1.py` | `python simple_without_lcel-1.py` |
| 2 | `simple_lcel (1).py` | `python "simple_lcel (1).py"` *(quote it — the filename has a space)* |
| 3 | `agent-simple-updated.py` | `python agent-simple-updated.py` |
| 4 | `csv_1.py` | `streamlit run csv_1.py` |
| 5 | `updated-arag.py` | `streamlit run "updated-arag.py"` |

Scripts 1–3 print straight to the terminal and exit. Scripts 4–5 are Streamlit apps — they open a browser tab at `http://localhost:8501` and keep running until you stop them with `Ctrl+C` in the terminal. `updated-arag.py` needs **both** OpenRouter and Tavily keys pasted into its sidebar before it will do anything (it won't initialize with only one).

When you're done, leave the virtual environment with:
```
deactivate
```

## Troubleshooting

**macOS: venv creation fails with `ensurepip`, `pyexpat`, or `libexpat` in the error**
Some Homebrew Python builds link `pyexpat` against an older system `libexpat` that's missing a symbol recent expat versions added. Fix:
```bash
brew install expat
DYLD_LIBRARY_PATH=/opt/homebrew/opt/expat/lib python3.11 -m venv .venv
```
Then permanently add this line to the end of `.venv/bin/activate` so every future `source .venv/bin/activate` carries the fix forward automatically:
```
export DYLD_LIBRARY_PATH="/opt/homebrew/opt/expat/lib:${DYLD_LIBRARY_PATH:-}"
```

**Windows: PowerShell won't run `Activate.ps1`**
Use Command Prompt's `activate.bat` instead, or allow scripts once with `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`.

**`ModuleNotFoundError` for anything**
Your virtual environment probably isn't active. Re-run the `source .venv/bin/activate` (macOS) or `.venv\Scripts\activate` (Windows) line from Setup step 2.

**A script errors immediately asking for a key, or a Streamlit app does nothing when you click a button**
Check that `.env` has real values (not the empty placeholders from `.env.example`), and for the two Streamlit apps, check the sidebar — they read keys from there at runtime, not just from `.env`.

**`streamlit run csv_1.py`'s "Analyze CSV" mode errors with `NameError: create_pandas_dataframe_agent`**
Means `langchain-experimental` isn't installed — re-run `pip install -r requirements.txt` inside the active virtual environment.

**`streamlit run csv_1.py` or `streamlit run "updated-arag.py"` floods the terminal with `ModuleNotFoundError: No module named 'torchvision'` tracebacks from `transformers/models/.../image_processing_*.py`**
Not fatal — this is Streamlit's file watcher walking every loaded module to figure out what to watch for hot-reload, tripping over `transformers`' vision-model image processors (they import `torchvision` at load time; we never install it since nothing here handles images). `Day_10/.streamlit/config.toml` disables the watcher (`fileWatcherType = "none"`) so this never fires — if you don't see it, the fix is already in place. Trade-off: the app won't auto-reload when you save the file; use the "Rerun" button (or press `R`) or restart the server after edits.

## Models & keys — why this setup

Every script defaults to `openai/gpt-4.1-mini` via OpenRouter: cheap, fast, and matches or beats `gpt-4o` on most benchmarks, which matters when a whole classroom is making live calls back-to-back. `csv_1.py` exposes a model picker in its sidebar if you want to switch to something else (Claude, Llama, Grok, etc.) for comparison mid-demo.
