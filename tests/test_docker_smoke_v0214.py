"""Testes offline do smoke Docker; não alegam teste real de container."""
import json
from pathlib import Path

import scripts.check_docker_http as smoke


class FakeResponse:
    status = 200

    def __init__(self, content):
        self._content = content

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return self._content


def test_health_and_frontend_no_paid_chat(monkeypatch, capsys):
    urls = []

    def fake_urlopen(req, timeout):
        urls.append(req.full_url)
        if req.full_url.endswith('/health'):
            return FakeResponse(json.dumps({'status':'ok','engine':'sdk','loaded_agents':['financeiro','informacoes_internas','ouvidoria']}).encode())
        return FakeResponse(b'<!doctype html><html lang="pt">')

    monkeypatch.setattr(smoke, 'urlopen', fake_urlopen)
    smoke.run('http://127.0.0.1:8000')
    assert urls == ['http://127.0.0.1:8000/health','http://127.0.0.1:8000/']
    assert capsys.readouterr().out.count('PASS') == 2


def test_paid_chat_only_when_explicit(monkeypatch, capsys):
    seen = []

    def fake_urlopen(req, timeout):
        seen.append(req.full_url)
        if req.full_url.endswith('/health'):
            return FakeResponse(json.dumps({'status':'ok','engine':'sdk','loaded_agents':['financeiro','informacoes_internas','ouvidoria']}).encode())
        if req.full_url.endswith('/api/v1/chat'):
            assert req.data is not None
            return FakeResponse(json.dumps({'domain':'informacoes_internas', 'handoffs':['transfer_to_informacoes_internas'],'tools_used':['buscar_documentos'], 'sources':[{'source':'01_politica_ferias.md'}], 'trace_id':'trace_mocked'}).encode())
        return FakeResponse(b'<html>mocked</html>')

    monkeypatch.setattr(smoke, 'urlopen', fake_urlopen)
    smoke.run('http://localhost:8000/', chat=True)
    assert len(seen) == 3
    assert 'api/v1/chat' in seen[-1]
    assert capsys.readouterr().out.count('PASS') == 3


def test_missing_handoff_is_failure(monkeypatch):
    def fake_fetch(url, **kwargs):
        if url.endswith('/health'):
            return 200, json.dumps({'status':'ok','engine':'sdk','loaded_agents':['financeiro','informacoes_internas','ouvidoria']}).encode()
        if url.endswith('/api/v1/chat'):
            return 200, json.dumps({'domain':'informacoes_internas','handoffs':[],'tools_used':[],'sources':[],'trace_id':'trace_mocked'}).encode()
        return 200,b'<html></html>'

    monkeypatch.setattr(smoke,'_fetch',fake_fetch)
    import pytest
    with pytest.raises(AssertionError):
        smoke.run('http://127.0.0.1:8000',chat=True)


def test_docker_compose_has_healthcheck_and_local_port():
    root=Path(__file__).resolve().parents[1]
    config=(root/'compose.yaml').read_text(encoding='utf-8')
    assert '127.0.0.1:8000:8000' in config
    assert 'healthcheck:' in config and '/health' in config
    assert 'DATABASE_PATH: /app/data/runtime/knowledge.sqlite' in config
    assert '- .env' in config
