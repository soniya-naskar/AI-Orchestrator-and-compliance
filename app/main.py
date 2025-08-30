import uuid, asyncio, json, os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, UploadFile, File, Form
from .orchestrator import run_pipeline
from .schemas import FinalDecision
from datetime import datetime
from .hitl import register_ws, unregister_ws
from .storage import db, init_redis, redis
import base64

app = FastAPI()

JOBS = {}
RESULTS = {}

@app.on_event('startup')
async def startup():
    try:
        await init_redis()
    except Exception:
        pass

@app.post('/ask')
async def ask(payload: dict, background_tasks: BackgroundTasks):
    session_id = payload.get('session_id') or 'sess_' + str(uuid.uuid4())
    job_id = 'job_' + str(uuid.uuid4())
    JOBS[job_id] = {'session_id': session_id, 'status': 'queued', 'created_at': datetime.utcnow().isoformat()}
    background_tasks.add_task(_run_job, job_id, session_id, payload)
    return {'job_id': job_id, 'session_id': session_id}

async def _run_job(job_id, session_id, payload):
    JOBS[job_id]['status'] = 'running'
    attachments = payload.get('attachments', {})
    # if images provided as base64 string, decode
    if attachments.get('images') and isinstance(attachments.get('images'), str):
        try:
            attachments['images'] = base64.b64decode(attachments['images'])
        except Exception:
            attachments['images'] = None
    final = await run_pipeline(session_id, payload.get('question',''), attachments)
    final_json = final.dict()
    RESULTS[job_id] = final_json
    JOBS[job_id]['status'] = 'done'

@app.get('/result')
async def get_result(job_id: str):
    if job_id not in RESULTS:
        return {'status': JOBS.get(job_id, {}).get('status', 'unknown')}
    return RESULTS[job_id]

@app.post('/hitl')  # REST fallback for human replies / uploads
async def hitl_reply(request_id: str = Form(...), session_id: str = Form(...), answer: str = Form(None), file: UploadFile = File(None)):
    entry = {'request_id': request_id, 'session_id': session_id, 'payload': {'answer': answer}, 'received_at': datetime.utcnow().isoformat()}
    if file:
        data = await file.read()
        entry['payload']['file_name'] = file.filename
        entry['payload']['file_size'] = len(data)
    await db.human_responses.insert_one(entry)
    return {'status':'received'}

@app.websocket('/connect')
async def ws_connect(websocket: WebSocket):
    await websocket.accept()
    try:
        init = await websocket.receive_json()
        session_id = init.get('session_id')
        await register_ws(session_id, websocket)
        while True:
            msg = await websocket.receive_json()
            if msg.get('type') == 'hitl_response':
                await db.human_responses.insert_one(msg)
    except WebSocketDisconnect:
        await unregister_ws(session_id)
