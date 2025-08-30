import uuid, asyncio, json, os
from typing import Dict, Any
from .storage import db, redis

WS_CLIENTS: Dict[str, Any] = {}
PENDING = {}  # in-memory pending responses for demo

async def register_ws(session_id: str, websocket):
    WS_CLIENTS[session_id] = websocket

async def unregister_ws(session_id: str):
    WS_CLIENTS.pop(session_id, None)

async def send_hitl_request(session_id: str, request_id: str, payload):
    ws = WS_CLIENTS.get(session_id)
    entry = {'session_id':session_id,'request_id':request_id,'payload':payload,'sent_at':None}
    if not ws:
        # persist to Mongo for REST poll or fallback
        await db.hitl.insert_one(entry)
        PENDING[request_id] = entry
        return False
    await ws.send_json({ 'type':'hitl_request', 'session_id':session_id, 'request_id':request_id, 'payload':payload })
    PENDING[request_id] = entry
    return True

async def wait_for_response(request_id, timeout=60):
    # simple polling for demo; production should use pubsub/event system
    waited = 0
    while waited < timeout:
        # check in Mongo for response
        rec = await db.human_responses.find_one({'request_id': request_id})
        if rec:
            return rec
        await asyncio.sleep(1)
        waited += 1
    return None
