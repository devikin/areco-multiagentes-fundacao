from typing import Literal
from pydantic import BaseModel, Field

Domain = Literal['financeiro','informacoes_internas','ouvidoria','ambiguo','fora_de_escopo','seguranca','conversa','esclarecimento']

class ChatRequest(BaseModel):
    message: str = Field(min_length=2,max_length=1500)
    session_id: str | None = Field(default=None,max_length=80)

class Citation(BaseModel):
    source: str
    detail: str | None = None

class ChatResponse(BaseModel):
    request_id: str
    session_id: str | None = None
    answer: str
    domain: Domain
    agent: str | None
    sources: list[Citation] = Field(default_factory=list)
    classification_method: str
    confidence: float
    latency_ms: int
    generation_method: str = 'nao_aplicavel'
    classification_error: str | None = None
    generation_error: str | None = None
    # Campos de rastreabilidade do Agents SDK.
    engine: Literal['sdk'] = 'sdk'
    trace_id: str | None = None
    handoffs: list[str] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)
    token_usage: dict[str, int] | None = None
