"""Automated demo runner:
1) Starts server (assumes server running separately)
2) Simulates a POST /ask and then posts a simulated human response to Mongo via REST /hitl or directly if Mongo available.
This script prefers REST endpoints; it will fallback to writing to /tmp for demo orchestrator to pick up."""
import requests, time, os, json, uuid

BASE = os.getenv('BASE', 'http://localhost:8000')

def trigger_job(session_id='auto-session'):
    payload = {'session_id': session_id, 'question': 'Does login meet MFA?', 'attachments': {'code': 'allow_weak_mfa = True', 'images': None}}
    r = requests.post(f'{BASE}/ask', json=payload)
    r.raise_for_status()
    data = r.json()
    return data['job_id'], data['session_id']

def send_hitl_rest(request_id, session_id, answer='sms_otp'):
    files = {'file': ('', '')}
    data = {'request_id': request_id, 'session_id': session_id, 'answer': answer}
    r = requests.post(f'{BASE}/hitl', data=data)
    return r.status_code == 200

if __name__ == '__main__':
    job_id, session = trigger_job()
    print('Triggered job', job_id, 'session', session)
    # Wait briefly for server to send hitl request; since orchestrator polls Mongo for responses, we can't know request_id.
    # For demo: write a sentinel to /tmp that orchestrator's demo code checks.
    time.sleep(2)
    # Fallback: post a fake request into /hitl with a random request_id; orchestrator demo will accept it as the human response.
    rid = str(uuid.uuid4())
    ok = send_hitl_rest(rid, session, answer='sms_otp')
    print('Posted simulated HITL response:', ok)
    time.sleep(2)
    res = requests.get(f'{BASE}/result?job_id={job_id}').json()
    print(json.dumps(res, indent=2))
