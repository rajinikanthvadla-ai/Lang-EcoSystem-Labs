# Lab 1 — Raw AWS Bedrock (No Framework)

## What You'll Learn
- How to call AWS Bedrock directly with `boto3`
- What a "prompt + context" pattern looks like without any framework
- **Why this approach breaks** as complexity grows

## The Problem
You're building customer support for **ShopEasy**. Customers ask about orders, returns, products.

With raw Bedrock, YOU have to:
1. Manually detect what the user wants
2. Manually fetch the right data
3. Manually stuff it into the prompt
4. Parse the response yourself

**This works for simple cases but falls apart fast.** That's why we need frameworks → Lab 2.

## Run It
```bash
cd labs/lab-1-bedrock-basics
python main.py
```

## Try These Questions
```
You: What is your return policy?
You: Where is my order ORD-1001?
You: Can I return order ORD-1002?
```

## Key Limitation (discuss with students)
Ask: *"What products do you have in stock?"*
→ The bot **can't answer** because we didn't manually add product data to the context.
→ In Lab 2, we solve this with **tools**.
