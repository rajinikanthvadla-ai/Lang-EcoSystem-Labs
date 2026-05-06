import os
import sys
import uuid
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel

_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
load_dotenv(os.path.join(_root, ".env"))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _root)
from packages.shopease_agent import AgentState, build_agent


# ---------------------------------------------------------------------------
# Session store
# In production this is Redis or DynamoDB.
# Here it is a plain dictionary in memory.
# ---------------------------------------------------------------------------
sessions: dict[str, AgentState] = {}

agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent
    agent = build_agent()
    yield


app = FastAPI(
    title="ShopEasy Support API",
    description="Customer support agent powered by LangGraph and AWS Bedrock.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request and response models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Where is my order ORD-1001?",
                    "session_id": None,
                }
            ]
        }
    }


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    intent: str


class ResetResponse(BaseModel):
    session_id: str
    message: str


class HealthResponse(BaseModel):
    status: str
    sessions_active: int


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    """
    Check if the API is running.
    Use this in Postman first to confirm the server is up.
    """
    return {"status": "ok", "sessions_active": len(sessions)}


@app.post("/chat", response_model=ChatResponse, tags=["Agent"])
def chat(req: ChatRequest):
    """
    Send a message to the support agent.

    - If session_id is not provided, a new session is created automatically.
    - Pass the returned session_id in all follow-up messages to keep the conversation going.
    - The agent remembers everything said in the same session.

    Try these messages in order to see memory in action:
    1. "Where is my order ORD-1001?"
    2. "Can I return it?"
    3. "Is the Webcam in stock?"
    4. "I want to speak to a manager!"
    """
    session_id = req.session_id or str(uuid.uuid4())

    if session_id not in sessions:
        sessions[session_id] = {
            "messages": [],
            "intent": "",
            "customer_id": None,
        }

    state = sessions[session_id]
    state["messages"].append(HumanMessage(content=req.message))

    try:
        result = agent.invoke(state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    sessions[session_id] = result

    reply = ""
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            reply = msg.content
            break

    return ChatResponse(
        reply=reply or "Sorry, I could not process that. Please try again.",
        session_id=session_id,
        intent=result.get("intent", ""),
    )


@app.post("/chat/reset", response_model=ResetResponse, tags=["Agent"])
def reset(session_id: str):
    """
    Clear the conversation memory for a session.
    Useful when a customer wants to start fresh.
    """
    if session_id in sessions:
        del sessions[session_id]
    return {"session_id": session_id, "message": "Session cleared."}


@app.get("/sessions", tags=["System"])
def list_sessions():
    """
    List all active session IDs.
    Useful for debugging during development.
    """
    return {"active_sessions": list(sessions.keys())}
