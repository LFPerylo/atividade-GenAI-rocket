from functools import partial

from pydantic_ai import Agent, RunContext, Tool
from pydantic_ai.capabilities import ProcessHistory
from pydantic_ai.models import Model

from cinerocket.agent.deps import AgentDeps
from cinerocket.agent.history import keep_recent_turns
from cinerocket.agent.prompts import SYSTEM_INSTRUCTIONS, reference_date_instructions, schema_instructions
from cinerocket.agent.tools import (
    describe_table,
    distinct_values,
    only_with_semantic_index,
    run_sql,
    search_synopses,
)
from cinerocket.agent.validation import validate_answer
from cinerocket.domain.models import AgentAnswer

AnalystAgent = Agent[AgentDeps, AgentAnswer]


def build_agent(model: Model | None, *, retries: int, history_max_turns: int) -> AnalystAgent:
    agent: AnalystAgent = Agent(
        model,
        name="cinerocket-analyst",
        deps_type=AgentDeps,
        output_type=AgentAnswer,
        instructions=SYSTEM_INSTRUCTIONS,
        retries=retries,
        defer_model_check=True,
        tools=[
            Tool(describe_table),
            Tool(distinct_values),
            Tool(run_sql),
            Tool[AgentDeps](search_synopses, prepare=only_with_semantic_index),
        ],
        capabilities=[ProcessHistory(partial(keep_recent_turns, max_turns=history_max_turns))],
    )

    @agent.instructions
    def dynamic_context(ctx: RunContext[AgentDeps]) -> str:
        return "\n\n".join(
            (reference_date_instructions(ctx.deps.today), schema_instructions(ctx.deps.catalog.describe()))
        )

    @agent.output_validator
    def check_answer(ctx: RunContext[AgentDeps], answer: AgentAnswer) -> AgentAnswer:
        return validate_answer(ctx.deps, answer)

    return agent
