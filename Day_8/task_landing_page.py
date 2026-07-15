"""
Task 1: Build an interactive landing page for an edu-tech startup
selling gen-AI courses to working professionals.

The model gets coding tools in a sandbox and must produce a complete,
functional landing page. Scored by LLM judge on 6 deterministic criteria.

Usage:
    inspect eval task_landing_page.py --model openai/anthropic/claude-sonnet-4-6
    inspect eval task_landing_page.py -T sandbox_type=modal  # use Modal sandbox
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
from inspect_ai.solver import generate, system_message, use_tools
from inspect_ai.tool import bash, text_editor
from inspect_ai.model import GenerateConfig, get_model, ChatMessageUser
from inspect_ai.util import sandbox

import os
import re


SYSTEM_PROMPT = """\
You are a senior frontend developer. You have access to a sandbox with \
bash and a text editor. Node.js 22 and live-server are available.

Your task is to build a complete, production-quality landing page. \
Write all files under /app/ in the sandbox. You must create at minimum \
an index.html file. You may also create CSS and JS files.

Requirements:
- Modern, visually polished design (not a bare template)
- Semantic HTML5
- Responsive layout (mobile + desktop)
- Meaningful JavaScript interactivity (animations, form handling, etc.)
- Professional copy and section structure

When done, confirm the files you created and their purpose.\
"""

LANDING_PAGE_BRIEF = """\
Build an interactive landing page for **SkillForge AI** — an edu-tech startup \
that sells generative AI courses to working professionals.

Target audience: mid-career professionals (product managers, marketers, \
analysts, engineers) who want to upskill in gen-AI tools and workflows.

The page should include:
1. **Hero section** — bold headline, subheading, primary CTA button
2. **Course highlights** — 3-4 featured courses with icons/visuals
3. **Social proof** — testimonials or company logos
4. **How it works** — 3-step process (enroll → learn → apply)
5. **Pricing section** — at least 2 tiers
6. **Footer** — links, newsletter signup form with validation

Make it feel premium and modern. Use a cohesive color scheme, smooth \
scroll, subtle animations, and interactive elements. The form must \
validate email input client-side before submission.\
"""


@scorer(metrics=[accuracy()])
def landing_page_scorer(grader_model: str | None = None):
    rubric = open(
        os.path.join(os.path.dirname(__file__), "rubrics", "landing_page.txt")
    ).read()

    async def score(state, target):
        output = state.output.completion

        grader = get_model(grader_model or os.environ.get(
            "INSPECT_GRADER_MODEL", "openai/anthropic/claude-sonnet-4-6"
        ))

        result = await grader.generate(
            f"{rubric}\n\n## Model Output to Evaluate\n\n{output}"
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
def landing_page(
    sandbox_type: str = "docker",
    grader_model: str | None = None,
):
    if sandbox_type == "docker":
        sandbox_cfg = "docker"
    elif sandbox_type == "modal":
        sandbox_cfg = ("modal", "modal_sandbox.yaml")
    else:
        raise ValueError(f"Unknown sandbox_type: {sandbox_type}. Use 'docker' or 'modal'.")

    return Task(
        dataset=[
            Sample(
                input=LANDING_PAGE_BRIEF,
                target="A complete, interactive landing page with HTML/CSS/JS",
                id="landing_page_v1",
            )
        ],
        solver=[
            system_message(SYSTEM_PROMPT),
            use_tools([bash(), text_editor()]),
            generate(),
        ],
        scorer=landing_page_scorer(grader_model),
        sandbox=sandbox_cfg,
        config=GenerateConfig(
            temperature=0.7,
            max_tokens=16384,
        ),
        message_limit=30,
        token_limit=100_000,
    )
