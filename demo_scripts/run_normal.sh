#!/bin/bash
# Normal compliant run (no HITL expected)
set -e
echo "Triggering normal run (expect compliant, no HITL)..."
JOBID=$(curl -s -X POST http://localhost:8000/ask -H 'Content-Type: application/json' -d '{
  "session_id":"demo-normal",
  "question":"Does our login flow meet Policy X MFA requirements?",
  "attachments": {"code":"", "images": null, "evidence":"Mobile login supports OTP via SMS and TOTP configured"}
}' | jq -r .job_id)
echo "Job ID: $JOBID"
sleep 2
echo "Result:"
curl -s "http://localhost:8000/result?job_id=$JOBID" | jq
