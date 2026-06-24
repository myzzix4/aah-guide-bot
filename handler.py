"""
포탈 가이드 도우미 — samsunglife_kit 적용. governance registry 자동 등재.
frontend 가 '현재 페이지 내용 + 질문' 을 input 으로 합쳐 보내고, 가이드 근거로 답변.
"""
from samsunglife_kit import Agent

agent = Agent(
    name="가이드 도우미",
    agent_id="portal-guide-bot",                 # 고정 ID — register dedup (한글 이름 해시 회피)
    platform="aws",                              # 2.4.1 — registry zone
    model_id="anthropic.claude-sonnet-4-6",
    system_prompt=(
        "당신은 삼성생명 AgentCore/Control Plane 가이드 도우미입니다. "
        "사용자가 보고 있는 가이드 페이지 내용과 질문이 함께 주어집니다. "
        "그 내용을 근거로 한국어로 간결·정확하게 답하세요. 페이지에 없는 건 일반 지식으로 "
        "보완하되 추측은 피하고, 모르면 모른다고 하세요."
    ),
)


@agent.invoke
def handle(ctx, req):
    # req.input = "[페이지]\n...\n\n[질문]\n..." (frontend 가 합쳐 보냄)
    for chunk in ctx.llm.stream(req.input):
        yield chunk


if __name__ == "__main__":
    agent.run()   # 0.0.0.0:8080 /invocations
