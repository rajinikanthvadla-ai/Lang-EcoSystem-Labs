import os

from langchain_aws import ChatBedrock
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, StateGraph

from .state import AgentState
from .tools import ALL_TOOLS, TOOL_MAP


def build_agent():
    llm = ChatBedrock(
        model_id=os.getenv("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    )
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    def classify_intent(state: AgentState) -> AgentState:
        last_message = state["messages"][-1].content

        result = llm.invoke([
            SystemMessage(content="""Classify the customer message into exactly ONE category:
- ORDER_STATUS: asking about order tracking, delivery, or status
- RETURN: wants to return, refund, or exchange
- PRODUCT: asking about products, stock, availability, prices
- ESCALATE: customer is frustrated, angry, or asks for a human or manager
- GENERAL: greeting, thanks, policy questions, or anything else

Reply with ONLY the category name, nothing else."""),
            HumanMessage(content=last_message),
        ])

        intent = result.content.strip().upper()
        if intent not in {"ORDER_STATUS", "RETURN", "PRODUCT", "ESCALATE", "GENERAL"}:
            intent = "GENERAL"

        return {"intent": intent}

    def handle_with_tools(state: AgentState) -> AgentState:
        system = SystemMessage(content=f"""You are a friendly customer support agent for ShopEasy.
Customer intent: {state['intent']}
Use your tools to look up information before answering.
Be concise and helpful. If you need an order ID or customer ID, ask for it.""")

        messages = [system] + state["messages"]
        response = llm_with_tools.invoke(messages)

        if not response.tool_calls:
            return {"messages": [response]}

        new_messages = [response]
        for tc in response.tool_calls:
            result = TOOL_MAP[tc["name"]].invoke(tc["args"])
            new_messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

        final = llm_with_tools.invoke(messages + new_messages)
        new_messages.append(final)

        if final.tool_calls:
            for tc in final.tool_calls:
                result = TOOL_MAP[tc["name"]].invoke(tc["args"])
                new_messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
            last = llm_with_tools.invoke(messages + new_messages)
            new_messages.append(last)

        return {"messages": new_messages}

    def handle_escalation(state: AgentState) -> AgentState:
        msg = AIMessage(content=(
            "I understand your frustration and I am sorry for the inconvenience. "
            "I am escalating this to our senior support team right now.\n\n"
            "Ticket #ESC-2026-0506 has been created.\n"
            "A senior agent will contact you within 2 hours.\n\n"
            "Is there anything else I can help with in the meantime?"
        ))
        return {"messages": [msg]}

    def route_by_intent(state: AgentState) -> str:
        return "escalate" if state["intent"] == "ESCALATE" else "tools"

    graph = StateGraph(AgentState)
    graph.add_node("classify", classify_intent)
    graph.add_node("tools", handle_with_tools)
    graph.add_node("escalate", handle_escalation)
    graph.set_entry_point("classify")
    graph.add_conditional_edges("classify", route_by_intent, {
        "tools": "tools",
        "escalate": "escalate",
    })
    graph.add_edge("tools", END)
    graph.add_edge("escalate", END)

    return graph.compile()
