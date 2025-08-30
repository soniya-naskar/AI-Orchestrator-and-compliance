"""Index sample docs into Qdrant collection 'policies' and 'evidence'. Requires qdrant running and the qdrant-client package."""
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from app.embeddings import embed_text
import json
import os

client = QdrantClient(url=os.getenv('QDRANT_URL','http://localhost:6333'))

def ensure_collection(name):
    try:
        client.recreate_collection(collection_name=name, vectors_config=qmodels.VectorParams(size=32, distance=qmodels.Distance.COSINE))
    except Exception as e:
        print('ensure collection error', e)

def index_docs(collection, docs):
    points = []
    for i, doc in enumerate(docs):
        vec = embed_text(doc['text'])
        points.append(qmodels.PointStruct(id=i, vector=vec, payload={'doc_id': doc['doc_id'], 'chunk_id': doc['chunk_id'], 'text': doc['text']}))
    client.upsert(collection_name=collection, point_request=qmodels.PointsList(points=points))

if __name__ == '__main__':
    policies = [{'doc_id':'policy-x','chunk_id':'p1','text':'Policy-X: All remote logins MUST enforce MFA for interactive sessions.'}]
    evidence = [{'doc_id':'product-spec','chunk_id':'e1','text':'Product: Mobile login supports OTP via SMS. No TOTP configured.'}]
    ensure_collection('policies')
    ensure_collection('evidence')
    index_docs('policies', policies)
    index_docs('evidence', evidence)
    print('Indexed sample docs.')
