"""
포탈 가이드 도우미 — RAG. samsunglife_kit 적용 + governance registry 등재.
전체 가이드(97 페이지)를 chunk·임베딩한 guide_index.json 을 코사인 검색해서,
현재 페이지뿐 아니라 가이드 전체를 근거로 답한다.
"""
import json
import os
import boto3
import numpy as np
from samsunglife_kit import Agent

# ── 가이드 인덱스 로드 (cold start 1회) ─────────────────────────────
_IDX_PATH = os.path.join(os.path.dirname(__file__), "guide_index.json")
_IDX = json.load(open(_IDX_PATH, encoding="utf-8"))
_MAT = np.array([c["vector"] for c in _IDX], dtype=np.float32)
_MAT = _MAT / (np.linalg.norm(_MAT, axis=1, keepdims=True) + 1e-9)
_EMBED_MODEL = "cohere.embed-multilingual-v3"   # 한국어 retrieval + 비대칭(query/document)
_br = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "us-east-1"))


def _embed(text: str) -> np.ndarray:
    # 질문은 search_query 로 임베딩 (문서는 search_document 로 색인됨)
    r = _br.invoke_model(modelId=_EMBED_MODEL,
                         body=json.dumps({"texts": [text[:2000]], "input_type": "search_query"}))
    v = np.array(json.loads(r["body"].read())["embeddings"][0], dtype=np.float32)
    return v / (np.linalg.norm(v) + 1e-9)


def _search(query: str, k: int = 6):
    qv = _embed(query)
    sims = _MAT @ qv
    order = np.argsort(-sims)[:k]
    return [(_IDX[i], float(sims[i])) for i in order]


agent = Agent(
    name="가이드 도우미",
    agent_id="portal-guide-bot",
    platform="aws",
    model_id="anthropic.claude-sonnet-4-6",
    system_prompt=(
        "당신은 삼성생명 AgentCore/Control Plane 가이드 도우미입니다. "
        "사용자 질문과 함께 '전체 가이드 검색 결과'(관련 페이지 발췌)가 주어집니다. "
        "그 발췌를 근거로 한국어로 간결·정확하게 markdown 으로 답하세요. "
        "관련 가이드 페이지가 있으면 답변 끝에 '📄 관련 가이드' 아래 [제목](/portal/...) "
        "markdown 링크로 1~3개 안내하세요(검색 결과의 url 사용). 발췌에 없으면 추측하지 말고 모른다고 하세요."
    ),
)


@agent.invoke
def handle(ctx, req):
    full = req.input or ""
    # 질문만 뽑아 검색 (frontend 가 [질문] 마커로 보냄)
    qtext = full
    if "[질문]" in full:
        qtext = full.split("[질문]", 1)[1].strip().split("\n")[0]
    hits = _search(qtext, k=6)
    blocks = [f"### {h['title']} ({h['url']})\n{h['text']}" for h, s in hits if s > 0.15]
    retrieved = "\n\n".join(blocks)
    prompt = f"{full}\n\n[전체 가이드 검색 결과 — 아래 발췌를 근거로 답하세요]\n{retrieved}"
    for chunk in ctx.llm.stream(prompt):
        yield chunk


if __name__ == "__main__":
    agent.run()
