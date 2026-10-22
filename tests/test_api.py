"""Contratos do backend sem chamadas reais à OpenAI."""
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_sdk_is_only_available_engine(monkeypatch, tmp_path):
    monkeypatch.setenv('AGENT_ENGINE', 'legacy')
    monkeypatch.setenv('DATABASE_PATH', str(tmp_path / 'db.sqlite'))
    with pytest.raises(RuntimeError, match='exclusivamente Agents SDK'):
        with TestClient(app):
            pass

def test_invalid_short_question_rejected_by_schema():
    from app.schemas import ChatRequest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        ChatRequest(message='a')

def test_windows_default_database_is_local(tmp_path):
    from app.main import default_database_path
    fake_local = str(tmp_path / 'AppData' / 'Local')
    path = default_database_path(tmp_path / 'Drive project', platform='win32',
                                 local_appdata=fake_local)
    assert path == Path(fake_local) / 'ArecoMultiagentes' / 'knowledge.sqlite'
    assert 'Drive project' not in str(path)


def test_nonwindows_database_path_default(tmp_path):
    from app.main import default_database_path
    path = default_database_path(tmp_path, platform='linux')
    assert path == tmp_path / 'data' / 'runtime' / 'knowledge.sqlite'
