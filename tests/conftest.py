"""Fixtures de dados sintéticos — não requer rede ou modelo."""
from pathlib import Path
import pytest
from app.knowledge.ingest import bootstrap

ROOT = Path(__file__).resolve().parent.parent

@pytest.fixture
def prepared(tmp_path):
    db = tmp_path / 'test.sqlite'
    stats = bootstrap(ROOT / 'data' / 'knowledge', db)
    return None, stats, db
