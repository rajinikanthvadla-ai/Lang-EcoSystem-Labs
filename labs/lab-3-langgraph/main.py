"""
LAB 3 — LangGraph + Bedrock (Stateful Agent with Routing)
===========================================================
GOAL: Build a PRODUCTION-STYLE agent with state, memory, and routing.

WHAT CHANGED from Lab 2:
  - MEMORY: Remembers the full conversation (ask follow-ups!)
  - ROUTING: Classifies intent → routes to specialized handlers
  - STATE: Tracks the entire conversation as a graph state
  - HUMAN ESCALATION: Detects frustrated customers → escalates

THIS IS HOW REAL AGENTS WORK:
  Customer → [Classify Intent] → Order Node / Return Node / Product Node / Escalate
                                       ↓
                              [Use Tools + LLM]
                                       ↓
                               [Generate Response]

RUN:  python main.py
"""

import os
import sys
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_aws import ChatBedrock
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from shared.fake_db import (
    check_product_stock,
    get_customer_orders,
    get_order,
    get_return_policy,
    request_return,
)

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

# ═══════════════════════════════════════════════════════════════════════
# 1. STATE — This is what makes LangGraph different from LangChain
# ═══════════════════════════════════════════════════════════════════════

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]  # Full conversation history
    intent: str                                            # Classified intent
    customer_id: str | None                                # Tracked across turns


# ═══════════════════════════════════════════════════════════════════════
# 2. TOOLS — Same tools as Lab 2, but now used within graph nodes
# ═══════════════════════════════════════════════════════════════════════

@tool
def lookup_order(order_id: str) -> str:
    """Look up order status and details by order ID (e.g. ORD-1001)."""
    order = get_order(order_id)
    if not order:
        return f"No order found with ID {order_id}"
    return (
        f"Order {order_id}:\n"
        f"  Items: {', '.join(order['items'])}\n"
        f"  Total: ₹{order['total']}\n"
        f"  Status: {order['status']}\n"
        f"  Tracking: {order.get('tracking_id', 'N/A')}\n"
        f"  Delivery: {order.get('estimated_delivery', order.get('delivered_on', 'N/A'))}"
    )


@tool
def check_stock(product_name: str) -> str:
    """Check if a product is available in stock."""
    return check_product_stock(product_name)


@tool
def get_policy() -> str:
    """Get the store's return and refund policy."""
    return get_return_policy()


@tool
def initiate_return(order_id: str) -> str:
    """Start a return/refund process for a delivered order."""
    return request_return(order_id)


@tool
def list_customer_orders(customer_id: str) -> str:
    """List all orders for a customer by their customer ID (e.g. C001)."""
    orders = get_customer_orders(customer_id)
    if not orders:
        return f"No orders found for customer {customer_id}"
    lines = [f"  {o['order_id']}: {o['status']} — ₹{o['total']}" for o in orders]
    return "Orders:\n" + "\n".join(lines)


ALL_TOOLS = [lookup_order, check_stock, get_policy, initiate_return, list_customer_orders]
TOOL_MAP = {t.name: t for t in ALL_TOOLS}


# ═══════════════════════════════════════════════════════════════════════
# 3. LLM SETUP
# ═══════════════════════════════════════════════════════════════════════

llm = ChatBedrock(
    model_id=os.getenv("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0"),
    region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
)

llm_with_tools = llm.bind_tools(ALL_TOOLS)


# ═══════════════════════════════════════════════════════════════════════
# 4. GRAPH NODES — Each node is a step in the agent's workflow
# ═══════════════════════════════════════════════════════════════════════

def classify_intent(state: AgentState) -> AgentState:
    """
    NODE 1: Classify what the customer wants.
    This replaces hand-coded if/else routing in traditional apps.
    """
    last_message = state["messages"][-1].content

    classification_prompt = [
        SystemMessage(content="""Classify the customer message into exactly ONE category:
- ORDER_STATUS: asking about order tracking, delivery, or status
- RETURN: wants to return, refund, or exchange
- PRODUCT: asking about products, stock, availability, prices
- ESCALATE: customer is frustrated, angry, or asks for a human/manager
- GENERAL: greeting, thanks, general policy questions, or anything else

Respond with ONLY the category name, nothing else."""),
        HumanMessage(content=last_message),
    ]

    result = llm.invoke(classification_prompt)
    intent = result.content.strip().upper()

    valid_intents = {"ORDER_STATUS", "RETURN", "PRODUCT", "ESCALATE", "GENERAL"}
    if intent not in valid_intents:
        intent = "GENERAL"

    return {"intent": intent}


def handle_with_tools(state: AgentState) -> AgentState:
    """
    NODE 2: Let the LLM use tools to answer the question.
    This handles ORDER_STATUS, RETURN, PRODUCT, and GENERAL intents.
    """
    system = SystemMessage(content=f"""You are a friendly customer support agent for ShopEasy.
Customer intent: {state['intent']}
Use your tools to look up information before answering. Be concise and helpful.
If you need a customer ID or order ID that wasn't provided, ask for it.""")

    messages = [system] + state["messages"]

    response = llm_with_tools.invoke(messages)

    if not response.tool_calls:
        return {"messages": [response]}

    new_messages = [response]
    for tc in response.tool_calls:
        tool_fn = TOOL_MAP[tc["name"]]
        result = tool_fn.invoke(tc["args"])
        new_messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    final_response = llm_with_tools.invoke(messages + new_messages)
    new_messages.append(final_response)

    # One more round of tool calls if needed
    if final_response.tool_calls:
        for tc in final_response.tool_calls:
            tool_fn = TOOL_MAP[tc["name"]]
            result = tool_fn.invoke(tc["args"])
            new_messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
        final = llm_with_tools.invoke(messages + new_messages)
        new_messages.append(final)

    return {"messages": new_messages}


def handle_escalation(state: AgentState) -> AgentState:
    """
    NODE 3: Handle angry/frustrated customers.
    In production, this would create a ticket and route to a human agent.
    """
    msg = AIMessage(content=(
        "I completely understand your frustration, and I'm sorry for the inconvenience. "
        "I'm escalating this to our senior support team right now.\n\n"
        "🎫 **Ticket #ESC-2026-0506** has been created.\n"
        "A senior agent will contact you within 2 hours.\n\n"
        "Is there anything else I can help with in the meantime?"
    ))
    return {"messages": [msg]}


# ═══════════════════════════════════════════════════════════════════════
# 5. ROUTING — The graph decides which path to take
# ═══════════════════════════════════════════════════════════════════════

def route_by_intent(state: AgentState) -> str:
    """
    CONDITIONAL EDGE: Routes to the right node based on classified intent.
    This is the power of LangGraph — declarative routing as a graph.
    """
    if state["intent"] == "ESCALATE":
        return "escalate"
    return "tools"


# ═══════════════════════════════════════════════════════════════════════
# 6. BUILD THE GRAPH — This is the actual agent architecture
# ═══════════════════════════════════════════════════════════════════════
#
#   [START]
#      │
#      ▼
#   [classify_intent]
#      │
#      ├── intent == ESCALATE ──→ [handle_escalation] ──→ [END]
#      │
#      └── else ────────────────→ [handle_with_tools]  ──→ [END]
#

graph = StateGraph(AgentState)

# Add nodes
graph.add_node("classify", classify_intent)
graph.add_node("tools", handle_with_tools)
graph.add_node("escalate", handle_escalation)

# Add edges
graph.set_entry_point("classify")
graph.add_conditional_edges("classify", route_by_intent, {"tools": "tools", "escalate": "escalate"})
graph.add_edge("tools", END)
graph.add_edge("escalate", END)

# Compile into a runnable agent
agent = graph.compile()


# ═══════════════════════════════════════════════════════════════════════
# 7. INTERACTIVE LOOP — With conversation memory!
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  LAB 3 — LangGraph + Bedrock (Stateful Agent)")
    print("=" * 60)
    print("This agent has MEMORY + ROUTING + TOOLS!")
    print()
    print("Try this conversation flow:")
    print("  1. 'Where is my order ORD-1001?'")
    print("  2. 'Can I return it?'          ← it remembers ORD-1001!")
    print("  3. 'Is the Webcam in stock?'")
    print("  4. 'This is ridiculous, I want to speak to a manager!'")
    print("     ↑ escalation detection!")
    print()
    print("Type 'quit' to exit, 'reset' to clear memory.\n")

    conversation_state: AgentState = {
        "messages": [],
        "intent": "",
        "customer_id": None,
    }

    while True:
        question = input("You: ").strip()
        if question.lower() in ("quit", "exit", "q"):
            break
        if question.lower() == "reset":
            conversation_state = {"messages": [], "intent": "", "customer_id": None}
            print("\n[Memory cleared]\n")
            continue

        conversation_state["messages"].append(HumanMessage(content=question))

        result = agent.invoke(conversation_state)
        conversation_state = result

        last_ai_msg = None
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
                last_ai_msg = msg
                break

        if last_ai_msg:
            print(f"\nBot: {last_ai_msg.content}\n")
        else:
            print("\nBot: I'm not sure how to help with that. Could you rephrase?\n")
