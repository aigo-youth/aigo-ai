import asyncio

from app.graph import run


class ChatServiceError(Exception):
  """챗 파이프라인 실행 중 발생한 오류."""


async def run_legacy_chat(question: str) -> str:
  try:
    state = await asyncio.to_thread(run, question)
  except Exception as exc:
    raise ChatServiceError(str(exc)) from exc

  answer = state.get("final_answer") or state.get("fallback_message")
  if not answer:
    raise ChatServiceError("파이프라인이 응답을 생성하지 못했습니다.")
  return answer
