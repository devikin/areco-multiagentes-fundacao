"""Regressão da recuperação interna sem API externa (v0.2.9)."""
from __future__ import annotations

from contextlib import closing
import sqlite3

import pytest

from app.knowledge.retrieval import retrieve
from app.sdk_integration.tools import ExecutionContext, buscar_documentos


@pytest.fixture
def index(prepared):
    _, _, database = prepared
    with closing(sqlite3.connect(database)) as conn:
        conn.row_factory = sqlite3.Row
        yield conn


@pytest.mark.parametrize('pergunta,fonte', [
    ('Como solicito férias?', '01_politica_ferias.md'),
    ('Qual o prazo para pedir reembolso?', '02_politica_reembolso.md'),
    ('Quais aprovações para compra de R$ 12.000?', '03_aprovacao_de_compras.md'),
    ('Como reporto um e-mail de phishing?', '04_seguranca_da_informacao.md'),
    ('Posso trabalhar de casa?', '06_politica_home_office.md'),
    ('O que fazer se houver incidente de segurança?', '07_fluxo_de_incidentes.md'),
    ('Qual o procedimento para atualizar meus dados cadastrais?', '08_faq_rh.md'),
])
def test_documento_correto_entre_os_mais_relevantes(index, pergunta, fonte):
    results = retrieve(index, pergunta)
    assert results and results[0]['source'] == fonte, results
    assert results[0]['document_version']


def test_reembolso_exclui_documento_de_acesso_nao_relacionado(index):
    sources = [item['source'] for item in retrieve(index, 'Qual o prazo para pedir reembolso?')]
    assert sources == ['02_politica_reembolso.md']


def test_multiassunto_retorna_duas_politicas_sem_faq_duplicada(index):
    hits = retrieve(index, 'Como solicito férias e reembolso?')
    assert {item['source'] for item in hits} == {'01_politica_ferias.md', '02_politica_reembolso.md'}
    assert len({item['source'] for item in hits}) == len(hits)


def test_documento_completo_quando_faq_mais_relevante(index):
    hit = retrieve(index, 'Como solicito férias?')[0]
    assert hit['section'].startswith('Política de férias')
    assert hit['document_version'] == '1.2'
    assert 'Não confirmar saldo individual' in hit['content']
    assert 'liderança direta deve analisar' in hit['content']


@pytest.mark.parametrize('pergunta', [
    'Qual o nome do CEO?',
    'Quantos dias de licença maternidade?',
    'DROP TABLE kb_chunks;',
])
def test_rejeita_perguntas_sem_evidencia(index, pergunta):
    assert retrieve(index, pergunta) == []


def test_sdk_tool_registra_fonte_versao_sem_alucinar(prepared):
    _, _, db = prepared
    knowledge = __import__('pathlib').Path(__file__).resolve().parents[1] / 'data' / 'knowledge'
    context = ExecutionContext(db, knowledge, 'Como solicito férias?')
    result = buscar_documentos(context, context.question)
    assert 'VERSÃO: 1.2' in result
    assert '01_politica_ferias.md' in result
    assert 'Não confirmar saldo individual' in result
    assert context.tools_used == ['buscar_documentos']
    assert context.sources[0].detail.endswith('versão 1.2)')


def test_sdk_tool_nao_inventa_fonte_para_pergunta_sem_dados(prepared):
    _, _, db = prepared
    knowledge = __import__('pathlib').Path(__file__).resolve().parents[1] / 'data' / 'knowledge'
    context = ExecutionContext(db, knowledge, 'Quantos dias de licença maternidade?')
    output = buscar_documentos(context, context.question)
    assert 'SEM_EVIDENCIA' in output
    assert context.sources == []
    assert context.control_answer is not None


def test_senha_sensivel_devolve_politica_de_seguranca_sem_credenciais(index):
    hits = retrieve(index, 'Qual a senha de acesso da diretoria?')
    assert hits and hits[0]['source'] == '04_seguranca_da_informacao.md'
    assert 'Nunca compartilhe senhas' in hits[0]['content']
