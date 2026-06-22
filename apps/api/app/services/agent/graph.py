from dataclasses import dataclass
from typing import Any, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.enums import AgentIntent, MessageRole, PolicyDecision, UnansweredPromptReason
from app.db.models.retrieval_log import UnansweredPrompt
from app.services.agent.context import build_context_text, summarize_used_sources
from app.services.agent.grounding import verify_grounding
from app.services.agent.intent import classify_intent
from app.services.agent.language import detect_language
from app.services.agent.policy import evaluate_policy, policy_refusal_message
from app.services.agent.prompts import SYSTEM_PROMPT, build_user_prompt
from app.services.agent.tool_intent import (
    build_tool_arguments,
    classify_tool_intent,
    format_tool_response,
    tool_name_for_intent,
)
from app.services.conversations import add_message, create_conversation, get_conversation
from app.services.llm.base import LLMMessage, LLMProvider
from app.services.llm.factory import get_llm_provider
from app.services.mcp.client import ApiMcpClient, get_mcp_client
from app.services.retrieval.hybrid import HybridRetrievalResult, run_hybrid_retrieval


class AgentState(TypedDict, total=False):
    conversation_id: int
    session_id: str | None
    user_message: str
    language: str
    intent: str
    intent_hints: list[str]
    policy_decision: str
    retrieval_log_id: int | None
    unanswered_prompt_id: int | None
    context_text: str
    assistant_message: str
    grounded: bool
    refused: bool
    sources_summary: list[dict[str, str | bool]]
    retrieval_result: HybridRetrievalResult | None
    uses_mcp_tool: bool


@dataclass(frozen=True)
class AgentTurnResult:
    conversation_id: int
    assistant_message: str
    language: str
    intent: AgentIntent
    policy_decision: PolicyDecision
    retrieval_log_id: int | None
    unanswered_prompt_id: int | None
    sources: list[dict[str, str | bool]]
    grounded: bool
    refused: bool


async def run_agent_turn(
    session: AsyncSession,
    message: str,
    *,
    conversation_id: int | None = None,
    session_id: str | None = None,
    language: str | None = None,
    settings: Settings | None = None,
    llm_provider: LLMProvider | None = None,
    document_search_override=None,
) -> AgentTurnResult:
    config = settings or get_settings()
    provider = llm_provider or get_llm_provider(config)

    if conversation_id is not None:
        conversation = await get_conversation(session, conversation_id)
        if conversation is None:
            raise ValueError(f"Conversation {conversation_id} not found")
    else:
        conversation = await create_conversation(
            session,
            session_id=session_id,
            language=language,
        )

    initial_state: AgentState = {
        "conversation_id": conversation.id,
        "session_id": session_id,
        "user_message": message,
        "language": language or conversation.language or config.default_language,
    }

    final_state = await _AGENT_GRAPH.ainvoke(
        initial_state,
        config={
            "configurable": {
                "session": session,
                "settings": config,
                "llm_provider": provider,
                "document_search_override": document_search_override,
            }
        },
    )

    return AgentTurnResult(
        conversation_id=final_state["conversation_id"],
        assistant_message=final_state["assistant_message"],
        language=final_state["language"],
        intent=AgentIntent(final_state["intent"]),
        policy_decision=PolicyDecision(final_state["policy_decision"]),
        retrieval_log_id=final_state.get("retrieval_log_id"),
        unanswered_prompt_id=final_state.get("unanswered_prompt_id"),
        sources=final_state.get("sources_summary", []),
        grounded=final_state.get("grounded", False),
        refused=final_state.get("refused", False),
    )


def _configurable(config: RunnableConfig) -> dict[str, Any]:
    return config.get("configurable", {})


async def _prepare_node(state: AgentState, config: RunnableConfig) -> AgentState:
    cfg = _configurable(config)
    session: AsyncSession = cfg["session"]
    settings: Settings = cfg["settings"]

    language = detect_language(state["user_message"], settings, state.get("language"))
    intent, intent_hints = classify_intent(state["user_message"])
    policy_decision = evaluate_policy(state["user_message"])

    if policy_decision != PolicyDecision.ALLOW:
        intent = AgentIntent.SALARY if policy_decision == PolicyDecision.REFUSE_SALARY else AgentIntent.CONTACT
        uses_mcp_tool = False
    else:
        tool_intent = classify_tool_intent(state["user_message"])
        if tool_intent is not None:
            intent = tool_intent
            uses_mcp_tool = True
        else:
            uses_mcp_tool = False

    conversation = await get_conversation(session, state["conversation_id"])
    if conversation is None:
        raise ValueError(f"Conversation {state['conversation_id']} not found")

    await add_message(
        session,
        conversation,
        role=MessageRole.USER,
        content=state["user_message"],
    )

    conversation.language = language
    await session.commit()

    return {
        **state,
        "language": language,
        "intent": intent.value,
        "intent_hints": intent_hints,
        "policy_decision": policy_decision.value,
        "grounded": False,
        "refused": False,
        "sources_summary": [],
        "uses_mcp_tool": uses_mcp_tool,
    }


def _route_after_prepare(state: AgentState) -> str:
    if state["policy_decision"] != PolicyDecision.ALLOW.value:
        return "policy_refusal"
    if state.get("uses_mcp_tool"):
        return "mcp_tool"
    return "retrieve"


async def _policy_refusal_node(state: AgentState, config: RunnableConfig) -> AgentState:
    cfg = _configurable(config)
    session: AsyncSession = cfg["session"]
    decision = PolicyDecision(state["policy_decision"])
    refusal = policy_refusal_message(decision)

    unanswered = UnansweredPrompt(
        query=state["user_message"],
        reason=UnansweredPromptReason.POLICY,
        language=state["language"],
        session_id=state.get("session_id"),
    )
    session.add(unanswered)
    await session.flush()

    return {
        **state,
        "assistant_message": refusal,
        "refused": True,
        "grounded": True,
        "unanswered_prompt_id": unanswered.id,
    }


async def _mcp_tool_node(state: AgentState, config: RunnableConfig) -> AgentState:
    cfg = _configurable(config)
    session: AsyncSession = cfg["session"]
    settings: Settings = cfg["settings"]
    mcp_client: ApiMcpClient = cfg.get("mcp_client") or get_mcp_client(settings)

    intent = AgentIntent(state["intent"])
    tool_name = tool_name_for_intent(intent)
    arguments = build_tool_arguments(intent, state["user_message"])

    cleaned_arguments = {
        key: value for key, value in arguments.items() if value not in ("", None)
    }
    result = await mcp_client.call_tool(
        session,
        conversation_id=state["conversation_id"],
        tool_name=tool_name,
        arguments=cleaned_arguments,
    )

    if result.success and result.payload is not None:
        assistant_message = format_tool_response(intent, result.payload)
        sources_summary = [
            {
                "source_type": str(source.get("source_type", "")),
                "title": str(source.get("title", "")),
                "was_used": bool(source.get("was_used", False)),
            }
            for source in result.payload.get("sources", [])
            if isinstance(source, dict)
        ]
        retrieval_log_id = result.payload.get("retrieval_log_id")
        return {
            **state,
            "assistant_message": assistant_message,
            "grounded": True,
            "refused": False,
            "sources_summary": sources_summary,
            "retrieval_log_id": retrieval_log_id if isinstance(retrieval_log_id, int) else None,
        }

    return {
        **state,
        "assistant_message": (
            "I could not complete the requested workflow tool call safely. "
            "Please try again or use approved contact channels."
        ),
        "grounded": False,
        "refused": True,
        "policy_decision": PolicyDecision.REFUSE_UNSUPPORTED.value,
    }


async def _retrieve_node(state: AgentState, config: RunnableConfig) -> AgentState:
    cfg = _configurable(config)
    session: AsyncSession = cfg["session"]
    settings: Settings = cfg["settings"]

    retrieval_result = await run_hybrid_retrieval(
        session,
        state["user_message"],
        language=state["language"],
        session_id=state.get("session_id"),
        intent_hints=state.get("intent_hints", []),
        settings=settings,
        document_search_override=cfg.get("document_search_override"),
    )

    context_text = build_context_text(retrieval_result.sources)
    return {
        **state,
        "retrieval_result": retrieval_result,
        "retrieval_log_id": retrieval_result.retrieval_log_id,
        "unanswered_prompt_id": retrieval_result.unanswered_prompt_id,
        "context_text": context_text,
        "sources_summary": summarize_used_sources(retrieval_result.sources),
    }


def _route_after_retrieve(state: AgentState) -> str:
    retrieval_result = state.get("retrieval_result")
    if retrieval_result is None or not retrieval_result.had_usable_context:
        return "unsupported_refusal"
    return "generate"


async def _unsupported_refusal_node(state: AgentState, config: RunnableConfig) -> AgentState:
    decision = PolicyDecision.REFUSE_UNSUPPORTED
    if state.get("policy_decision") == PolicyDecision.REFUSE_GROUNDING.value:
        decision = PolicyDecision.REFUSE_GROUNDING

    return {
        **state,
        "assistant_message": policy_refusal_message(decision),
        "refused": True,
        "grounded": False,
        "policy_decision": decision.value,
    }


async def _generate_node(state: AgentState, config: RunnableConfig) -> AgentState:
    cfg = _configurable(config)
    provider: LLMProvider = cfg["llm_provider"]
    context_text = state.get("context_text", "")

    user_prompt = build_user_prompt(state["user_message"], context_text)
    answer = await provider.complete(
        [
            LLMMessage(role="system", content=SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_prompt),
        ]
    )

    grounded = await verify_grounding(provider, context_text=context_text, answer=answer)
    return {
        **state,
        "assistant_message": answer,
        "grounded": grounded,
        "refused": False,
        "policy_decision": PolicyDecision.ALLOW.value if grounded else PolicyDecision.REFUSE_GROUNDING.value,
    }


def _route_after_generate(state: AgentState) -> str:
    if not state.get("grounded", False):
        return "unsupported_refusal"
    return "finalize"


async def _finalize_node(state: AgentState, config: RunnableConfig) -> AgentState:
    cfg = _configurable(config)
    session: AsyncSession = cfg["session"]
    conversation = await get_conversation(session, state["conversation_id"])
    if conversation is None:
        raise ValueError(f"Conversation {state['conversation_id']} not found")

    await add_message(
        session,
        conversation,
        role=MessageRole.ASSISTANT,
        content=state["assistant_message"],
    )
    return state


def _build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("prepare", _prepare_node)
    graph.add_node("policy_refusal", _policy_refusal_node)
    graph.add_node("mcp_tool", _mcp_tool_node)
    graph.add_node("retrieve", _retrieve_node)
    graph.add_node("unsupported_refusal", _unsupported_refusal_node)
    graph.add_node("generate", _generate_node)
    graph.add_node("finalize", _finalize_node)

    graph.set_entry_point("prepare")
    graph.add_conditional_edges(
        "prepare",
        _route_after_prepare,
        {
            "policy_refusal": "policy_refusal",
            "mcp_tool": "mcp_tool",
            "retrieve": "retrieve",
        },
    )
    graph.add_edge("policy_refusal", "finalize")
    graph.add_edge("mcp_tool", "finalize")
    graph.add_conditional_edges(
        "retrieve",
        _route_after_retrieve,
        {
            "unsupported_refusal": "unsupported_refusal",
            "generate": "generate",
        },
    )
    graph.add_edge("unsupported_refusal", "finalize")
    graph.add_conditional_edges(
        "generate",
        _route_after_generate,
        {
            "unsupported_refusal": "unsupported_refusal",
            "finalize": "finalize",
        },
    )
    graph.add_edge("finalize", END)

    return graph.compile()


_AGENT_GRAPH = _build_graph()
