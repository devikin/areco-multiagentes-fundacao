"""v0.2.32 — regressão da saudação única na interface.

Validação estática: confirma que o prompt não obriga a reabrir o atendimento.
A observação do comportamento real da LLM exige script HTTP separado.
"""
from pathlib import Path
import ast
import re

ROOT = Path(__file__).resolve().parents[1]


def test_initial_welcome_owned_only_by_frontend():
    html = (ROOT/'frontend/index.html').read_text(encoding='utf-8')
    source = (ROOT/'app/sdk_integration/workflow.py').read_text(encoding='utf-8')
    assert html.count('Olá, como posso te ajudar hoje?') == 1
    assert 'A interface do chat já apresenta' in source
    assert 'não repita essa mensagem' in source
    assert 'Ao iniciar um atendimento, cumprimente' not in source
    assert 'sem abrir automaticamente' in source
    assert 'Se houver uma saudação junto com uma pergunta' in source
    ast.parse(source)


def test_no_frontend_automatic_greeting_on_submit():
    # O JS apenas exibe data.answer; não cola a saudação no texto da LLM.
    js = (ROOT/'frontend/app.js').read_text(encoding='utf-8')
    assert 'renderMessage(data.answer' in js
    assert 'Olá, como posso te ajudar hoje?' not in js


def test_backend_and_frontend_version_bumped():
    html = (ROOT/'frontend/index.html').read_text(encoding='utf-8')
    backend = (ROOT/'app/main.py').read_text(encoding='utf-8')
    assert 'v0.2.35' in html
    assert "version='0.2.35'" in backend


def test_handoff_and_guardrails_still_present():
    src = (ROOT/'app/sdk_integration/workflow.py').read_text(encoding='utf-8')
    assert 'não prometa localizar uma manifestação individual' in src
    assert 'descarte só a ordem indevida' in src
    assert "ModelSettings(tool_choice='required')" in src
    assert src.count('reset_tool_choice=True') == 3
    assert src.count('tools=[') == 3
    assert 'handoff(financeiro), handoff(internas), handoff(ouvidoria)' in src
