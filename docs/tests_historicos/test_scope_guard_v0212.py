"""Regressão offline: resposta fora de escopo nunca pode vazar fatos da LLM."""
import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
import pytest

from app.sdk_integration.service import (
    OUT_OF_SCOPE_ANSWER, SECURITY_ANSWER, SdkChatService,
    _orchestrator_response,
)


@pytest.mark.parametrize('model_reply', [
    'FORA_DE_ESCOPO: A Copa do Mundo de 2018 foi vencida pela França.',
    'fora_de_escopo: Não é nosso domínio; mas foi a França.',
    'FORA_DE_ESCOPO:',
])
def test_out_of_scope_never_repeats_generated_facts(model_reply):
    domain, message = _orchestrator_response(model_reply)
    assert domain == 'fora_de_escopo'
    assert message == OUT_OF_SCOPE_ANSWER
    assert 'França' not in message
    assert '2018' not in message


def test_security_response_never_repeats_model_secrets():
    domain, message = _orchestrator_response('SEGURANCA: Não posso compartilhar. A senha é 123ABC.')
    assert domain == 'seguranca'
    assert message == SECURITY_ANSWER
    assert '123ABC' not in message


def test_ambiguous_still_requests_more_information():
    domain, message = _orchestrator_response('AMBIGUO: Qual dos prazos deseja consultar?')
    assert domain == 'ambiguo'
    assert 'Qual dos prazos' in message


def test_no_marker_discards_untrusted_orchestrator_answer():
    domain, message = _orchestrator_response('Foi a França!')
    assert domain == 'ambiguo'
    assert 'França' not in message


def test_sdk_service_never_returns_out_of_scope_factual_text(tmp_path):
    """Simula o Runner retornando classificação certa + resposta inadequada."""
    class FakeRunner:
        @staticmethod
        async def run(*args, **kwargs):
            return SimpleNamespace(
                final_output=('FORA_DE_ESCOPO: O tema não é suportado, '
                              'mas a campeã de 2018 foi a França.'),
                last_agent=SimpleNamespace(name='Orquestrador'),
                new_items=[],
                context_wrapper=SimpleNamespace(usage=SimpleNamespace(
                    requests=1, input_tokens=35, output_tokens=18, total_tokens=53)),
            )

    instance = SdkChatService.__new__(SdkChatService)
    instance.runner = FakeRunner
    instance.run_config_type = lambda **kwargs: SimpleNamespace(**kwargs)
    instance.orchestrator = SimpleNamespace(name='Orquestrador')
    instance.database = tmp_path / 'db.sqlite'
    instance.knowledge_dir = tmp_path / 'knowledge'

    result = asyncio.run(instance.chat('Quem venceu a Copa do Mundo de 2018?'))
    assert result.domain == 'fora_de_escopo'
    assert result.answer == OUT_OF_SCOPE_ANSWER
    assert result.agent is None
    assert result.sources == []
    assert result.handoffs == []
    assert result.tools_used == []
    assert result.generation_method == 'sdk_resposta_controle'
    assert result.classification_method == 'agents_sdk_orquestrador'
    assert result.trace_id.startswith('trace_')
    assert result.token_usage['total_tokens'] == 53


def test_orchestrator_instructions_explicitly_forbid_answering_off_scope():
    workflow = Path(__file__).resolve().parents[1] / 'app/sdk_integration/workflow.py'
    module = ast.parse(workflow.read_text(encoding='utf-8'))
    function = next(n for n in module.body if isinstance(n, ast.FunctionDef)
                    and n.name == 'construir_orquestrador')
    returned = next(n.value for n in function.body if isinstance(n, ast.Return))
    instructions = next(ast.literal_eval(k.value) for k in returned.keywords
                        if k.arg == 'instructions')
    assert 'NUNCA acrescente fatos' in instructions
    assert 'SEM responder à pergunta original' in instructions
