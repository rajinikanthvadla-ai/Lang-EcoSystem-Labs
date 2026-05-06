# Production Architecture

## Local Setup (What This Lab Runs)

```
Browser or Postman
       |
       | HTTP POST /chat
       v
 FastAPI Backend  (port 8000)
       |
       v
 LangGraph Agent
       |
       v
 AWS Bedrock (Nova Lite)
```

Sessions are stored in a Python dictionary in memory.
This is fine locally. It resets when the server restarts.

---

## AWS Production Setup (How Companies Deploy This)

```
User (Browser / Mobile App / WhatsApp)
       |
       v
  CloudFront  <-- CDN, caches static assets
       |
       v
  Application Load Balancer  <-- routes traffic to containers
       |
       v
  ECS Fargate  <-- runs your FastAPI container, auto-scales
       |               |
       v               v
  AWS Bedrock     ElastiCache Redis  <-- stores session state
  (Nova / Claude)       |
                        v
                   DynamoDB  <-- long-term conversation history
```

### Why Each Piece Exists

| Component | Why |
|-----------|-----|
| ECS Fargate | Runs your FastAPI container without managing servers |
| Application Load Balancer | Distributes traffic across multiple containers |
| ElastiCache Redis | Fast in-memory session store, shared across all containers |
| DynamoDB | Permanent storage for conversation history and audit logs |
| CloudFront | Serves the Streamlit frontend globally with low latency |
| AWS Bedrock | The LLM API, already in the same AWS network so latency is low |

---

## Simpler Option: AWS App Runner

If you want to deploy without learning ECS, use App Runner.
It reads your Dockerfile and handles everything automatically.

```yaml
# apprunner.yml
version: 1.0
runtime: docker
build:
  commands:
    build:
      - echo "Using Dockerfile"
run:
  network:
    port: 8000
  env:
    - name: AWS_DEFAULT_REGION
      value: us-east-1
```

Deploy command:
```bash
aws apprunner create-service \
  --service-name shopease-support \
  --source-configuration '{"ImageRepository": {...}}'
```

App Runner gives you a public HTTPS URL in about 2 minutes.

---

## What Changes Between Lab 3 and Production

| Lab 3 | Production |
|-------|------------|
| Terminal input/output | FastAPI REST API |
| State in Python variable | State in Redis |
| Runs on your laptop | Runs on ECS Fargate |
| One user at a time | Thousands of users at once |
| No URL | Public HTTPS endpoint |
| AWS keys in .env file | AWS IAM Role on the container |

The agent code itself does not change. Only where it runs and how state is stored changes.
