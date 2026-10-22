"""Contrato estático das instruções v0.2.10; não substitui testes reais do LLM.

Garante que termos e exemplos críticos do roteamento sejam mantidos ao editar prompts,
sem acoplar a suíte offline à instalação do SDK externo.
"""
from __future__ import annotations

import ast
from pathlib import Path


WORKFLOW = Path(__file__).resolve().parents[1] / 'app' / 'sdk_integration' / 'workflow.py'


def _policy() -> tuple[str, str, str]:
    module = ast.parse(WORKFLOW.read_text(encoding='utf-8'))
    builder = next(item for item in module.body if isinstance(item, ast.FunctionDef)
                   and item.name == 'construir_orquestrador')
    root_call = next(item.value for item in builder.body if isinstance(item, ast.Return))
    internal_call = next(item.value for item in builder.body if isinstance(item, ast.Assign)
                         and any(isinstance(target, ast.Name) and target.id == 'internas'
                                 for target in item.targets))
    kw = lambda call, name: next(ast.literal_eval(arg.value) for arg in call.keywords
                                  if arg.arg == name)
    return kw(root_call, 'instructions'), kw(internal_call, 'instructions'), kw(internal_call, 'handoff_description')


def test_domain_recognizable_questions_should_not_be_marked_ambiguous():
    router, _, description = _policy()
    assert 'classifique pelo ASSUNTO' in router
    assert 'execute o handoff' in router
    for question in ('Posso trabalhar de casa?', 'Tenho direito a home office?',
                     'Como funciona o trabalho remoto?'):
        assert question in router
    assert 'home office' in description and 'trabalho remoto' in description


def test_genuine_ambiguity_and_safety_remain_supported():
    router, specialist, _ = _policy()
    assert all(prefix in router for prefix in ('AMBIGUO:', 'FORA_DE_ESCOPO:', 'SEGURANCA:'))
    assert 'Qual é o prazo?' in router
    assert 'sem confirmar permissão pessoal' in specialist
    assert 'buscar_documentos' in specialist
