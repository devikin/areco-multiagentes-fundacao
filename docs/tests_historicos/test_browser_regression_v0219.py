"""v0.2.19: reproduce o diálogo reportado no navegador, com Runner simulado."""
from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

from app.knowledge.ingest import bootstrap
from app.sdk_integration.finance_queries import FinancePlan
from app.sdk_integration.service import SdkChatService, _orchestrator_response
from app.sdk_integration.session_memory import SessionMemory
from app.sdk_integration.tools import consultar_financeiro, buscar_documentos

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / 'data/knowledge'


def result(agent, answer, handoff=None, tool=None):
    items = []
    if handoff:
        items.append(SimpleNamespace(type='handoff_call_item', raw_item=SimpleNamespace(name='transfer_to_'+handoff)))
    if tool:
        items.append(SimpleNamespace(type='tool_call_item', raw_item=SimpleNamespace(name=tool)))
    return SimpleNamespace(last_agent=SimpleNamespace(name=agent), final_output=answer,
       new_items=items, context_wrapper=SimpleNamespace(usage=SimpleNamespace(
       requests=2, input_tokens=400, output_tokens=50, total_tokens=450)))


def create_service(tmp_path, runner):
    database = tmp_path / 'knowledge.sqlite'
    bootstrap(KB, database)
    obj = SdkChatService.__new__(SdkChatService)
    obj.runner = runner
    obj.orchestrator = SimpleNamespace(name='Orquestrador')
    obj.run_config_type = lambda **kwargs: SimpleNamespace(**kwargs)
    obj.database = database
    obj.knowledge_dir = KB
    obj.sessions = SessionMemory(max_exchanges=8)
    return obj


def test_unmarked_natural_questions_preserved():
    cases = (
       'Claro! Sobre o que você gostaria de conversar?',
       'Você deseja saber sobre o total de despesas, a distribuição por categoria ou departamento?',
       'Qual ano gostaria de analisar?',
       'Claro! De qual ano deseja ver as despesas por departamento?',
    )
    for utterance in cases:
        assert _orchestrator_response(utterance) == ('esclarecimento', utterance)
    # Respostas factuais da LLM, mesmo com interrogação, não viram uma resposta confiável.
    for text in ('Foi a França!', 'A campeã foi França, certo?',
                 'O resultado é R$ 12.345,67, quer saber mais?'):
        domain, answer = _orchestrator_response(text)
        assert domain == 'ambiguo'
        assert 'França' not in answer and '12.345' not in answer


def test_never_show_generic_three_domains_menu():
    for text in (
       'Você quer consultar Financeiro, Informações Internas ou Ouvidoria?',
       'AMBIGUO: Você quer consultar Financeiro, Informações Internas ou Ouvidoria?',
       'ESCLARECER: Você quer consultar Financeiro, Informações Internas ou Ouvidoria?',
    ):
        domain, answer = _orchestrator_response(text)
        assert domain == 'esclarecimento'
        assert 'Financeiro' not in answer and 'Ouvidoria' not in answer
        assert '?' in answer


def test_browser_sequence_with_unmarked_and_tool_clarification(tmp_path):
    class FakeRunner:
        count = 0

        @staticmethod
        async def run(agent, prompt, *, context, **kwargs):
            FakeRunner.count += 1
            idx = FakeRunner.count
            if idx == 1:
                return result('Orquestrador', 'SAUDACAO: Olá!')
            if idx == 2:
                return result('Orquestrador', 'Claro! Sobre o que você gostaria de conversar?')
            if idx == 3:
                assert isinstance(prompt, list)
                docs = buscar_documentos(context, 'sobre as férias')
                assert '01_politica_ferias.md' in docs
                return result('Informacoes_Internas', 'Férias solicitadas pelo portal interno.',
                              handoff='informacoes_internas', tool='buscar_documentos')
            if idx == 4:
                return result('Orquestrador', 'ESCLARECER: Claro! Qual é a sua nova dúvida?')
            if idx == 5:
                return result('Orquestrador', 'Você quer consultar o total das despesas ou ver por departamento?')
            if idx == 6:
                assert 'sobre despesas' in context.question.casefold()
                query = consultar_financeiro(context, FinancePlan(
                    dataset='lancamentos', operation='agrupar', group_by='departamento',
                    transaction_type='Despesa'))
                assert 'Informe o ano' in query
                return result('Financeiro', 'ESCLARECER: Qual ano?',
                              handoff='financeiro', tool='consultar_financeiro')
            if idx == 7:
                assert 'sobre despesas' in context.question.casefold()
                assert 'departamento' in context.question.casefold()
                assert '2025' in context.question
                response = consultar_financeiro(context, FinancePlan(
                    dataset='lancamentos', operation='agrupar', year=2025,
                    group_by='departamento', transaction_type='Despesa'))
                assert 'por departamento' in response
                return result('Financeiro', response,
                              handoff='financeiro', tool='consultar_financeiro')
            raise AssertionError('Unexpected FakeRunner call')

    svc = create_service(tmp_path, FakeRunner)
    sequence = ['ola', 'queria tirar uma duvida', 'sobre as ferias',
                'certo..tenho outra duvida', 'sobre despesas', 'departamento', '2025']

    async def test():
        results = [await svc.chat(q, session_id='browser-A') for q in sequence]
        assert [r.domain for r in results] == [
            'conversa', 'esclarecimento', 'informacoes_internas', 'esclarecimento',
            'esclarecimento', 'esclarecimento', 'financeiro']
        assert all('Você quer consultar Financeiro' not in r.answer for r in results)
        assert 'ano' in results[5].answer.lower()
        assert results[6].sources[0].source == 'lancamentos_financeiros.csv'
        assert results[6].tools_used == ['consultar_financeiro']
        assert svc.sessions.get('browser-A').pending_questions == []
    asyncio.run(test())


def test_pending_persists_six_clarification_turns_and_isolation():
    mem = SessionMemory(max_exchanges=8)
    state = mem.get('A')
    for i in range(6):
        state.record(f'despesas passo {i}', 'Pode especificar?',
                     needs_clarification=True, reset_pending=True, max_exchanges=8)
    assert 'despesas passo 0' in state.contextual_question('2025')
    assert mem.get('B').contextual_question('2025') == '2025'
    state.record('2025', 'Consulta executada', needs_clarification=False,
                 reset_pending=True, max_exchanges=8)
    assert state.pending_questions == []
