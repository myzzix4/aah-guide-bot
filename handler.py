"""
포탈 가이드 도우미 — samsunglife_kit · governance registry 등재.
검색(RAG)은 Control Plane 의 가이드 KB 가 담당하고, 이 Runtime 은 LLM 답변만 한다.
(Control Plane 이 검색 결과를 input 에 실어 보냄 → 핸들러는 가볍게 stream 만)
"""
from samsunglife_kit import Agent

agent = Agent(
    name="가이드 도우미",
    agent_id="portal-guide-bot",
    platform="aws",
    model_id="anthropic.claude-sonnet-4-6",
    system_prompt=(
        "당신은 삼성생명 AgentCore/Control Plane 가이드 도우미입니다. "
        "사용자 질문과 함께 'Control Plane 가이드 KB 검색 결과'(관련 페이지 발췌)가 주어집니다. "
        "그 발췌를 근거로 한국어로 간결·정확하게 markdown 으로 답하세요. "
        "관련 가이드 페이지가 있으면 답변 끝에 '📄 관련 가이드' 아래 [제목](/portal/...) "
        "markdown 링크로 1~3개 안내하세요. 발췌에 없으면 추측하지 말고 모른다고 하세요."
    ),
)


@agent.invoke
def handle(ctx, req):
    # Control Plane 이 검색 결과를 input 에 포함해 보냄 → LLM stream
    for chunk in ctx.llm.stream(req.input):
        yield chunk


if __name__ == "__main__":
    agent.run()
