from pydantic import BaseModel, Field


class LegacyChatRequest(BaseModel):
  question: str = Field(..., min_length=1, max_length=10_000)


class LegacyChatResponse(BaseModel):
  answer: str
