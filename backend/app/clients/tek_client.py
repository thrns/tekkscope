import os
import logging
import asyncio
from typing import Annotated, Sequence, TypedDict
import json
from dotenv import load_dotenv
from fastapi import HTTPException
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from app.research import run_research
from app.research_lib.api.settings_utils import create_settings_snapshot
from app.research_lib.config.llm_config import get_llm as get_configured_llm
from app.research_lib.config.provider_router import provider_overrides_from_env
from app.models.api_models import ChatRequest
from app.clients.supabase_client import supabase, decrement_credits
from app.config.credit_rates import compute_credits_used
from app.utils.rate_limiter import check_rate_limit
from app.streaming import manager
import uuid

load_dotenv()
logging.basicConfig(level=logging.INFO)


def deep_research_fn(query: str) -> str:
    """
    Performs deep research on a given query using the local_deep_research library.
    This tool is useful for complex questions that require in-depth analysis and web searching.
    """
    result = run_research(query, mode="quick")
    return result.get("summary", "")

class GraphState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    query: str
    response: str
    iterations: int
    research_summary: str

@tool("quick_research")
async def quick_research_tool(query: str) -> dict:
    """
    Lightweight research for context/definitions. Returns text plus optional citations.
    """
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(
        None,
        lambda: run_research(query, mode="quick")
    )
    text = res.get("summary") or ""
    sources = res.get("sources") or []
    citations = []
    try:
        for s in sources:
            title = s.get("title") or s.get("name") or ""
            url = s.get("url") or s.get("link") or ""
            if url:
                citations.append({"title": title, "url": url})
    except Exception:
        pass
    return {"text": text, "citations": citations}

@tool("search_content")
async def search_content_tool(query: str) -> dict:
    """
    Perform targeted web search and return top results with citations.
    """
    try:
        from app.clients.search import search_links
        results = await search_links(query, n_queries=3, num_results=8, enhanced_search=True)
    except Exception:
        results = []
    citations = []
    for r in results[:8]:
        title = r.get("title", "")
        url = r.get("url", "")
        if url:
            citations.append({"title": title, "url": url})
    text = "\n".join([f"- {x.get('title','')} ({x.get('url','')})" for x in results[:8]])
    return {"text": text, "citations": citations, "results": results}

tools = [quick_research_tool, search_content_tool]


def get_llm():
    max_tokens = int(
        os.getenv("TEKK_LLM_MAX_TOKENS", os.getenv("LDR_LLM_MAX_TOKENS", "16000"))
    )
    overrides = provider_overrides_from_env(
        max_tokens=max_tokens,
        temperature=0,
        search_tool="searxng",
        search_instance_url=os.getenv(
            "TEKK_SEARXNG_URL", "https://search.tekkscope.com"
        ),
    )
    settings_snapshot = create_settings_snapshot(overrides=overrides)
    return get_configured_llm(settings_snapshot=settings_snapshot)


# Define the enhanced system prompt
SYSTEM_PROMPT = """
You are Tek Pro, an AI assistant developed by Tekkscope Team. You excel at providing accurate, timely, and precise answers to questions.

# Core Communication Style

Write naturally and conversationally, as a knowledgeable person would speak. Avoid these AI-typical phrases:
- "delve into", "underscore", "at its core", "that being said"
- "a key takeaway is", "from a broader perspective", "it's worth noting"
- "generally speaking", "typically", "to some extent"
- "streamline", "bolster", "facilitate", "leverage", "robust"

Instead, use direct language:
- "let's look at" → "here's what matters"
- "typically" → "usually" or "most of the time"
- "facilitate" → "help" or "make easier"

Add personality through:
- Real-world examples and analogies
- Personal observations or context
- Specific details over vague generalizations
- Conversational transitions that feel natural

# Expert-Level Thinking and Response

**Approach every question with depth:**
- Break down complex problems systematically
- Consider multiple angles before answering
- Identify edge cases and nuances
- Question assumptions in the query itself
- Connect ideas across different domains when relevant

**Show reasoning, not just results:**
- Walk through your thought process when it adds value
- Explain *why* something works, not just *what* works
- Highlight trade-offs and alternatives
- Point out where consensus ends and debate begins

**Adapt to context:**
- Match technical depth to the user's level
- For beginners: build understanding from the ground up
- For experts: skip basics, focus on insights and nuances
- For professionals: emphasize practical implications and real-world constraints

# Information Strategy

**Search intelligently:**
- For rapidly changing topics (news, prices, trends, current events): search immediately
- For established knowledge (science, history, definitions): answer directly unless verification would add value
- For technical questions: use your knowledge base first, search for recent changes or specific implementations
- For controversial topics: search to capture multiple perspectives and current discourse

**When searching:**
- Synthesize findings into coherent insights, don't just summarize
- Identify patterns and connections across sources
- Evaluate source quality and note conflicting information
- Extract the most valuable information, not just the most recent

**When answering directly:**
- Draw on deep understanding, not surface-level facts
- Provide context that makes the answer more useful
- Anticipate follow-up questions and address them proactively
- Use examples that illuminate rather than just illustrate

# Response Excellence

**Structure for impact:**
1. Lead with the core answer or insight
2. Build understanding layer by layer
3. Use examples that resonate with real experience
4. End with actionable takeaways or next steps when appropriate

**Precision in language:**
- Choose specific words over general ones
- Use concrete examples over abstract descriptions
- Replace hedging ("might", "could be") with honest uncertainty ("I'm not sure" or "this depends on...")
- Be direct about limitations or gaps in knowledge

**Quality markers:**
- Does this answer reveal understanding, not just information?
- Would an expert find something valuable here?
- Have I avoided both over-simplification and unnecessary complexity?
- Does this feel like talking to someone who really knows their stuff?

# Before You Respond

Ask yourself:
- Have I thought about this deeply enough?
- Does this sound natural, or like corporate speak?
- Am I being specific and concrete?
- Have I added genuine insight, not just facts?
- Would I be satisfied with this answer if I asked the question?

Your goal: Be the expert who not only knows the answer, but understands it deeply enough to explain it in a way that actually helps someone learn, decide, or act.
"""
def create_agent_graph():
    # Create the LLM with tools
    llm = get_llm()
    llm_with_tools = llm.bind_tools(tools)

    # Define the prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    # Define the agent node
    def agent_node(state: GraphState):
        messages = state["messages"]
        query = state["query"]

        # Add the current query if it's the first interaction
        if not messages or (
            messages
            and isinstance(messages[-1], HumanMessage)
            and messages[-1].content != query
        ):
            messages = messages + [HumanMessage(content=query)]

        # Generate response
        chain = prompt | llm_with_tools
        response = chain.invoke({"messages": messages})

        return {
            "messages": messages + [response],
            "query": query,
            "iterations": state.get("iterations", 0) + 1,
        }

    # Heuristic routing
    def should_research(query: str) -> bool:
        return False

    def router_node(state: GraphState):
        return state

    async def researcher_node(state: GraphState):
        query = state["query"]
        loop = asyncio.get_running_loop()
        summary = await loop.run_in_executor(None, lambda: deep_research_fn(query))
        msgs = state["messages"] + [HumanMessage(content=f"Research summary:\n{summary}")]
        return {
            "messages": msgs,
            "query": query,
            "iterations": state.get("iterations", 0),
            "research_summary": summary,
        }

    # Create the graph
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tools))

    # Add edges
    workflow.add_edge("tools", "agent")
    workflow.add_edge("researcher", "agent")

    # Add conditional edges
    workflow.add_conditional_edges(
        "agent",
        tools_condition,
        {
            "tools": "tools",
            "__end__": END,
        },
    )

    workflow.add_conditional_edges(
        "router",
        lambda state: "researcher" if should_research(state["query"]) else "agent",
        {
            "researcher": "researcher",
            "agent": "agent",
        },
    )

    # Set entry point
    workflow.set_entry_point("router")

    # Compile the graph
    return workflow.compile()


# Create the graph instance
graph = create_agent_graph()


async def get_chat_completion(request: ChatRequest, user_id: str, api_key_id: str | None = None) -> dict:
    if user_id and api_key_id:
        await check_rate_limit(api_key_id, user_id)

    initial_state = {
        "messages": [],
        "query": request.query,
        "response": "",
        "iterations": 0,
    }

    try:
        final_state = graph.invoke(initial_state)
        messages = final_state["messages"]
        if messages and isinstance(messages[-1], AIMessage):
            response = messages[-1].content
        else:
            response = "I apologize, but I couldn't generate a response."
        try:
            total_tokens = max(1, round(len(response) / 4))
            input_tokens = max(1, round(total_tokens * 0.7))
            output_tokens = max(1, round(total_tokens * 0.3))
            # Ensure they sum to total_tokens
            if input_tokens + output_tokens != total_tokens:
                output_tokens = total_tokens - input_tokens
            credits_used = compute_credits_used(input_tokens, output_tokens, "TEKKSCOPE", "tek_pro")
            research_id = str(uuid.uuid4())
            supabase.table("usage").insert({
                "user_id": user_id,
                "service_used": "tek_pro",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "credits_used": credits_used,
                "research_id": research_id,
                "api_token_id": api_key_id,
                "timestamp": __import__("datetime").datetime.utcnow().isoformat()+"Z",
            }).execute()
            try:
                decrement_credits(user_id, credits_used)
            except Exception:
                pass
        except Exception:
            pass
    except Exception:
        logging.exception("Error during graph execution:")
        raise

    return {"response": response}


async def stream_chat(messages: list, client_id: str, user_id: str, api_key_id: str | None = None) -> None:
    # Check rate limit and send error to client if exceeded
    if client_id and api_key_id:
        try:
            await check_rate_limit(api_key_id, user_id)
        except HTTPException as e:
            await manager.send_to_client(client_id, {"type": "error", "content": e.detail})
            await manager.send_to_client(client_id, {"type": "response", "content": "[END_OF_STREAM]"})
            return

    initial_state = {
        "messages": messages,
        "query": messages[-1].content if messages and isinstance(messages[-1], HumanMessage) else "", # Assuming last message is the query
        "response": "",
        "iterations": 0,
    }

    try:
        full_text = ""
        def _to_jsonable(obj):
            try:
                json.dumps(obj)
                return obj
            except TypeError:
                pass
            if isinstance(obj, BaseMessage):
                role = (
                    "user" if isinstance(obj, HumanMessage) else
                    "assistant" if isinstance(obj, AIMessage) else
                    "system"
                )
                return {"role": role, "content": getattr(obj, "content", "")}
            if isinstance(obj, (list, tuple)):
                return [_to_jsonable(x) for x in obj]
            if isinstance(obj, dict):
                return {k: _to_jsonable(v) for k, v in obj.items()}
            return str(obj)

        def normalize_thinking(k, v):
            payload = {"phase": k}
            try:
                if isinstance(v, dict):
                    if "iterations" in v and isinstance(v["iterations"], int):
                        payload["iterations"] = v["iterations"]
                    if "query" in v and v["query"]:
                        payload["query"] = v["query"]
                    msgs = v.get("messages")
                    if isinstance(msgs, list) and msgs:
                        # find latest content string
                        preview = ""
                        for m in reversed(msgs):
                            if isinstance(m, BaseMessage):
                                c = getattr(m, "content", "") or ""
                                if c:
                                    preview = str(c)
                                    break
                            elif isinstance(m, dict):
                                c = m.get("content")
                                if isinstance(c, str) and c:
                                    preview = c
                                    break
                        if preview:
                            payload["text_preview"] = preview[:200]
            except Exception:
                pass
            return payload

        def flatten_ai_content(content):
            try:
                if isinstance(content, str):
                    return content
                if isinstance(content, list):
                    parts = []
                    for item in content:
                        if isinstance(item, str):
                            parts.append(item)
                        elif isinstance(item, dict):
                            # OpenAI new content parts {type:"text", text:"..."}
                            t = item.get("text") or item.get("content")
                            if isinstance(t, str):
                                parts.append(t)
                    return "".join(parts)
            except Exception:
                pass
            return str(content or "")

        # Do not pre-search; allow the agent to decide which tool to use

        async for event in graph.astream(initial_state):
            for k, v in event.items():
                if k == END:
                    continue
                await manager.send_to_client(
                    client_id,
                    {"type": "thinking", "content": normalize_thinking(k, _to_jsonable(v))},
                )

                # Try streaming agent response content during the run
                try:
                    if k == "agent":
                        text_piece = ""
                        if isinstance(v, AIMessage):
                            text_piece = flatten_ai_content(getattr(v, "content", ""))
                        elif isinstance(v, dict):
                            content = v.get("content")
                            if content:
                                text_piece = flatten_ai_content(content)
                            else:
                                msgs = v.get("messages")
                                if isinstance(msgs, list) and msgs:
                                    last_msg = msgs[-1]
                                    if isinstance(last_msg, AIMessage):
                                        text_piece = flatten_ai_content(getattr(last_msg, "content", ""))
                                    elif isinstance(last_msg, dict):
                                        c = last_msg.get("content")
                                        if c:
                                            text_piece = flatten_ai_content(c)
                        if text_piece:
                            if isinstance(text_piece, str):
                                await manager.send_to_client(client_id, {"type": "response", "content": text_piece})
                            else:
                                try:
                                    await manager.send_to_client(client_id, {"type": "response", "content": str(text_piece)})
                                except Exception:
                                    pass
                    elif k == "tools":
                        # If a tool returned citations or results, forward citations to client
                        try:
                            payload = v
                            if isinstance(payload, dict):
                                # Stream text from tool output
                                t = payload.get("text")
                                if isinstance(t, str) and t:
                                    await manager.send_to_client(client_id, {"type": "response", "content": t})
                                # Stream structured results directly
                                results = payload.get("results")
                                if isinstance(results, list) and results:
                                    await manager.send_to_client(client_id, {"type": "response", "content": {"results": results}})
                                # Stream citations if provided
                                cits = payload.get("citations")
                                if isinstance(cits, list) and cits:
                                    await manager.send_to_client(client_id, {"type": "response", "content": {"citations": cits}})
                        except Exception:
                            pass
                except Exception:
                    pass

            # Check for the final response in the stream
            if END in event:
                final_state = event[END]
                messages = final_state["messages"]
                full_text = ""
                if messages:
                    # Prefer last AIMessage content
                    last = messages[-1]
                    if isinstance(last, AIMessage):
                        full_text = flatten_ai_content(getattr(last, "content", "")) or ""
                    # Fallback: concatenate all AIMessage contents
                    if not full_text:
                        for m in messages:
                            if isinstance(m, AIMessage):
                                c = flatten_ai_content(getattr(m, "content", "")) or ""
                                if c:
                                    full_text += c
                if not full_text:
                    # Final fallback: serialize final_state
                    try:
                        full_text = json.dumps(_to_jsonable(final_state))
                    except Exception:
                        full_text = ""
                if not full_text:
                    full_text = "Research completed, but no answer text was generated."

        # Stream the final response
        chunk_size = 40
        for i in range(0, len(full_text), chunk_size):
            chunk = full_text[i : i + chunk_size]
            if chunk:
                await manager.send_to_client(
                    client_id, {"type": "response", "content": chunk}
                )
                await asyncio.sleep(0)  # yield to loop
        await manager.send_to_client(
            client_id, {"type": "response", "content": "[END_OF_STREAM]"}
        )
        await manager.send_to_client(client_id, "[END_OF_STREAM]")
        try:
            total_tokens = max(1, round(len(full_text) / 4))
            input_tokens = max(1, round(total_tokens * 0.7))
            output_tokens = max(1, round(total_tokens * 0.3))
            # Ensure they sum to total_tokens
            if input_tokens + output_tokens != total_tokens:
                output_tokens = total_tokens - input_tokens
            credits_used = compute_credits_used(input_tokens, output_tokens, "TEKKSCOPE", "tek_pro")
            research_id = str(uuid.uuid4())
            await manager.send_to_client(client_id, {"type": "thinking", "content": {"phase": "finalizing"}})
            import asyncio
            loop = asyncio.get_running_loop()
            def _insert():
                try:
                    supabase.table("usage").insert({
                        "user_id": user_id,
                        "service_used": "tek_pro",
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "credits_used": credits_used,
                        "research_id": research_id,
                        "api_token_id": api_key_id,
                        "timestamp": __import__("datetime").datetime.utcnow().isoformat()+"Z",
                    }).execute()
                    decrement_credits(user_id, credits_used)
                except Exception:
                    pass
            loop.run_in_executor(None, _insert)
        except Exception:
            pass

    except Exception:
        logging.exception("Error during graph execution:")
        raise
