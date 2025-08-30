#!/bin/bash
# Trigger a job and do NOT respond as HITL -> expect insufficient_evidence after timeout
set -e
echo "Triggering run that will timeout waiting for HITL..."
JOBID=$(curl -s -X POST http://localhost:8000/ask -H 'Content-Type: application/json' -d '{
  "session_id":"demo-timeout",
  "question":"Does our login flow meet Policy X MFA requirements?",
  "attachments": {"code":"allow_weak_mfa = True", "images": null}
}' | jq -r .job_id)
echo "Job ID: $JOBID"
echo "Do NOT connect a HITL client for session 'demo-timeout' or do not reply to prompts. Waiting for timeout..."
# Wait longer than orchestrator's HITL timeout (demo uses ~30s)
sleep 40
echo "Result after timeout:"
curl -s "http://localhost:8000/result?job_id=$JOBID" | jq
