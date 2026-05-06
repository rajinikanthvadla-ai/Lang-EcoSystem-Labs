"""
LAB 2 — LangChain + Bedrock (Chains & Tools)
==============================================
GOAL: See how LangChain adds structure with tools and chains.

WHAT CHANGED from Lab 1:
  - Instead of manually stuffing context, we give the LLM **tools**
  - The LLM DECIDES which tool to call (order lookup, stock check, etc.)
  - LangChain handles the tool-calling loop automatically

STILL LIMITED:
  - No memory between turns (each question is independent)
  - No complex routing (can't do "if angry → escalate to human")
  - That's what LangGraph fixes in Lab 3

RUN:  python main.py
"""

import os
import sys

from dotenv import load_dotenv
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from shared.fake_db import (
    check_product_stock,
    get_customer_orders,
    get_order,
    get_return_policy,
    request_return,
)

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

# ── 1. Define Tools (the LLM can call these) ──────────────────────────

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
    lines = []
    for o in orders:
        lines.append(f"  {o['order_id']}: {o['status']} — ₹{o['total']}")
    return "Orders:\n" + "\n".join(lines)


ALL_TOOLS = [lookup_order, check_stock, get_policy, initiate_return, list_customer_orders]

# ── 2. Create LLM with tools bound ────────────────────────────────────

llm = ChatBedrock(
    model_id=os.getenv("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0"),
    region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
)

llm_with_tools = llm.bind_tools(ALL_TOOLS)

SYSTEM = SystemMessage(content="""You are a friendly customer support agent for ShopEasy.
You have access to tools to look up orders, check stock, handle returns, and explain policies.
Always use the appropriate tool before answering — never guess.
Be concise and helpful.""")

# ── 3. The chain: ask → tool call → tool result → final answer ────────

TOOL_MAP = {t.name: t for t in ALL_TOOLS}


def handle_question(question: str) -> str:
    """
    This is a ReAct-style loop:
    1. Send question to LLM
    2. If LLM wants to call a tool → execute it → send result back
    3. Repeat until LLM gives a final text answer
    """
    messages = [SYSTEM, HumanMessage(content=question)]

    for _ in range(5):  # max 5 tool-call rounds (safety limit)
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            return response.content

        # Execute each tool the LLM requested
        for tc in response.tool_calls:
            tool_fn = TOOL_MAP[tc["name"]]
            result = tool_fn.invoke(tc["args"])
            from langchain_core.messages import ToolMessage
            messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    return response.content


# ── 4. Interactive loop ────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  LAB 2 — LangChain + Bedrock (Tools & Chains)")
    print("=" * 60)
    print("Now the bot can USE TOOLS to answer!")
    print("Try: 'Is the Webcam in stock?'")
    print("Try: 'Where is order ORD-1001?'")
    print("Try: 'I want to return order ORD-1002'")
    print("Try: 'Show me all orders for customer C001'")
    print("Type 'quit' to exit.\n")

    while True:
        question = input("You: ").strip()
        if question.lower() in ("quit", "exit", "q"):
            break

        answer = handle_question(question)
        print(f"\nBot: {answer}\n")
