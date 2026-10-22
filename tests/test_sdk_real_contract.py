"""Montagem de tools/agents com o openai-agents REAL, quando instalado.

Sem chave ou chamadas de API: este teste NÃO demonstra handoff ao vivo.
"""
from __future__ import annotations
import sys
import pytest


def test_real_agents_sdk_can_build_workflow():
    pytest.importorskip('agents')
    # Outro teste usa um SDK simulado: não reutilizar workflow decorado pelo stub.
    sys.modules.pop('app.sdk_integration.workflow', None)
    from app.sdk_integration.workflow import construir_orquestrador
    orchestrator = construir_orquestrador('gpt-4o-mini')
    assert orchestrator.name == 'Orquestrador'
    assert {handoff.agent_name for handoff in orchestrator.handoffs} == {
        'Financeiro', 'Informacoes_Internas', 'Ouvidoria'
    }
