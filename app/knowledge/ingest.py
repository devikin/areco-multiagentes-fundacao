"""Importação validada dos dados sintéticos. Não executa SQL gerado pelo LLM."""
from __future__ import annotations

import csv
from contextlib import closing
import json
import re
import sqlite3
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS lancamentos_financeiros (
 id_lancamento TEXT PRIMARY KEY, data_competencia TEXT NOT NULL,
 data_vencimento TEXT NOT NULL, tipo TEXT NOT NULL CHECK(tipo IN ('Receita','Despesa')),
 categoria TEXT NOT NULL, descricao TEXT NOT NULL, centro_custo TEXT NOT NULL,
 departamento TEXT NOT NULL, contraparte TEXT NOT NULL, valor_brl TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('Pago','Pendente','Atrasado')),
 metodo_pagamento TEXT, observacao TEXT
);
CREATE TABLE IF NOT EXISTS orcamento_mensal (
 ano INTEGER NOT NULL, mes TEXT NOT NULL, centro_custo TEXT NOT NULL,
 departamento TEXT NOT NULL, orcamento_brl TEXT NOT NULL,
 versao_orcamento TEXT NOT NULL, observacao TEXT,
 PRIMARY KEY (ano, mes, centro_custo)
);
CREATE TABLE IF NOT EXISTS manifestacoes_ouvidoria (
 protocolo TEXT PRIMARY KEY, data_abertura TEXT NOT NULL, categoria TEXT NOT NULL,
 assunto TEXT NOT NULL, canal_entrada TEXT NOT NULL, prioridade TEXT NOT NULL,
 status TEXT NOT NULL, area_responsavel TEXT NOT NULL, resumo_manifestacao TEXT NOT NULL,
 data_resposta TEXT, resposta_resumo TEXT, prazo_referencia_dias INTEGER NOT NULL,
 dados_pessoais TEXT, observacao TEXT
);
CREATE TABLE IF NOT EXISTS kb_chunks (
 id INTEGER PRIMARY KEY, source TEXT NOT NULL, section TEXT NOT NULL,
 content TEXT NOT NULL, domain TEXT NOT NULL, document_version TEXT
);
CREATE INDEX IF NOT EXISTS idx_fin_comp ON lancamentos_financeiros(data_competencia, tipo);
CREATE INDEX IF NOT EXISTS idx_ouv_status ON manifestacoes_ouvidoria(status);
"""


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def _money(value: str) -> str:
    try:
        amount = Decimal(value)
        if not amount.is_finite() or amount < 0 or amount.as_tuple().exponent < -2:
            raise ValueError('valor monetário inválido')
        return str(amount.quantize(Decimal('0.01')))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f'Valor monetário inválido: {value}') from exc


def _date(value: str) -> str:
    date.fromisoformat(value)
    return value


def _insert(conn: sqlite3.Connection, table: str, rows: list[dict], columns: list[str]) -> None:
    if not rows:
        raise ValueError(f'Arquivo vazio para tabela {table}')
    if set(columns) - rows[0].keys():
        raise ValueError(f'Colunas ausentes em {table}: {set(columns) - rows[0].keys()}')
    # table e columns vêm exclusivamente de constantes de código, nunca do usuário.
    placeholders = ','.join('?' for _ in columns)
    sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
    conn.executemany(sql, ([row.get(c, '') for c in columns] for row in rows))


def bootstrap(knowledge_dir: Path, database_path: Path) -> dict[str, int]:
    """Reconstrói a base transacionalmente em arquivo temporário, sem estado parcial."""
    knowledge_dir = Path(knowledge_dir)
    database_path = Path(database_path)
    required = [
        knowledge_dir/'financeiro'/'lancamentos_financeiros.csv',
        knowledge_dir/'financeiro'/'orcamento_mensal.csv',
        knowledge_dir/'ouvidoria'/'manifestacoes.csv',
        knowledge_dir/'ouvidoria'/'referencia_ouvidoria.json',
        knowledge_dir/'informacoes_internas'/'faq_interno.json',
    ]
    missing = [str(x) for x in required if not x.is_file()]
    if missing:
        raise FileNotFoundError('Bases de conhecimento ausentes: ' + ', '.join(missing))
    database_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = database_path.with_name(database_path.name + '.building')
    temporary.unlink(missing_ok=True)
    try:
        # O context manager da conexão só gerencia commit/rollback; closing garante
        # sqlite3.Connection.close() ANTES do os.replace (essencial no Windows).
        with closing(sqlite3.connect(temporary)) as conn, conn:
            conn.executescript(SCHEMA)
            fin = _read_csv(required[0])
            budget = _read_csv(required[1])
            complaints = _read_csv(required[2])
            for row in fin:
                row['data_competencia'] = _date(row['data_competencia'])
                row['data_vencimento'] = _date(row['data_vencimento'])
                row['valor_brl'] = _money(row['valor_brl'])
                if row['tipo'] not in {'Receita', 'Despesa'} or row['status'] not in {'Pago','Pendente','Atrasado'}:
                    raise ValueError('Enum financeiro inválido')
            for row in budget:
                row['ano'] = int(row['ano'])
                if not re.fullmatch(r'(0[1-9]|1[0-2])', row['mes']):
                    raise ValueError('Mês orçamentário inválido')
                row['orcamento_brl'] = _money(row['orcamento_brl'])
            valid_status = set(json.loads(required[3].read_text(encoding='utf-8'))['status_validos'])
            for row in complaints:
                row['data_abertura'] = _date(row['data_abertura'])
                if row['data_resposta']:
                    row['data_resposta'] = _date(row['data_resposta'])
                if row['status'] not in valid_status:
                    raise ValueError(f"Status ouvidoria inválido: {row['status']}")
                row['prazo_referencia_dias'] = int(row['prazo_referencia_dias'])
            _insert(conn, 'lancamentos_financeiros', fin, [
                'id_lancamento','data_competencia','data_vencimento','tipo','categoria',
                'descricao','centro_custo','departamento','contraparte','valor_brl',
                'status','metodo_pagamento','observacao'])
            _insert(conn, 'orcamento_mensal', budget, [
                'ano','mes','centro_custo','departamento','orcamento_brl','versao_orcamento','observacao'])
            _insert(conn, 'manifestacoes_ouvidoria', complaints, [
                'protocolo','data_abertura','categoria','assunto','canal_entrada','prioridade',
                'status','area_responsavel','resumo_manifestacao','data_resposta',
                'resposta_resumo','prazo_referencia_dias','dados_pessoais','observacao'])
            files = sorted((knowledge_dir/'informacoes_internas').glob('*.md'))
            if not files:
                raise FileNotFoundError('Não há documentos .md para informações internas')
            n_chunks = 0
            for path in files:
                content = path.read_text(encoding='utf-8-sig')
                title = next((line.strip('# ').strip() for line in content.splitlines() if line.startswith('# ')), path.stem)
                version = re.search(r'Versão\s+([\d.]+)', content)
                # Documentos são curtos; 1 chunk/documento preserva contexto e versão.
                conn.execute('INSERT INTO kb_chunks(source,section,content,domain,document_version) VALUES(?,?,?,?,?)',
                             (path.name,title,content,'informacoes_internas',version.group(1) if version else None))
                n_chunks += 1
            faqs = json.loads(required[4].read_text(encoding='utf-8'))
            for faq in faqs:
                conn.execute('INSERT INTO kb_chunks(source,section,content,domain,document_version) VALUES(?,?,?,?,?)',
                             (faq['documento'],faq['id'],f"{faq['pergunta']}\n{faq['resposta']}",
                              'informacoes_internas',None))
                n_chunks += 1
            conn.commit()
        temporary.replace(database_path)
    except Exception:
        # Não mascarar a falha original caso outro processo retenha o arquivo.
        try:
            temporary.unlink(missing_ok=True)
        except PermissionError:
            pass
        raise
    return {'lancamentos': len(fin),'orcamentos': len(budget),
            'manifestacoes':len(complaints),'documentos':len(files),'chunks':n_chunks}
