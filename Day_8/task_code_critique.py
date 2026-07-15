"""
Task 2: Code critique — given AGENTS.md guidelines and a Python file,
produce a structured critique with issues, explanations, and fixes.

Scored by LLM judge with deterministic criteria checklist.

Usage:
    inspect eval task_code_critique.py --model openai/anthropic/claude-sonnet-4-6
    inspect eval task_code_critique.py -T grader_model=openai/openai/gpt-5.4
"""

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import (
    Score,
    Target,
    accuracy,
    scorer,
    CORRECT,
    INCORRECT,
    PARTIAL,
)
from inspect_ai.solver import generate, system_message
from inspect_ai.model import GenerateConfig, get_model

import os


KNOWN_ISSUES = [
    {
        "id": "loose_function_boundary",
        "category": "Code Quality",
        "description": "Function accepts primitive input and returns a loose dict[str, int]. "
        "There is no Pydantic request/result schema, so validation, serialization, "
        "and output shape guarantees are weak.",
    },
    {
        "id": "python_side_id_shaping",
        "category": "Performance",
        "description": "The function repeatedly pulls IDs into Python lists and sets, then sends "
        "them back into SQL queries. This creates unnecessary memory pressure and "
        "extra database round trips.",
    },
    {
        "id": "too_many_sequential_queries",
        "category": "Performance",
        "description": "The reset operation is implemented as many individual select/delete/update "
        "queries. Related set operations should be composed into a SQLAlchemy query "
        "pipeline using CTEs, subqueries, joins, and anti-joins.",
    },
    {
        "id": "orphan_detection_outside_query_pipeline",
        "category": "Correctness",
        "description": "Orphan image detection is delegated to _orphaned_image_ids after deleting "
        "SourceImage rows. This hides important correctness logic and makes the "
        "reset harder to reason about as one atomic database operation.",
    },
    {
        "id": "prompt_cleanup_hidden_in_helper",
        "category": "Correctness",
        "description": "Prompt deletion is delegated to _delete_orphan_prompts using prompt_ids "
        "collected before T2ISample deletion. The orphan-prompt decision should be "
        "computed inside the same query pipeline from remaining references.",
    },
    {
        "id": "checkpoint_reset_missing",
        "category": "Correctness",
        "description": "deleted_checkpoints is hardcoded to 0. If ingestion checkpoints exist, "
        "the function name implies they should be reset as part of the same operation.",
    },
    {
        "id": "early_return_skips_cleanup_paths",
        "category": "Correctness",
        "description": "The function returns early when no orphaned images are found. This is only "
        "safe if all other cleanup targets depend strictly on orphaned images. "
        "Checkpoint cleanup, source-level metadata cleanup, or ingestion state reset "
        "would be skipped.",
    },
    {
        "id": "file_cleanup_logic_in_python_sets",
        "category": "Performance",
        "description": "canonical_file_ids, derivative_file_ids, referenced_canonical_file_ids, "
        "and clean_file_ids are computed in Python. This should be expressed as "
        "SQL set logic so Postgres can optimize it.",
    },
    {
        "id": "non_atomic_multi_step_mutation",
        "category": "Correctness",
        "description": "The function performs several dependent mutations across multiple statements. "
        "Without an explicit transaction boundary and DB-side pipeline, partial failure "
        "can leave source images, samples, prompts, images, and file storage states "
        "inconsistent.",
    },
    {
        "id": "rowcount_reliance",
        "category": "Correctness",
        "description": "The function relies on rowcount from multiple statements. For complex operations, "
        "DELETE/UPDATE ... RETURNING CTEs are safer because they provide both the "
        "affected IDs and the final counts from the same pipeline.",
    },
    {
        "id": "poor_query_readability",
        "category": "Maintainability",
        "description": "Business concepts like affected images, orphaned images, orphaned prompts, "
        "cleanable canonical files, and cleaned storages are scattered across local "
        "variables. They should be named query builders so the pipeline documents "
        "the domain flow.",
    },
    {
        "id": "missing_index_assumptions",
        "category": "Performance",
        "description": "The function depends on lookups by source_id, image_id, prompt_id, "
        "canonical_file_id, derivative_of_file_id, and file_id, but does not document "
        "the required indexes. Without indexes, the reset can become slow at scale.",
    },
]

def _load_file(name: str) -> str:
    path = os.path.join(os.path.dirname(__file__), "data", name)
    with open(path) as f:
        return f.read()


def _build_known_issues_text() -> str:
    lines = []
    for i, issue in enumerate(KNOWN_ISSUES, 1):
        lines.append(f"{i}. **[{issue['category']}] {issue['id']}**: {issue['description']}")
    return "\n".join(lines)


SYSTEM_PROMPT = """\
You are a senior software engineer performing a code review. You will be \
given a guidelines document (AGENTS.md) and a Python source file.

Your task:
1. Identify every issue in the Python code that violates the guidelines \
or represents a genuine code quality problem.
2. For each issue, explain **why** it matters (the risk or consequence).
3. For each issue, propose a **concrete fix** — show the corrected code \
or describe the specific change.
4. Prioritize issues by severity (security > resilience > architecture > style).
5. Reference the relevant AGENTS.md section for each issue.

Be thorough but precise. Do not invent issues that don't exist in the code.\
"""


@scorer(metrics=[accuracy()])
def code_critique_scorer(grader_model: str | None = None):
    rubric = open(
        os.path.join(os.path.dirname(__file__), "rubrics", "code_critique.txt")
    ).read()
    known_issues_text = _build_known_issues_text()
    filled_rubric = rubric.replace("{known_issues}", known_issues_text)

    async def score(state, target):
        output = state.output.completion

        grader = get_model(grader_model or os.environ.get(
            "INSPECT_GRADER_MODEL", "openai/anthropic/claude-sonnet-4-6"
        ))

        result = await grader.generate(
            f"{filled_rubric}\n\n## Model's Critique to Evaluate\n\n{output}"
        )
        grader_text = result.completion.lower()

        if "grade: correct" in grader_text:
            return Score(value=CORRECT, explanation=result.completion)
        elif "grade: partial" in grader_text:
            return Score(value=PARTIAL, explanation=result.completion)
        else:
            return Score(value=INCORRECT, explanation=result.completion)

    return score


@task
def code_critique(grader_model: str | None = None):
    agents_md = _load_file("agents_guidelines.md")
    buggy_code = _load_file("buggy_agent.py")

    prompt = f"""\
## AGENTS.md — Development Guidelines

{agents_md}

---

## Python File to Review: `agent.py`

```python
{buggy_code}
```

---

Review the Python code above against the AGENTS.md guidelines. \
Identify all issues, explain why each matters, and propose concrete fixes. \
Prioritize by severity.\
"""

    return Task(
        dataset=[
            Sample(
                input=prompt,
                target="Comprehensive critique identifying security, resilience, "
                "architecture, and code quality issues with explanations and fixes",
                id="buggy_agent_v1",
                metadata={
                    "known_issue_count": len(KNOWN_ISSUES),
                    "categories": list({i["category"] for i in KNOWN_ISSUES}),
                },
            )
        ],
        solver=[
            system_message(SYSTEM_PROMPT),
            generate(),
        ],
        scorer=code_critique_scorer(grader_model),
        config=GenerateConfig(
            temperature=0.3,
            max_tokens=8192,
        ),
    )
