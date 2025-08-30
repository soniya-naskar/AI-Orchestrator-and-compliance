# AI Compliance & Risk Orchestrator - GitHub-ready Repo

This repository is a GitHub-ready scaffold for the AI Compliance & Risk Orchestrator described in the spec.
It includes a FastAPI server (agents + API), HITL clients (CLI + React UI scaffold), infra configs (docker-compose),
indexing script, tests, and demo scripts for three scenarios.

---
## Repo Layout (important files)
```
/app                   # FastAPI server, agents, orchestrator, storage, hitl manager
/client                # HITL clients: CLI and React UI scaffold
/scripts               # helper scripts (indexing, automated demo)
/demo_scripts          # runnable demo scripts for scenarios
/tests                 # basic unit tests
/docker-compose.yml
/Dockerfile
/README.md (this file)
/postman_collection.json
```
---
## Setup & Run (local, no Docker required - quick path)

Requirements: Python 3.11+, pip, (optional: Docker & docker-compose)

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate     # macOS / Linux
venv\Scripts\activate.bat  # Windows (PowerShell)
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Index sample docs into Qdrant if you have Qdrant running locally:
```bash
python scripts/index_sample_docs.py
```

4. Start the server:
```bash
uvicorn app.main:app --reload --port 8000
```

5. Start the HITL client (CLI) in another terminal:
```bash
python client/hitl_client.py demo-session
```

6. Trigger demos via the included demo scripts (see below).

### Using Docker Compose (optional, spins up Qdrant/Mongo/Redis)
```bash
docker-compose up --build
# then run the indexer (if qdrant is up) in another terminal:
docker exec -it <orchestrator_container> python scripts/index_sample_docs.py
```

---
## Environment Variables (example .env)
```
MONGO_URI=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
WS_SECRET=supersecret
AGENT_TIMEOUT=20
TOP_K=5
```

---
## Architecture (DAG + Event Flow)

Text diagram (simplified):

```
Client (API POST /ask) --> Planner (build DAG) --> Orchestrator Executor
   |                                                   |
   |---> Parallel Collectors (PolicyRetriever, EvidenceRetriever, VisionOCR, CodeScanner) --   |                                                                                      |
   \-------------------------------------- Fan-in ----------------------------------------/
                                              |
                                          RiskScorer
                                              |
                                      Red-Team Critic (open_questions?)
                                              |
                                (If needed) HITL Manager -> WS (server->client hitl_request)
                                              |
                            Human replies -> resume -> Final Aggregator -> Result JSON
                                              |
                                 Persist: MongoDB (plans, results, human_responses)
                                 Cache: Redis (top-k, OCR results)
                                 Vector DB: Qdrant (RAG retrieval)
```

Sequence notes: planner persists DAG; orchestrator executes parallel tasks via `asyncio.gather`. HITL requests are pushed to connected clients via WebSocket `/connect`. Orchestrator waits for human responses (polls Mongo in demo).

---
## Sequence chart: run with two HITL interruptions (ASCII)

1. POST /ask -> server queues job -> starts orchestration
2. Parallel: PolicyRAG, EvidenceRAG, VisionOCR, CodeScanner
3. Fan-in -> RiskScorer -> score > threshold -> Critic generates open question -> HITL (clarification)
4. Human replies (via WS) -> orchestrator resumes -> detects missing artifact (screenshot) -> HITL (upload_request)
5. Human uploads image via REST `/hitl` (multipart) -> VisionOCR extracts text -> finalize decision -> store result

```
Client -> Server: POST /ask
Server -> Qdrant/Mongo: retrieve chunks (parallel)
Policy/Evidence/OCR/Code -> Server (fan-in)
Server -> Critic -> Server -> Client (hitl_request: clarification)
Client -> Server: hitl_response (WS)
Server -> Critic -> Server -> Client (hitl_request: upload_request)
Client -> Server: POST /hitl (upload image)
Server -> VisionOCR -> Evidence updated -> FinalAggregator -> Persist + Return result
```

---
## Example WebSocket messages

Server -> Client (`hitl_request`):
```json
{
  "type":"hitl_request",
  "session_id":"sess-123",
  "request_id":"req-789",
  "payload":{
    "type":"clarification",
    "prompt":"Which MFA method is used in mobile login? (options: totp, push, sms, none)",
    "required_artifact": null
  }
}
```

Client -> Server (`hitl_response`):
```json
{
  "type":"hitl_response",
  "session_id":"sess-123",
  "request_id":"req-789",
  "response_type":"clarification",
  "payload": {"answer":"totp"}
}
```

HITL upload (REST POST /hitl multipart):
```
POST /hitl
form fields: request_id, session_id, answer (optional)
file: image file to upload
```

---
## Demo scripts (three scenarios)

Scripts are in `/demo_scripts` and are executable (`chmod +x`). They use `curl` and assume server at http://localhost:8000 and a HITL CLI connected for WS scenarios. Each script prints the job_id and the final result JSON.

1. **Normal compliant decision (no HITL)** - `demo_scripts/run_normal.sh`
   - Sends attachments showing OTP evidence (so risk low). Orchestrator should decide `compliant` with no HITL prompts.

2. **Run with 2 HITL steps (clarification + upload)** - `demo_scripts/run_two_hitl.sh`
   - Triggers a job that will cause risk>threshold, causing an initial clarification HITL. The script instructs you to reply in the connected HITL client.
   - After clarification, the orchestrator requests an upload. Upload is performed via `curl` to `/hitl` with the image; orchestrator resumes and finalizes decision (likely `non_compliant`).

3. **Timeout -> insufficient_evidence** - `demo_scripts/run_timeout.sh`
   - Triggers a job but the human does not respond within the configured timeout. The orchestrator will fallback and return `insufficient_evidence` and log the timeout in human_interactions.

(Each script includes usage notes and prints what to watch for.)

---
## Known limitations & trade-offs

- This repo is a demo scaffold: many components are stubbed or simplified (embeddings, OCR fallback, code scanning heuristics).
- RAG quality depends on vector DB quality and chunking strategy; sample embedding is deterministic demo only.
- HITL waiting uses simple polling of Mongo in the demo; production should use event-driven pub/sub.
- Security: WS authentication, TLS (wss), artifact encryption, and strict access control are required for production but are simplified here.
- Scalability: For higher throughput use a task queue (Celery/RQ) and worker autoscaling; current demo runs in-process using asyncio which is fine for prototypes.
- Cost: integrating large LLMs will incur cost. Replace with private models where required.
- OCR: visual layout and diagrams require robust OCR with layout-aware parsing (PaddleOCR, Google Vision, or specialized models).

---
## Pushing to GitHub (suggested commands)

```bash
git init
git add .
git commit -m "Initial commit: AI Compliance & Risk Orchestrator demo"
# create a repo on GitHub (via web UI or gh CLI) then:
git remote add origin git@github.com:<your-org>/<repo>.git
git branch -M main
git push -u origin main
```

---
## Demo: expected outputs

- Normal run: final JSON with `"decision": "compliant"` and `human_interactions: []`.
- Two HITL run: final JSON containing two entries in `human_interactions` (clarification + upload) and a non-compliant decision with citations.
- Timeout run: `"decision":"insufficient_evidence"`, `human_interactions` contains a `timeout` status entry.

---
## Contact & contribution
Open issues or PRs after pushing to GitHub. Contributions welcome: improve RAG, replace embeddings, add role-aware memory, and add automated CI.

