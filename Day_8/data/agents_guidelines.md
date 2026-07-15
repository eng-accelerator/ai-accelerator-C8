# Zangei Data
An operating system, distributed, to grow t2i, image dataset. With backend api (1), remote worker devices, google colab

Before doing incident-prone runtime, notebook, ingestion, Docker, or Tailscale work, read [docs/letter-of-shame.md](docs/letter-of-shame.md).

**Mothership**: This os runs distributed with single Mothership, with backend core and api and a frontend. Single per enviornment. MacMini M4 16GB RAM

**Remote Devices**: Hetzner, Vast.ai, Runpod, etc. instances — they register themselves with Mothership, and have their own backend and frontend running

**Collab Notebook**: even more ephemeral for smaller tasks, etc.


## Stack: Common
- docker. Managed using OrbStack on mac
- tailscale cli/sdk to ensure we register with tailscale and get our accessible API and frontend URLs
- backend outputs openapi docs using fastapi, on frontend use openapi-codegen or zod specific schema generator


## Stack: Backend
- uv, python (no pip!) using virtual enviornment [activate it]
- fastapi, pydantic schemas as membrane for each layer do not seralise/de-seralise line by line, sqlalchemy
- logging for workers, api, and frontend separately
- parquet, duckdb?, huggingface datasets, etc.
- With pydantic schema as membrane: model, repo [db io limit to here], interfaces [business logic], workers|routes|cli|scripts
- uv commands must run from project root
- postgresql database to power api backend on mothership, sqllite for remote devices


## Stack: Frotend
- bun. bun everything (no npm/npx/pnpm)
- nextjs, react, shadcn, tailwind
- reactquery, zod schemas everywhere as membrane between layers
- bun etc commands must run from project root
- Figtree variable font, utilisie variable font leverages. Dark mode only, OKLCH colour space


## Project Structure
...
[PROJECT ROOT]
├─ sample.env
├─ docs/
├─ logs/                
├─ tmp/
├─ scripts/
├─ backend/
│  ├─ main.py
│  ├─ schemas/             # use them everywhere. overuse them if needed
│  │  ├─ datasets/         # Organise all most folders in frontend and backend in domain/common sub-folder
│  │  ├─ ...
│  │  └─ samples/ 
│  │
│  ├─ migrations/          # Alembic migrations, db connection, etc.
│  ├─ models/              # SQLAlchemy
│  ├─ repos/ 
│  ├─ interfaces/ 
│  ├─ workers/ 
│  ├─ middleware/
│  ├─ tests/                  # Functional/integration testing covering major flows, organize in folders mimicing backend repo structure 
│  ├─ logging/ 
│  ├─ lib/                    # Subfolder organized functional code only. NO SIDEEFFECTS
│  └─ api/v1/                 # Route files here 
│
├─ frontend/
│  ├─ components/             # use them everywhere. overuse them if needed
│  │  ├─ charts/
│  │  ├─ ...
│  │  └─ ui/                  # Shadcn imports
│  ├─ hooks/                  
│  ├─ app/                    # NextS app, no "components" sub-folders here!
│  ├─ public/                 # Images, fonts, css, etc.
│  ├─ layouts/ 
│  ├─ logging/ 
│  ├─ ... 
│  └─ lib/                    # Subfolder organized functional code only. NO SIDEEFFECTS
│
├─ pyproject.toml
├─ package.json
├─ components.json
├─ tsconfig.json
├─ ...
└─ alembic.ini
...

# Files & Folders: Organizing Code
- Write your schemas in `backend/schemas`. Not in a route, repo, worker, or any other place! Stop littering! You don't need data class/data model, we use pydantic
- DO create 


## Code Standards

### Enviornments, Secrets & Enviornment Variables
- We'd have develop/staing/production/test defined in .env file at the root of the project (only 1 at the root of the proect)
- Maintain sample.role.env as if it were real. NEVER EVER read .env directly or indirectly. 
- .env file is real and exists at the project root. 
- The code must always use it and allow overriding values in .env with enviornment specific .env file like .env.test — the restriction is specifically for AI agents against the agents reading .env (Code using .env GOOD. Agent reading .env FORBIDDEN)
- User will maintain .env for you
- All variables/config/statics must be defined at .env at root. You MUST NOT create anotehr competing .env other than .env.test 
- Do not randomply put shit like this in code:
  ...
  # Absolute misaligned degenerate behaviour
  _TAILSCALE_RANGE = ipaddress.ip_network("100.64.0.0/10")
  _CLAIM_PREREQ_CACHE: dict[str, tuple[float, bool]] = {}
  ...

### Common Rules
- Do NOT write code comments unless some information is must to pass on to future humans but code does not make it obvious
- DO NO write code that hides/eats errors — let error surface and be logged properly
- DO NOT maintain backward compataibility/shims unless explicitly asked to, this software is not released so no need of that
- You MUST address me as Sidgai Sen
- DO NOT create a markdown document as docs unless you were explicitly asked to
- After you are done making all code changes, you MUST run lint (ruff for python), fix associated issues
- Validations MUST exists on FE and BE, both, FE should not ping BE / API till FE validations pass
- Keep calculations, formatting, etc. on backend — avoid overheads on frontend
- Write LESS code. Make it simpler, saner, and avoid over complicating it. Code is liability
- [C0003] DO NOT ADD HARDCODED fallbacks! No-fallbacks of API Keys, secrets, expected values in code! Code MUST throw if they are missing
- [C0009] DO NOT EXCEEED ANY FILE BEYOND 250 lines of code. Should you notice a file is getting there soon — STOP! Mention it and give an alternative plan. If you did it anyway please mention files that exceeed that threshold that needs to be refactored!
- Use zod & pydantic scehmas DO NOT line-by-line parse/validate data, seralisze/deseralise using schema as membrane everywhere, overuse them if needed
- Backend layer boundaries MUST use Pydantic request/result schemas. Read [docs/use/pydantic.md](docs/use/pydantic.md) before adding repo, interface, API, worker, cli, or script contracts.
- Repo queries MUST keep set logic in SQLAlchemy/Postgres. No Python ID-list/set pipelines or ORM mutation loops when SQL can do it. Read [docs/patterns/queries.md](docs/patterns/queries.md).


### Frontend
- useEffect() is forbidden, use props
- Make it super snappy, clicks/link/navigations should respond asap

### Backend
- Avoid python classes unless absolutely needed
- Workers, api routes, cli (future) must be super thin layer
- Alembic migration revision IDs MUST be ≤32 characters (alembic_version.version_num is varchar(32))
- Layers and separation of concern:
  - Models & Repos: SQLAlchemy models, and repos for db io. Repos should be thin layer with only db io, no business logic, validation hardcore
  - Interfaces: Business logic, validation, etc. called by workers, api routes, cli (future)
  - Lib: Functional code, no side effects, can be used by interfaces, workers, api routes, cli (future)
  - Schemas: Pydantic schemas as membrane for each layer do not seralise/de-seralise line by line, use them everywhere. overuse them if needed
  - Repo functions should expose schema-shaped inputs/results and keep query shaping in SQL, not Python loops.

