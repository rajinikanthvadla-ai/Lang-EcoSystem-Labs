# Lab 3  LangGraph + Bedrock (Stateful Agent)

## What You'll Learn
- How **LangGraph** builds agents as **state machines (graphs)**
- Conversation **memory** that persists across turns
- **Intent classification** → **conditional routing**
- How real production agents handle escalation

## What Changed from Lab 2?

| Feature | Lab 2 (LangChain) | Lab 3 (LangGraph) |
|---------|-------------------|-------------------|
| Memory | ❌ None | ✅ Full conversation history |
| Routing | ❌ One path | ✅ Intent → route to handler |
| Escalation | ❌ No | ✅ Detects frustration → escalates |
| Architecture | Linear chain | Graph with nodes and edges |
| State | Stateless | Stateful (tracks intent, customer, messages) |

## The Agent Graph (Visual)

```
[START]
   │
   ▼
[Classify Intent]
   │
   ├── ESCALATE ──→ [Handle Escalation] ──→ [END]
   │
   └── else ──────→ [Handle With Tools] ──→ [END]
```

## Run It
```bash
cd labs/lab-3-langgraph
python main.py
```

## Try This Conversation Flow
```
You: Where is my order ORD-1001?     → routes to tools → lookup_order
You: Can I return it?                → REMEMBERS ORD-1001 from context!
You: Is the Webcam in stock?         → routes to tools → check_stock
You: This is unacceptable! Manager!  → routes to ESCALATE node
You: reset                           → clears memory
```

## Key Concepts

### Why a Graph?
- Real agents aren't linear. They need to **branch**, **loop**, and **remember**.
- A graph lets you visualize the agent's decision-making process.
- Easy to add new nodes: want a "billing" handler? Add a node + route.

### State is Everything
- `AgentState` carries `messages`, `intent`, and `customer_id` across the entire conversation.
- This is what makes "Can I return it?" work after "Where is ORD-1001?"

### Production Extensions
In a real system, you'd add:
- **Checkpointing**: Save state to a database (LangGraph supports this natively)
- **Human-in-the-loop**: Pause the graph, wait for human approval, then continue
- **Parallel nodes**: Check order + check inventory simultaneously
- **Retry/fallback**: If a tool fails, retry or use a fallback
