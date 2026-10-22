"""Smoke offline da cópia visual e do diagnóstico HTTP: sem chamadas à OpenAI."""
from pathlib import Path
import json
import scripts.check_ui_version_http as ui

ROOT = Path(__file__).resolve().parents[1]


def test_versioned_frontend_and_copy():
    html=(ROOT/'frontend/index.html').read_text(encoding='utf-8')
    js=(ROOT/'frontend/app.js').read_text(encoding='utf-8')
    css=(ROOT/'frontend/styles.css').read_text(encoding='utf-8')
    assert ui.GREETING in html
    assert ui.OLD_GREETING not in html
    assert 'v0.2.23</span>' in html
    assert 'MVP de avaliação' in html
    assert "renderMessage('...','bot')" in js
    assert ui.OLD_LOADING not in js
    assert 'session_id:sessionId' in js
    assert '.release-version{' in css


def test_ui_http_version_check_success(monkeypatch, capsys):
    html=(ROOT/'frontend/index.html').read_text(encoding='utf-8')
    js=(ROOT/'frontend/app.js').read_text(encoding='utf-8')
    css=(ROOT/'frontend/styles.css').read_text(encoding='utf-8')
    def fake_fetch(url):
        if url.endswith('/openapi.json'):return json.dumps({'info':{'version':ui.VERSION}})
        if '/static/app.js?' in url:return js
        if '/static/styles.css?' in url:return css
        return html
    monkeypatch.setattr(ui,'fetch',fake_fetch)
    ui.check('http://127.0.0.1:8000')
    assert capsys.readouterr().out.count('PASS')==4


def test_ui_http_version_check_detects_outdated_docker(monkeypatch):
    monkeypatch.setattr(ui,'fetch',lambda url: '<html>Olá! Consulte lançamentos financeiros</html>')
    import pytest
    with pytest.raises(AssertionError, match='HTML antigo'):
        ui.check('http://127.0.0.1:8000')


def test_fastapi_exposes_release_version():
    from app.main import app
    assert app.version == ui.VERSION
