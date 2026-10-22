"""Recuperação documental local auditável (BM25, aliases restritos e fontes únicas).

Os documentos da avaliação são curtos; indexar um documento inteiro preserva regras
que se perderiam se o LLM respondesse apenas com uma linha isolada da FAQ.
Não há serviço de embeddings ou dependências adicionais.
"""
from __future__ import annotations

from collections import Counter
from math import log
import re
import sqlite3
import unicodedata

STOPWORDS = set((
    'a o os as de da do das dos e em um uma no na por para como qual quais '
    'que eu meu minha me com sem pode preciso fazer onde quem quando sobre tem '
    'gostaria queria quero queriamos saber conhecer entender '
    'explicar explica explique explicacao fale falar conte contar diga '
    'funciona funcionam funcionamento poderia poderiam informacao informacoes '
    'detalhes detalhe melhor pouco favor gentileza empresa oi ola bom boa tarde noite '

    'voce sao ser existe existem foi foram ao aos mais dias dia qual quantos quantas se houver'
).split())

# Mapeamento explícito para variações relevantes às dez políticas. Não equivale a
# busca semântica geral; consultas não cobertas devem continuar sem evidência.
ALIASES = {
    'trabalhar': 'trabalho', 'trabalhando': 'trabalho', 'casa': 'remoto',
    'teletrabalho': 'remoto', 'home': 'remoto', 'office': 'remoto',
    'hibrida': 'hibrido', 'hibridas': 'hibrido',
    'reporto': 'report', 'reportar': 'report', 'reporte': 'report',
    'reportados': 'report', 'reportado': 'report',
    'solicito': 'solicit', 'solicitar': 'solicit', 'solicitacao': 'solicit',
    'solicitacoes': 'solicit', 'solicitada': 'solicit',
    'atualizar': 'atualiz', 'atualizo': 'atualiz', 'atualizacao': 'atualiz',
    'pedir': 'solicit', 'pido': 'solicit',
    'ressarcimento': 'reembolso', 'ressarcido': 'reembolso',
    'contracheque': 'holerite',
    'aprovacoes': 'aprovacao', 'aprovados': 'aprovacao',
    'aprovadas': 'aprovacao', 'aprovar': 'aprovacao',
    'phishing': 'phishing',
}


def normalize(text: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', text.lower())
                   if not unicodedata.combining(c))


def tokens(text: str) -> list[str]:
    parts = re.findall(r'[a-z0-9]+', normalize(text))
    cleaned = []
    for word in parts:
        if len(word) < 2 or word in STOPWORDS or any(ch.isdigit() for ch in word):
            continue
        word = ALIASES.get(word, word)
        if word.endswith('s') and len(word) > 5 and word not in {'ferias'}:
            word = word[:-1]
        cleaned.append(word)
    return cleaned


def retrieve(conn: sqlite3.Connection, question: str, top_k: int = 3) -> list[dict]:
    """Retorna no máximo top_k *fontes distintas* com texto completo + versão.

    FAQ auxilia no ranking; quando seu registro ganha, a evidência devolvida é
    sempre o documento principal que contém a política e seus limites.
    """
    query = set(tokens(question))
    if not query or top_k < 1:
        return []
    rows = conn.execute(
        'SELECT source,section,content,document_version FROM kb_chunks WHERE domain=?',
        ('informacoes_internas',)
    ).fetchall()
    if not rows:
        return []
    docs = [tokens(r['section'] + ' ' + r['content']) for r in rows]
    avg_len = sum(len(d) for d in docs) / len(docs)
    df = Counter(word for doc in docs for word in set(doc))
    total = len(docs)

    primary = {r['source']: r for r in rows if r['document_version'] is not None}
    candidates: dict[str, dict] = {}
    for row, terms in zip(rows, docs):
        frequency = Counter(terms)
        overlap = query.intersection(frequency)
        if not overlap:
            continue
        coverage = len(overlap) / len(query)
        # Impede trechos coincidentes apenas por palavras genéricas, como 'prazo'.
        # Uma pergunta misturada a instruções adversariais pode ter termos
        # irrelevantes. Dois termos distintos do título autorizam avaliar a
        # relevância por BM25, sem liberar fontes por coincidência genérica.
        title_terms = set(tokens(row['section']))
        anchored = len(query.intersection(title_terms)) >= 2
        if coverage < .5 and not anchored:
            continue
        score = 0.0
        for term in overlap:
            idf = log(1 + (total - df[term] + .5) / (df[term] + .5))
            score += idf * (frequency[term] * 2.2) / (
                frequency[term] + 1.2 * (.25 + .75 * len(terms) / max(1, avg_len))
            )
        # Um tópico mencionado no título é evidência mais forte do assunto do documento.
        score += 1.5 * len(query.intersection(title_terms))
        if normalize(question).strip(' ?!') in normalize(row['content']):
            score += 3.0
        source = row['source']
        document = primary.get(source, row)
        item = {
            'source': source,
            'section': document['section'],
            'content': document['content'],
            'document_version': document['document_version'],
            'score': round(score, 3),
            'coverage': round(coverage, 3),
        }
        existing = candidates.get(source)
        if existing is None or item['score'] > existing['score']:
            candidates[source] = item
    results = sorted(candidates.values(), key=lambda item: (-item['score'], item['source']))
    if not results:
        return []
    # Corte relativo evita incluir fontes que compartilham só palavras genéricas.
    best = results[0]['score']
    return [item for item in results if item['score'] >= max(.8, best * .70)][:top_k]
