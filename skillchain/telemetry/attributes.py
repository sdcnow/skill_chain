"""OTel GenAI semantic convention attribute constants.

Follows https://opentelemetry.io/docs/specs/semconv/gen-ai/
"""

GEN_AI_OPERATION_NAME = "gen_ai.operation.name"
GEN_AI_PROVIDER_NAME = "gen_ai.provider.name"
GEN_AI_REQUEST_MODEL = "gen_ai.request.model"
GEN_AI_RESPONSE_MODEL = "gen_ai.response.model"
GEN_AI_SYSTEM = "gen_ai.system"

GEN_AI_USAGE_INPUT_TOKENS = "gen_ai.usage.input_tokens"
GEN_AI_USAGE_OUTPUT_TOKENS = "gen_ai.usage.output_tokens"

GEN_AI_AGENT_NAME = "gen_ai.agent.name"
GEN_AI_AGENT_DESCRIPTION = "gen_ai.agent.description"
GEN_AI_WORKFLOW_NAME = "gen_ai.workflow.name"

GEN_AI_TOOL_NAME = "gen_ai.tool.name"
GEN_AI_TOOL_TYPE = "gen_ai.tool.type"

SKILLCHAIN_SKILL_NAME = "skillchain.skill.name"
SKILLCHAIN_SKILL_DESCRIPTION = "skillchain.skill.description"
SKILLCHAIN_SKILL_MODEL = "skillchain.skill.model"
SKILLCHAIN_PATTERN_TYPE = "skillchain.pattern.type"
SKILLCHAIN_CHAIN_POSITION = "skillchain.chain.position"
SKILLCHAIN_CHAIN_LENGTH = "skillchain.chain.length"
SKILLCHAIN_DISCLOSURE_STAGE = "skillchain.disclosure.stage"
SKILLCHAIN_LOOP_ITERATION = "skillchain.loop.iteration"
SKILLCHAIN_LOOP_MAX_ITERATIONS = "skillchain.loop.max_iterations"
SKILLCHAIN_MAPREDUCE_ITEMS_COUNT = "skillchain.mapreduce.items_count"

OP_CHAT = "chat"
OP_INVOKE_AGENT = "invoke_agent"
OP_INVOKE_WORKFLOW = "invoke_workflow"
OP_EXECUTE_TOOL = "execute_tool"

PROVIDER_SKILLCHAIN = "skillchain"
