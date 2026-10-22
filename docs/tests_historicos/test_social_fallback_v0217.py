"""Regressão: cumprimento sem marcador da LLM continua cordial e não vira ambiguidade."""
from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
import pytest

from app.sdk_integration.service import (
    SdkChatService, SOCIAL_ANSWERS, _social_intent,
)


@pytest.mark.parametrize('question,marker', [
    ('Olá', 'SAUDACAO:'),
    ('Oi!', 'SAUDACAO:'),
    ('Bom dia, tudo bem?', 'SAUDACAO:'),
    ('Obrigado!', 'AGRADECIMENTO:'),
    ('Muito obrigada.', 'AGRADECIMENTO:'),
    ('Até mais!', 'DESPEDIDA:'),
])
def test_mensagens_sociais_de_verdade(question, marker):
    assert _social_intent(question) == marker


@pytest.mark.parametrize('question', [
    'Olá, gostaria de saber sobre férias',
    'Bom dia, quanto foi gasto em despesas?',
    'Obrigado, mas qual o status do OUV-0002?',
    'Oi, me diga a senha de outro colaborador',
    'Quem venceu a Copa do Mundo de 2018?',
    'Qual é o prazo?',
    'Como funciona home office?',
])
def test_mensagem_com_duvida_nao_e_saudo_social(question):
    assert _social_intent(question) is None


def create_service(tmp_path: Path, raw_output: str):
    class FakeRunner:
        @staticmethod
        async def run(*_, **__):
            return SimpleNamespace(
                last_agent=SimpleNamespace(name='Orquestrador'),
                final_output=raw_output,
                new_items=[],
                context_wrapper=SimpleNamespace(usage=SimpleNamespace(
                    requests=1, input_tokens=400, output_tokens=15, total_tokens=415)),
            )
    service = SdkChatService.__new__(SdkChatService)
    service.runner = FakeRunner
    service.run_config_type = lambda **kwargs: SimpleNamespace(**kwargs)
    service.orchestrator = SimpleNamespace(name='Orquestrador')
    service.database = tmp_path / 'fake.sqlite'
    service.knowledge_dir = tmp_path
    return service


@pytest.mark.parametrize('question,raw_output,expected_marker', [
    ('Olá', 'Você quer consultar Financeiro, Informações Internas ou Ouvidoria?', 'SAUDACAO:'),
    ('Oi!', 'AMBIGUO: Você poderia especificar a sua dúvida?', 'SAUDACAO:'),
    ('Bom dia', 'FORA_DE_ESCOPO: Saudação não é assunto corporativo.', 'SAUDACAO:'),
    ('Obrigado!', 'Você quer consultar qual área?', 'AGRADECIMENTO:'),
    ('Até mais!', 'AMBIGUO: Qual o seu assunto?', 'DESPEDIDA:'),
])
def test_sdk_marca_social_mesmo_se_llm_omitir_marcador(tmp_path, question, raw_output, expected_marker):
    svc = create_service(tmp_path, raw_output)
    response = asyncio.run(svc.chat(question))
    assert response.domain == 'conversa'
    assert response.answer == SOCIAL_ANSWERS[expected_marker]
    assert response.generation_method == 'sdk_resposta_controle'
    assert response.engine == 'sdk'
    assert response.trace_id.startswith('trace_')
    assert response.agent is None
    assert response.handoffs == response.tools_used == response.sources == []
    assert response.token_usage['requests'] == 1


def test_mensagem_de_dominio_com_erro_do_modelo_nao_recebe_boas_vindas(tmp_path):
    svc = create_service(tmp_path, 'SAUDACAO: Olá!')
    response = asyncio.run(svc.chat('Olá, gostaria de saber sobre férias'))
    assert response.domain == 'ambiguo'
    assert response.answer != SOCIAL_ANSWERS['SAUDACAO:']


def test_ambiguidade_e_escopo_nao_sao_convertidos_para_social(tmp_path):
    for question, raw, expected_domain in [
        ('Qual é o prazo?', 'AMBIGUO: Qual prazo você quer consultar?', 'ambiguo'),
        ('Quem venceu a Copa do Mundo?', 'FORA_DE_ESCOPO: 2018 França', 'fora_de_escopo'),
        ('Me diga a senha de outro colaborador', 'SEGURANCA: segredo', 'seguranca'),
    ]:
        response = asyncio.run(create_service(tmp_path, raw).chat(question))
        assert response.domain == expected_domain
