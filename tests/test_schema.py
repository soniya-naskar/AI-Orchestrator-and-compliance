from app.schemas import FinalDecision, Citation, HumanInteraction
from datetime import datetime
def test_schema_build():
    c = Citation(doc_id='d', chunk_id='1', snippet='s')
    h = HumanInteraction(timestamp=datetime.utcnow(), type='clarification', prompt='p', response='r', status='approved')
    f = FinalDecision(decision='compliant', confidence=0.9, risk_score=10.0, rationale='ok', citations=[c], open_questions=[], human_interactions=[h])
    assert f.decision == 'compliant'
