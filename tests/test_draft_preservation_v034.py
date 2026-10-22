"""v0.2.35 — mensagem sem POST é pendente; após POST incerto, nunca há retry automático."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_draft_is_kept_until_confirmed_answer():
    src = (ROOT/'frontend/app.js').read_text(encoding='utf-8')
    pre, post = src.split('async function ask(question) {', 1)[1].split('  } catch (error) {', 1)
    assert 'input.value = text;' in pre
    assert 'input.value = \'\';' in pre
    assert pre.index('input.value = text;') < pre.index('await serverAvailable()') < pre.index("input.value = '';")
    assert 'setBusy(true)' in pre
    assert 'setBusy(false)' in post


def test_no_duplicate_chat_requests():
    src = (ROOT/'frontend/app.js').read_text(encoding='utf-8')
    assert src.count("fetch('/api/v1/chat'") == 1
    assert src.count("fetch('/health'") == 1
    assert 'postStarted = true;' in src
    assert 'A solicitação pode ter sido processada' in src
    assert 'RECONNECT_CANCELLED' in src


def test_no_persisted_chat_or_secrets():
    src = (ROOT/'frontend/app.js').read_text(encoding='utf-8')
    assert 'localStorage' not in src and 'sessionStorage' not in src
    assert 'OPENAI_API_KEY' not in src
    assert 'const sessionId = crypto.randomUUID()' in src
