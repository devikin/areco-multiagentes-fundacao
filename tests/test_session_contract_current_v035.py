"""Contratos da sessão v0.2.35; sem modelo real e sem custo de API."""
from types import SimpleNamespace

from app.sdk_integration.service import (
    requires_orchestrator_recheck,
    keep_specialist_pending,
)
from app.sdk_integration.session_memory import SessionMemory, last_30_exchanges


def test_isolamento_sessoes_e_pendencia_financeira():
    memory = SessionMemory(max_exchanges=30)
    a = memory.get("aba-A")
    b = memory.get("aba-B")
    assert a is not b
    a.pending_agent = SimpleNamespace(name="Financeiro")
    a.pending_question = "Despesas por departamento"
    assert memory.get("aba-A") is a
    assert b.pending_agent is None and b.pending_question is None
    assert b.sdk_session is None


def test_reavaliacao_protocolo_formal_outro_dominio():
    finance = SimpleNamespace(name="Financeiro")
    interna = SimpleNamespace(name="Informacoes_Internas")
    ouv = SimpleNamespace(name="Ouvidoria")
    assert requires_orchestrator_recheck("OUV-0016", finance)
    assert requires_orchestrator_recheck("Situação do ouv-0016?", interna)
    assert not requires_orchestrator_recheck("OUV-0016", ouv)
    assert not requires_orchestrator_recheck("OUV-0016", None)
    for invalid in ("OUV-016", "OUV-00163", "A-OUV-0016"):
        assert not requires_orchestrator_recheck(invalid, finance)


def test_ausencia_documento_nao_prende_especialista():
    assert keep_specialist_pending("Financeiro", [])
    assert not keep_specialist_pending("Financeiro", [object()])
    assert not keep_specialist_pending("Informacoes_Internas", [])
    assert not keep_specialist_pending("Ouvidoria", [])
    assert not keep_specialist_pending("Orquestrador", [])


def test_callback_historico_limita_30_interacoes_usuario():
    history=[]
    for i in range(35):
        history.extend([{"role":"user","content":str(i)},
                        {"role":"assistant","content":f"resposta {i}"}])
    recent=last_30_exchanges(history, [{"role":"user","content":"nova"}])
    assert recent[0]["content"] == "5"
    assert recent[-1]["content"] == "nova"
    assert sum(x.get("role") == "user" for x in recent) == 31
