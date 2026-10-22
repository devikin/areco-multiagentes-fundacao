"""v0.2.35 — contrato de UI e resiliência, sem chamadas externas."""
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def test_release_versions_aligned():
    main = (ROOT/'app/main.py').read_text(encoding='utf-8')
    html = (ROOT/'frontend/index.html').read_text(encoding='utf-8')
    assert "version='0.2.35'" in main
    assert '>v0.2.35</span>' in html
    assert '/static/app.js?v=0.2.35' in html
    assert '/static/styles.css?v=0.2.35' in html
    ast.parse(main)


def test_frontend_timeout_and_single_post():
    js = (ROOT/'frontend/app.js').read_text(encoding='utf-8')
    assert 'const REQUEST_TIMEOUT_MS = 120000;' in js
    assert "fetch('/api/v1/chat'" in js
    assert js.count("fetch('/api/v1/chat'") == 1
    assert 'new AbortController()' in js
    assert 'clearTimeout(timeoutId)' in js
    assert 'input.value = text;' in js
    assert "input.value = '';" in js
    assert 'if (send.disabled) return;' in js
    assert 'examples.forEach(button => { button.disabled = busy; });' in js
    assert 'renderMessage(data.answer' in js
    assert 'bubble.textContent = text' in js


def test_preflight_and_overlay_exist():
    js = (ROOT/'frontend/app.js').read_text(encoding='utf-8')
    html = (ROOT/'frontend/index.html').read_text(encoding='utf-8')
    css = (ROOT/'frontend/styles.css').read_text(encoding='utf-8')
    assert "fetch('/health'" in js
    assert 'cache: \'no-store\'' in js
    assert 'await serverAvailable()' in js
    assert 'await waitForServer()' in js
    assert 'id="reconnectOverlay"' in html
    assert 'id="reconnectCancel"' in html
    assert 'backdrop-filter:blur(' in css
    assert '@keyframes reconnect-rotate' in css


def test_prompts_and_tools_not_changed():
    # A suíte de conversação precisa continuar passando após aplicar o patch.
    workflow = ROOT/'app/sdk_integration/workflow.py'
    if workflow.exists():
        assert 'A interface do chat já apresenta' in workflow.read_text(encoding='utf-8')
