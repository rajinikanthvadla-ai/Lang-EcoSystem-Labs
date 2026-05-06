# Lang EcoSystem Labs — AI Agents with AWS Bedrock

> Build a real-world **Customer Support Agent** step by step.  
> Go from raw API calls → LangChain → LangGraph, and see exactly why each layer exists.

## The Customer Problem

**ShopEasy** is an e-commerce store. Customers contact support to:
- Track orders ("Where is my order ORD-1001?")
- Return items ("I want to return my keyboard")
- Check product stock ("Is the Webcam available?")
- Escalate issues ("This is terrible, get me a manager!")

You'll build an AI agent that handles ALL of this — in 3 progressive labs.

---

## Lab Progression

```
Lab 1 (Raw Bedrock)     Lab 2 (LangChain)      Lab 3 (LangGraph)
─────────────────────   ─────────────────────   ─────────────────────
• Direct boto3 call     • Tools (@tool)         • State machine (graph)
• Manual context        • LLM picks tools       • Memory across turns
• No tools              • ReAct loop            • Intent routing
• No memory             • No memory             • Escalation handling
• ~50 lines             • ~100 lines            • ~180 lines
```

### Why 3 labs?

| You'll understand... | By experiencing... |
|----------------------|-------------------|
| What Bedrock does | Lab 1: Raw API call |
| Why we need tools | Lab 1 fails → Lab 2 adds tools |
| Why we need memory | Lab 2 forgets → Lab 3 remembers |
| Why we need routing | Lab 2 can't escalate → Lab 3 routes |
| How real agents work | Lab 3 = production architecture |

---

## Quick Start

### 1. Prerequisites
- Python 3.11+
- AWS Account with Bedrock access (Claude 3 Sonnet enabled)
- AWS CLI configured OR `.env` file with credentials

### 2. Setup
```bash
# Clone and enter
git clone <your-repo-url>
cd Lang-EcoSystem-Labs

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Configure AWS credentials
copy .env.example .env       # Windows
# cp .env.example .env       # Mac/Linux
# Then edit .env with your AWS keys
```

### 3. Run Each Lab
```bash
python labs/lab-1-bedrock-basics/main.py    # Raw Bedrock
python labs/lab-2-langchain/main.py         # LangChain + Tools
python labs/lab-3-langgraph/main.py         # LangGraph Agent
```

---

## Project Structure

```
Lang-EcoSystem-Labs/
│
├── README.md                  ← You are here
├── requirements.txt           ← All dependencies
├── .env.example               ← AWS credential template
│
└── labs/
    ├── shared/
    │   └── fake_db.py         ← Mock e-commerce database
    │
    ├── lab-1-bedrock-basics/
    │   ├── README.md          ← Lab instructions
    │   └── main.py            ← Raw boto3 → Bedrock
    │
    ├── lab-2-langchain/
    │   ├── README.md          ← Lab instructions
    │   └── main.py            ← LangChain tools + ReAct
    │
    └── lab-3-langgraph/
        ├── README.md          ← Lab instructions
        └── main.py            ← Stateful graph agent
```

---

## Key Concepts Comparison

### How each approach handles: "Where is ORD-1001?" then "Can I return it?"

**Lab 1 — Raw Bedrock:**
```
Turn 1: You manually detect "ORD-1001", fetch data, stuff into prompt → works
Turn 2: "Can I return it?" → FAILS (what is "it"? No memory, no context)
```

**Lab 2 — LangChain:**
```
Turn 1: LLM calls lookup_order("ORD-1001") automatically → works
Turn 2: "Can I return it?" → FAILS (no memory of previous turn)
```

**Lab 3 — LangGraph:**
```
Turn 1: Classify → ORDER_STATUS → tools node → lookup_order → works
Turn 2: "Can I return it?" → WORKS! Full conversation in state.messages
```

---

## AWS Bedrock Setup

1. Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock)
2. Navigate to **Model access** in the left sidebar
3. Request access to **Anthropic Claude 3 Sonnet**
4. Wait for approval (usually instant)
5. Create an IAM user with `AmazonBedrockFullAccess` policy
6. Put the access key and secret in your `.env` file

---

