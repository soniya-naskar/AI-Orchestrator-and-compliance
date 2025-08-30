import asyncio
from app.orchestrator import run_pipeline
import pytest

@pytest.mark.asyncio
async def test_pipeline_completes():
    final = await run_pipeline('test-session', 'Does login require MFA?', {'code': 'allow_weak_mfa = True', 'images': None})
    assert final.risk_score >= 0
    assert final.decision in ('compliant','non_compliant','insufficient_evidence')
