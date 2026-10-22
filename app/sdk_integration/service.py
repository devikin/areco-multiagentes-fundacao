"""Chat com geração exclusiva pela LLM e memória nativa do OpenAI Agents SDK."""
from __future__ import annotations

import os
import re
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from app.schemas import ChatResponse
from app.sdk_integration.tools import ExecutionContext
from app.sdk_integration.session_memory import SessionMemory, SessionState, last_30_exchanges

# Identificador formal, não classificação semântica de domínio nem redação de resposta.
OUVIDORIA_ID = re.compile(r'(?<![\w-])OUV-\d{4}(?![\w-])', re.IGNORECASE)


def requires_orchestrator_recheck(message: str, pending_agent: object | None) -> bool:
    """Um novo identificador de outro domínio não pode ficar preso ao especialista anterior."""
    return (pending_agent is not None
            and getattr(pending_agent, 'name', None) != 'Ouvidoria'
            and OUVIDORIA_ID.search(message) is not None)


def keep_specialist_pending(agent_name: str, sources: list) -> bool:
    """Só o Financeiro retém o esclarecimento necessário para plano validado.

    Sem evidência em busca documental não é uma solicitação de esclarecimento;
    confundir os dois estados causava o lock-in entre departamentos.
    """
    return agent_name == 'Financeiro' and not sources


DOMAIN_BY_AGENT = {
    'Financeiro': 'financeiro',
    'Informacoes_Internas': 'informacoes_internas',
    'Ouvidoria': 'ouvidoria',
}


class SdkChatService:
    def __init__(self, database: Path, knowledge_dir: Path):
        if not os.getenv('OPENAI_API_KEY'):
            raise RuntimeError('Agents SDK requer OPENAI_API_KEY no .env.')
        try:
            from agents import Runner, RunConfig, SQLiteSession
            from app.sdk_integration.workflow import construir_orquestrador
        except ImportError as exc:
            raise RuntimeError('Instale openai-agents: pip install -r requirements.txt') from exc
        self.runner = Runner
        self.run_config_type = RunConfig
        self.sdk_session_type = SQLiteSession
        self.orchestrator = construir_orquestrador(os.getenv('OPENAI_MODEL', 'gpt-4.1-mini'))
        self.database = database
        self.knowledge_dir = knowledge_dir
        self.sessions = SessionMemory(ttl_seconds=1800, max_sessions=200, max_exchanges=30)
        self.agents = {key: True for key in DOMAIN_BY_AGENT.values()}

    async def chat(self, message: str, session_id: str | None = None) -> ChatResponse:
        state = self.sessions.get(session_id) if session_id else None
        if state is None:
            return await self._run_chat(message, state=None, session_id=None)
        async with state.lock:
            return await self._run_chat(message, state=state, session_id=session_id)

    async def _run_chat(self, message: str, *, state: SessionState | None,
                        session_id: str | None) -> ChatResponse:
        start = perf_counter()
        request_id = str(uuid4())
        trace_id = 'trace_' + uuid4().hex
        # Mantém o texto original para o modelo. Quando o especialista ainda
        # precisa de um dado, o contexto da ferramenta inclui a pergunta inicial
        # para impedir a perda de filtros; não é usado para redigir respostas.
        active_pending = state.pending_agent if state is not None else None
        switch_to_router = requires_orchestrator_recheck(message, active_pending)
        pending = state.pending_question if state is not None and not switch_to_router else None
        # O contexto antigo nunca contamina uma nova consulta formal da Ouvidoria.
        tool_question = f'{pending} | Complemento: {message}' if pending else message
        context = ExecutionContext(database=self.database, knowledge_dir=self.knowledge_dir,
                                   question=tool_question)
        sdk_session = None
        if state is not None:
            if state.sdk_session is None:
                state.sdk_session = self.sdk_session_type(session_id)
            sdk_session = state.sdk_session
        # Reutilizar o especialista após um esclarecimento é nativo do SDK:
        # o histórico continua na sessão e a entrada do usuário não é reescrita.
        # Um novo assunto pode voltar ao Orquestrador por handoff do especialista.
        initial_agent = (active_pending if active_pending is not None and not switch_to_router
                         else self.orchestrator)
        result = await self.runner.run(
            initial_agent, message, context=context, session=sdk_session, max_turns=10,
            run_config=self.run_config_type(
                workflow_name='Areco | Conversacional SDK',
                trace_id=trace_id,
                trace_include_sensitive_data=False,
                trace_metadata={'ambiente': 'api', 'arquitetura': 'agents_sdk'},
                session_input_callback=last_30_exchanges,
            ),
        )
        handoffs = [item.raw_item.name for item in result.new_items
                    if item.type == 'handoff_call_item' and hasattr(item.raw_item, 'name')]
        tool_events = [item.raw_item.name for item in result.new_items
                       if item.type == 'tool_call_item' and hasattr(item.raw_item, 'name')]
        answer = str(result.final_output or '').strip()
        if not answer:
            # Sem resposta da LLM: é um erro de execução, não uma resposta inventada.
            raise RuntimeError('Agents SDK concluiu sem gerar uma mensagem.')
        domain = DOMAIN_BY_AGENT.get(result.last_agent.name, 'conversa')
        if state is not None:
            if keep_specialist_pending(result.last_agent.name, context.sources):
                # Falta de evidência documental não significa esclarecimento
                # pendente. Preservamos apenas o plano financeiro incompleto;
                # respostas seguintes de outros domínios voltam ao Orquestrador.
                state.pending_agent = result.last_agent
                if state.pending_question is None or result.last_agent.name != initial_agent.name:
                    state.pending_question = message
            else:
                state.pending_agent = None
                state.pending_question = None
        usage = result.context_wrapper.usage
        return ChatResponse(
            request_id=request_id,
            session_id=session_id,
            answer=answer,
            domain=domain,
            agent=domain if domain in DOMAIN_BY_AGENT.values() else None,
            sources=context.sources if domain in DOMAIN_BY_AGENT.values() else [],
            classification_method=('agents_sdk_handoff' if handoffs else
                                   'agents_sdk_especialista_em_continuidade'
                                   if initial_agent is not self.orchestrator
                                   else 'agents_sdk_orquestrador'),
            confidence=0.0,
            latency_ms=round((perf_counter() - start) * 1000),
            generation_method='agents_sdk_llm',
            engine='sdk',
            trace_id=trace_id,
            handoffs=handoffs,
            tools_used=tool_events or context.tools_used,
            token_usage={
                'requests': usage.requests,
                'input_tokens': usage.input_tokens,
                'output_tokens': usage.output_tokens,
                'total_tokens': usage.total_tokens,
            },
        )
