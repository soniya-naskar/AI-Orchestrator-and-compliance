import asyncio, uuid, json
from datetime import datetime
from .agents import policy_rag, evidence_rag, vision_ocr, code_scanner, risk_scorer
from .hitl import send_hitl_request, wait_for_response
from .schemas import FinalDecision, Citation, HumanInteraction
from .storage import db, redis

async def run_pipeline(session_id, question, artifacts):
    # persist plan to Mongo
    plan = {'session_id': session_id, 'question': question, 'created_at': datetime.utcnow().isoformat()}
    plan_id = str(uuid.uuid4())
    await db.plans.insert_one({'plan_id': plan_id, 'plan': plan})
    # collectors in parallel
    tasks = [
        asyncio.create_task(policy_rag.policy_rag(question)),
        asyncio.create_task(evidence_rag.evidence_rag(question)),
        asyncio.create_task(vision_ocr.ocr_image_bytes(artifacts.get('images', b''))),
    ]
    code_issues = []
    if artifacts.get('code'):
        code_issues = code_scanner.scan_code_snippet(artifacts['code'])

    results = await asyncio.gather(*tasks, return_exceptions=True)
    policy_hits, evidence_hits, ocr_hits = results

    # cache top results in redis for a short TTL
    try:
        await redis.set(f'last:{session_id}', json.dumps({'policy':policy_hits,'evidence':evidence_hits,'ocr':ocr_hits}), ex=300)
    except Exception:
        pass

    score = risk_scorer.compute_risk(policy_hits, evidence_hits + ocr_hits, code_issues)
    open_questions = []
    if score > 50:
        open_questions.append('Which MFA method is used in mobile login?')

    human_interactions = []
    if open_questions:
        request_id = str(uuid.uuid4())
        prompt = 'Which MFA method is used in mobile login? (options: sms_otp, push, totp, none)'
        payload = {'prompt': prompt, 'required_artifact': None}
        sent = await send_hitl_request(session_id, request_id, payload)
        if sent:
            # Wait for human response via Mongo/pubsub
            resp = await wait_for_response(request_id, timeout=30)
            if resp:
                answer = resp.get('payload', {}).get('answer', 'sms_otp')
                human_interactions.append(HumanInteraction(timestamp=datetime.utcnow(), type='clarification', prompt=prompt, response=answer, status='approved'))
                if answer == 'sms_otp':
                    score -= 10
            else:
                human_interactions.append(HumanInteraction(timestamp=datetime.utcnow(), type='clarification', prompt=prompt, response=None, status='timeout'))
                final = FinalDecision(
                    decision='insufficient_evidence',
                    confidence=0.2,
                    risk_score=score,
                    rationale='Timed out waiting for human clarification.',
                    citations=[Citation(doc_id='policy-x', chunk_id='c1', snippet='MFA required for remote login')],
                    open_questions=open_questions,
                    human_interactions=human_interactions
                )
                return final

    citations = []
    for x in (policy_hits + evidence_hits + ocr_hits):
        if isinstance(x, dict):
            citations.append(Citation(doc_id=x['doc_id'], chunk_id=x['chunk_id'], snippet=x['snippet']))

    if score < 30:
        decision = 'compliant'; confidence = 0.85
    elif score < 70:
        decision = 'insufficient_evidence'; confidence = 0.5
    else:
        decision = 'non_compliant'; confidence = 0.9

    final = FinalDecision(
        decision=decision,
        confidence=confidence,
        risk_score=score,
        rationale=f'Automated aggregation: score {score}. See citations.',
        citations=citations,
        open_questions=[],
        human_interactions=human_interactions
    )
    # persist result
    await db.results.insert_one({'session_id':session_id,'result': final.dict(), 'created_at': datetime.utcnow().isoformat()})
    return final
