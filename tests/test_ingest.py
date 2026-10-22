from pathlib import Path
import sqlite3
import pytest
from app.knowledge.ingest import bootstrap

def test_real_source_counts(prepared):
    _,stats,db=prepared
    assert stats=={'lancamentos':300,'orcamentos':144,'manifestacoes':180,'documentos':10,'chunks':17}
    with sqlite3.connect(db) as conn:
        assert conn.execute('SELECT COUNT(*) FROM lancamentos_financeiros').fetchone()[0]==300
        assert conn.execute('SELECT COUNT(*) FROM kb_chunks').fetchone()[0]==17

def test_fail_closed_if_missing(tmp_path):
    with pytest.raises(FileNotFoundError, match='Bases de conhecimento ausentes'):
        bootstrap(tmp_path/'missing',tmp_path/'no.sqlite')
    assert not (tmp_path/'no.sqlite').exists()


def test_sqlite_closed_before_replace(tmp_path, monkeypatch):
    """Regressão WinError 32: no Windows replace de DB aberto falha."""
    from app.knowledge import ingest
    original_connect = sqlite3.connect
    original_replace = Path.replace
    connections = []

    class TrackingConnection(sqlite3.Connection):
        closed_explicitly = False

        def close(self):
            self.closed_explicitly = True
            super().close()

    def track_connect(*args, **kwargs):
        conn = original_connect(*args, factory=TrackingConnection, **kwargs)
        connections.append(conn)
        return conn

    def verify_replace(self, target):
        assert connections and connections[-1].closed_explicitly, (
            'SQLite precisa estar fechado antes do Path.replace no Windows'
        )
        return original_replace(self, target)

    monkeypatch.setattr(ingest.sqlite3, 'connect', track_connect)
    monkeypatch.setattr(Path, 'replace', verify_replace)
    root = Path(__file__).resolve().parent.parent
    result = ingest.bootstrap(root/'data'/'knowledge', tmp_path/'test.sqlite')
    assert result['lancamentos'] == 300
    assert not (tmp_path/'test.sqlite.building').exists()
    assert connections[-1].closed_explicitly


def test_repeat_bootstrap(tmp_path):
    root = Path(__file__).resolve().parent.parent
    database = tmp_path/'knowledge.sqlite'
    first = bootstrap(root/'data'/'knowledge', database)
    second = bootstrap(root/'data'/'knowledge', database)
    assert first == second
    assert not database.with_name(database.name+'.building').exists()
    with sqlite3.connect(database) as conn:
        assert conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
