# Lab 2 LangChain + Bedrock (Chains & Tools)

## What You'll Learn
- How LangChain **tools** let the LLM fetch data on its own
- The ReAct loop: Think → Act (tool call) → Observe (result) → Answer
- How `bind_tools()` works under the hood

## What Changed from Lab 1?

| Feature | Lab 1 (Raw) | Lab 2 (LangChain) |
|---------|-------------|-------------------|
| Data fetching | YOU write `if` statements | LLM **decides** which tool to call |
| New data sources | Rewrite the prompt | Just add a new `@tool` function |
| Tool execution | Manual | Automatic via ReAct loop |

## Run It
```bash
cd labs/lab-2-langchain
python main.py
```

## Try These Questions
```
You: Is the Webcam in stock?           → calls check_stock tool
You: Where is order ORD-1001?          → calls lookup_order tool  
You: I want to return order ORD-1002   → calls initiate_return tool
You: What's your return policy?        → calls get_policy tool
You: Show me all orders for C001       → calls list_customer_orders tool
```

## Key Limitation
- **No memory**: Ask "Where is ORD-1001?" then "Can I return it?" — it forgets ORD-1001
- **No routing**: Can't say "if customer is angry → escalate to human"
- **No state**: Can't track a multi-step process (return flow: check eligibility → confirm → process)

→ Lab 3 (LangGraph) solves ALL of these.
