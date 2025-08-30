#!/bin/bash
# Run that triggers 2 HITL steps: clarification then upload
set -e
echo "Triggering run that will ask for clarification and upload..."
JOBID=$(curl -s -X POST http://localhost:8000/ask -H 'Content-Type: application/json' -d '{
  "session_id":"demo-two-hitl",
  "question":"Does our login flow meet Policy X MFA requirements?",
  "attachments": {"code":"allow_weak_mfa = True", "images": null}
}' | jq -r .job_id)
echo "Job ID: $JOBID"
echo "Make sure a HITL client is connected with session 'demo-two-hitl' and reply to prompts."
# Wait a bit for human to respond and for upload step
sleep 10
# For upload step: send sample image to /hitl (simulate upload request)
echo "Uploading screenshot as part of HITL response..."
curl -s -X POST http://localhost:8000/hitl -F 'request_id=upload-1' -F 'session_id=demo-two-hitl' -F 'answer=see screenshot' -F 'file=@sample_data/screenshot.png' | jq
sleep 2
echo "Final result:"
curl -s "http://localhost:8000/result?job_id=$JOBID" | jq
