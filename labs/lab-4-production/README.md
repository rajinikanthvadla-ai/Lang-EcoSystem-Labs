# Lab 4 - Production Agent with FastAPI + Streamlit

## What This Lab Covers

- Wrapping the LangGraph agent as a real HTTP API using FastAPI
- A browser-based chat UI using Streamlit
- Multi-user session management (each user gets their own memory)
- Testing the API from Postman
- Understanding how this maps to a real AWS deployment

## Project Structure

```
lab-4-production/
├── packages/
│   └── shopease_agent/        # Agent logic as a reusable package
│       ├── state.py            # AgentState definition
│       ├── tools.py            # All tool functions
│       └── agent.py            # Graph builder
│
├── backend/
│   └── main.py                # FastAPI app with /chat, /health endpoints
│
├── frontend/
│   └── app.py                 # Streamlit chat UI
│
├── infra/
│   └── architecture.md        # AWS deployment diagram and explanation
│
└── docker-compose.yml         # Run everything with one command
```

## Option 1 - Run Without Docker (Easier for Local Testing)

Install the extra dependencies:
```bash
pip install fastapi uvicorn streamlit requests
```

Start the backend (keep this terminal open):
```bash
cd labs/lab-4-production
uvicorn backend.main:app --reload --port 8000
```

Open a second terminal and start the frontend:
```bash
cd labs/lab-4-production
streamlit run frontend/app.py
```

Open your browser at `http://localhost:8501`

## Option 2 - Run With Docker

```bash
cd labs/lab-4-production
docker-compose up --build
```

- Frontend: http://localhost:8501
- Backend API docs: http://localhost:8000/docs

---

## Testing with Postman

### Step 1 - Check the server is running

```
GET http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "sessions_active": 0
}
```

### Step 2 - Start a conversation (no session_id needed)

```
POST http://localhost:8000/chat
Content-Type: application/json

{
  "message": "Where is my order ORD-1001?"
}
```

Expected response:
```json
{
  "reply": "Your order ORD-1001 is currently shipped...",
  "session_id": "abc-123-xyz",
  "intent": "ORDER_STATUS"
}
```

**Copy the session_id from the response.**

### Step 3 - Follow up (pass the session_id to keep memory)

```
POST http://localhost:8000/chat
Content-Type: application/json

{
  "message": "Can I return it?",
  "session_id": "abc-123-xyz"
}
```

The agent remembers ORD-1001 from the previous message.

### Step 4 - Try more messages with the same session_id

```json
{ "message": "Is the Webcam in stock?", "session_id": "abc-123-xyz" }
{ "message": "I want to speak to a manager!", "session_id": "abc-123-xyz" }
```

### Step 5 - Reset the session

```
POST http://localhost:8000/chat/reset?session_id=abc-123-xyz
```

### Step 6 - Browse all API endpoints

Open `http://localhost:8000/docs` in your browser.
FastAPI generates this automatically. You can test every endpoint here without Postman.

---

## How Session Memory Works

When you call `/chat` without a session_id:
1. The backend creates a new UUID as the session_id
2. It creates an empty AgentState for that session
3. It stores it in the sessions dictionary
4. It returns the session_id to you

On every follow-up call with that session_id:
1. The backend loads the existing AgentState
2. Appends your new message to the conversation history
3. Runs the agent with the full history
4. Saves the updated state back

This is exactly how WhatsApp chatbots, Intercom, and Freshdesk AI work.
The only difference in production is the state is stored in Redis instead of a Python dictionary.

---

## API Endpoints Summary

| Method | Endpoint | What It Does |
|--------|----------|--------------|
| GET | /health | Check if server is running |
| POST | /chat | Send a message, get a reply |
| POST | /chat/reset | Clear memory for a session |
| GET | /sessions | List all active session IDs |
| GET | /docs | Interactive API documentation |
