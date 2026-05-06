"""
LAB 1 — Raw AWS Bedrock Call
=============================
GOAL: Understand what happens under the hood before any framework.

This is the SIMPLEST possible customer support bot:
  1. We call AWS Bedrock directly using boto3
  2. We stuff customer context into the prompt manually
  3. No tools, no chains, no agents — just a raw LLM call

RUN:  python main.py
"""

import json
import sys
import os

import boto3
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from shared.fake_db import get_order, get_return_policy

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

# ── 1. Connect to Bedrock ──────────────────────────────────────────────
bedrock = boto3.client(
    service_name="bedrock-runtime",
    region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
)
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")


def ask_bedrock(user_question: str, order_id: str | None = None) -> str:
    """
    Send a single question to Bedrock with optional order context.
    This is what EVERY framework does under the hood — just an HTTP call.
    """

    # ── 2. Build context manually (this is tedious — frameworks fix this) ──
    context_parts = [get_return_policy()]
    if order_id:
        order = get_order(order_id)
        if order:
            context_parts.append(f"Order details:\n{json.dumps(order, indent=2)}")

    system_prompt = f"""You are a friendly customer support agent for ShopEasy (an e-commerce store).
Use ONLY the context below to answer. If you don't know, say so.

Context:
{chr(10).join(context_parts)}"""

    # ── 3. The actual Bedrock API call (using the Converse API — works with ANY model) ──
    response = bedrock.converse(
        modelId=MODEL_ID,
        system=[{"text": system_prompt}],
        messages=[{"role": "user", "content": [{"text": user_question}]}],
        inferenceConfig={"maxTokens": 512},
    )

    return response["output"]["message"]["content"][0]["text"]


# ── 4. Interactive loop ────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  LAB 1 — Raw Bedrock Customer Support (No Framework)")
    print("=" * 60)
    print("Try: 'What is your return policy?'")
    print("Try: 'Where is my order ORD-1001?'")
    print("Type 'quit' to exit.\n")

    while True:
        question = input("You: ").strip()
        if question.lower() in ("quit", "exit", "q"):
            break

        # Naive order detection — just scan for ORD-XXXX pattern
        order_id = None
        for word in question.split():
            if word.startswith("ORD-"):
                order_id = word
                break

        answer = ask_bedrock(question, order_id)
        print(f"\nBot: {answer}\n")
