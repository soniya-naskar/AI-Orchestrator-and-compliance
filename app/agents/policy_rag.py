import asyncio
from ..storage import get_qdrant_client
from ..config import settings
from ..embeddings import embed_text

async def policy_rag(query, top_k=None):
    top_k = top_k or settings.TOP_K
    client = get_qdrant_client()
    vec = embed_text(query)
    try:
        res = client.search(collection_name='policies', query_vector=vec, limit=top_k)
        out = []
        for hit in res:
            payload = hit.payload or {}
            out.append({'doc_id': payload.get('doc_id','unknown'), 'chunk_id': payload.get('chunk_id','0'), 'snippet': payload.get('text',''), 'score': float(hit.score)})
        return out
    except Exception as e:
        # fallback to simple stub
        await asyncio.sleep(0.05)
        return [{'doc_id':'policy-x','chunk_id':'c1','snippet':'MFA required for remote login','score':0.9}]
