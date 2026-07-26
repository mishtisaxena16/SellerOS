"""
PromptBuilder — loads prompt templates from agent_layer/prompts/ and
injects ContextBuilder output into them. Per section 22:

    Never hardcode prompts.

Template format is deliberately simple: `{{section_name}}` placeholders
that get replaced with the matching PromptContext block (see
context_builder.py's `as_prompt_blocks()`), plus a reserved
`{{user_query}}`. No Jinja2/templating engine dependency for something
this small — if prompts grow conditional logic (loops, if/else) beyond
straight substitution, that's the signal to bring in a real templating
library, not a reason to add one preemptively now.

Missing placeholders are left as literal `{{name}}` text rather than
raising, and a warning is recorded on the returned PromptRenderResult —
matching this project's general pattern (see ContextBuilder) of making
gaps visible instead of either crashing or silently guessing.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from backend.ai.agent_layer.base.context_builder import PromptContext

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

_PLACEHOLDER_RE = re.compile(r"\{\{(\w+)\}\}")


@dataclass
class PromptRenderResult:
    text: str
    warnings: list[str] = field(default_factory=list)


class PromptBuilder:
    def load_template(self, prompt_name: str) -> str:
        path = PROMPTS_DIR / f"{prompt_name}.md"
        if not path.exists():
            raise FileNotFoundError(
                f"No prompt template '{prompt_name}.md' in {PROMPTS_DIR}. "
                f"Add one to agent_layer/prompts/ — prompts are never hardcoded "
                f"inline in agent code (see handover doc section 22)."
            )
        return path.read_text(encoding="utf-8")

    def render(
        self,
        prompt_name: str,
        context: PromptContext,
        user_query: Optional[str] = None,
    ) -> PromptRenderResult:
        template = self.load_template(prompt_name)
        blocks = context.as_prompt_blocks()
        if user_query is not None:
            blocks.setdefault("user_query", user_query)

        warnings: list[str] = []

        def _substitute(match: "re.Match[str]") -> str:
            key = match.group(1)
            if key in blocks:
                return blocks[key]
            warnings.append(f"Prompt '{prompt_name}' references unresolved placeholder '{{{{{key}}}}}'.")
            return match.group(0)

        rendered = _PLACEHOLDER_RE.sub(_substitute, template)
        return PromptRenderResult(text=rendered, warnings=warnings)
