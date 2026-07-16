# LangGraph Studio — Instructor Guide

A walkthrough for running the **local LangGraph Studio** live in class. The demo
graph is an **interactive storyteller** (a choose-your-own-adventure narrator)
built on `MessagesState`, so Studio's **Chat** tab works — you type your move and
the story continues. It needs **no API key** (you get a short canned scene
without one), so it works offline in the room.

## What this is

`langgraph dev` starts a local, in-memory LangGraph **API server** with hot
reloading, and (by default) opens **LangGraph Studio** in your browser pointed
at that server. Studio is the visual builder/runner: you see the graph's
topology, watch it execute node-by-node, inspect state, edit inputs, and
time-travel across runs.

> `langgraph dev` is for **local development**. For deployment you'd use
> `langgraph build` / `langgraph up` (Docker images) or **LangGraph Platform**.
> Those are out of scope for this session.

## Install (already done here)

The CLI ships in `requirements.txt` as `langgraph-cli[inmem]` (the `inmem`
extra pulls in the in-memory dev server, `langgraph-api`). It's installed in the
project venv at `.venv`. The in-mem server requires **Python 3.11+** (we use 3.11).

## Launch command

```bash
cd /Users/takshitmathur/Desktop/Projects/langgraph-basics/studio
/Users/takshitmathur/Desktop/Projects/langgraph-basics/.venv/bin/langgraph dev
```

What happens:
- Server binds to **http://127.0.0.1:2024** (default host `127.0.0.1`, port `2024`).
- A browser tab opens **LangGraph Studio** pointed at the local server, i.e.
  `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`.
- API docs are at **http://127.0.0.1:2024/docs**.

Handy flags (verified against the CLI source):
- `--no-browser` — start the server but don't auto-open Studio.
- `--port 8000` — use a different port.
- `--host 0.0.0.0` — bind all interfaces (only on trusted networks).
- `--no-reload` — disable hot reload.
- `--tunnel` — expose via a public Cloudflare tunnel (useful if a browser/network
  blocks `localhost`).
- `--config path/to/langgraph.json` — point at a different manifest (defaults to
  `langgraph.json` in the current directory).

Stop the server with `Ctrl+C`.

## The manifest: `langgraph.json`

This file is how the CLI/Studio discovers your graph. Ours:

```json
{
  "$schema": "https://langgra.ph/schema.json",
  "dependencies": ["."],
  "graphs": {
    "agent": "./agent.py:graph"
  },
  "env": ".env"
}
```

Key meanings (from the CLI config schema):
- **`dependencies`** — packages/local paths to make importable. `"."` means
  "this folder is a dependency," so `agent.py` is importable and any local
  `requirements.txt` is honored.
- **`graphs`** — maps a graph id (`agent`) to `path/to/file.py:variable`. We
  point at the module-level compiled graph `graph` in `agent.py`.
- **`env`** — path to an env file (`.env`). Ours is empty by default; the graph
  runs without it. (`.env.example` documents the optional `OPENROUTER_API_KEY`.)

## What students will SEE in Studio

1. **Graph topology** — the nodes and edges as a diagram. From `START` a
   **conditional edge** (the `route` router) forks to one of two nodes, each of
   which then goes straight to `END`:
   `START → {begin | continue} → END`. `begin` writes the opening scene; every
   later turn goes through `continue`.
2. **The Chat tab WORKS** — because the state is `MessagesState` (it has a
   `messages` key), Studio enables its chat view. **Type your move in the Chat
   tab** (e.g. "I take the forest path") and the narrator continues the story.
   This is the main thing to demo.
3. **Node-by-node execution** — nodes light up as they run; the very first turn
   runs `begin`, every reply after that runs `continue`. You can watch the
   router send each turn down the right branch.
4. **State inspector** — watch the `messages` list **GROW** turn by turn. Each
   node returns one new message and the built-in `add_messages` reducer
   *appends* it, so you can literally see the conversation (your moves + the
   narrator's scenes) stacking up.
5. **Threads = the story continuing** — the dev server adds persistence (a
   checkpointer) automatically, so each conversation is a **thread**. That
   thread is what keeps the story going across turns; start a new thread to
   begin a brand-new adventure. (Note: `agent.py` does NOT pass its own
   checkpointer — the dev server supplies one.)

## How the demo maps to the concepts

The graph in `studio/agent.py` is the same idea as `storygen.py`, re-expressed
as a chat graph so you can talk to it in Studio:
- **State** — `MessagesState`, a built-in TypedDict whose single field is
  `messages: Annotated[list, add_messages]`. The `add_messages` reducer
  **appends** each new message instead of replacing the list — that's why the
  conversation accumulates.
- **Nodes** — plain functions `state -> {"messages": [<one new message>]}`.
  `begin_story` writes the opening scene; `continue_story` continues from the
  player's latest message. Both call a shared `_narrate(...)` helper.
- **Conditional edge from START** — `route(state)` returns `"continue"` if the
  narrator (an `AIMessage`) has already spoken, otherwise `"begin"`. It's wired
  as `add_conditional_edges(START, route, {...})`, so the branch decision is the
  graph's entry point.
- **START / END** — modern idiom: the conditional edge starts at `START`, and
  both nodes end with `add_edge("begin", END)` / `add_edge("continue", END)`.
- **compile()** — turns the builder into the runnable `graph` Studio imports.
  No checkpointer is passed; the dev server's thread persistence is what keeps
  the story going.
- **Optional LLM path** — `_narrate` uses `langchain_openai.ChatOpenAI` (via
  OpenRouter) **only if** `OPENROUTER_API_KEY` is set; otherwise it returns a
  short canned scene so the live demo always works. Set `OPENROUTER_API_KEY`
  (and optionally `OPENROUTER_MODEL`, default `openai/gpt-4o-mini`) in
  `studio/.env` for a real, AI-written story.

## Quick sanity check (no Studio needed)

```bash
cd /Users/takshitmathur/Desktop/Projects/langgraph-basics/studio
/Users/takshitmathur/Desktop/Projects/langgraph-basics/.venv/bin/python -c "import agent; print(type(agent.graph))"
# or run the built-in smoke test:
/Users/takshitmathur/Desktop/Projects/langgraph-basics/.venv/bin/python agent.py
```
