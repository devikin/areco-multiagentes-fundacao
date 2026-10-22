"""Valida entradas objetivamente inválidas antes do Agents SDK, sem adivinhar dados.

O mecanismo NÃO classifica consultas empresariais nem substitui os handoffs.
Ele atua apenas sobre um campo solicitado no turno anterior ou um erro
sintático inequívoco; entradas válidas seguem integralmente para o Runner.
"""
from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
from difflib import get_close_matches
from pathlib import Path
import re
import sqlite3
import unicodedata


@dataclass(frozen=True)
class GuardDecision:
    # answer: pergunta local de esclarecimento, sem chamada ao modelo.
    answer: str | None = None
    # replacement: resposta previamente confirmada, enviada ao Runner.
    replacement: str | None = None


def _norm(text: str) -> str:
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD', text.casefold())
                            if not unicodedata.combining(c)).split())


def _last_question(state) -> str:
    if state is None:
        return ''
    return next((item['content'] for item in reversed(state.history)
                 if item['role'] == 'assistant'), '')


def _expected_field(state) -> str | None:
    previous = _norm(_last_question(state))
    if not previous or '?' not in previous:
        return None
    if re.search(r'\b(?:qual|que|informe|de qual|em qual)\b.{0,42}\bano\b|\bano\b.{0,40}\b(?:gostaria|quer|deseja|informe)\b', previous):
        return 'ano'
    if re.search(r'\b(?:numero|codigo)\s+(?:do\s+)?protocolo\b|\bprotocolo\b.{0,25}\b(?:numero|codigo)\b', previous):
        return 'protocolo'
    if re.search(r'\b(?:qual|quais|informe|de qual)\b.{0,35}\bdepartamento\b|\bdepartamento\b.{0,30}\b(?:deseja|quer|informe)\b', previous):
        return 'departamento'
    if re.search(r'\b(?:qual|quais|informe|de qual)\b.{0,30}\bmes\b', previous):
        return 'mes'
    return None


MONTHS = {'janeiro': 1, 'fevereiro': 2, 'marco': 3, 'abril': 4,
          'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
          'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12}


def _known_departments(database: Path) -> list[str]:
    # Exatamente duas tabelas e uma coluna permitidas; sem SQL produzido pela LLM.
    with closing(sqlite3.connect(database)) as conn:
        return sorted({row[0] for table in ('lancamentos_financeiros', 'orcamento_mensal')
                       for row in conn.execute(f'SELECT DISTINCT departamento FROM {table}')
                       if row[0]})


def evaluate(message: str, state, database: Path) -> GuardDecision | None:
    """Não usa ou modifica contexto fora da sessão; confirmação é sempre explícita."""
    if state is None:
        return None
    original = message.strip()
    q = _norm(original)

    # Confirmação pendente de correção de departamento. Nunca normalizar sem "sim".
    proposed = state.pending_confirmation
    if proposed:
        if q in {'sim', 'isso', 'correto', 'exatamente', 'sim correto', 'isso mesmo'}:
            state.pending_confirmation = None
            return GuardDecision(replacement=proposed)
        state.pending_confirmation = None
        if q in {'nao', 'nao e', 'errado', 'outro', 'outra'}:
            return GuardDecision(answer='Tudo bem. Qual é o nome correto do departamento?')
        # O usuário forneceu um texto novo; avaliá-lo normalmente.

    expected = _expected_field(state)
    explicit_year = bool(re.search(r'\bano\s*[:=]?\s*\d+\b', q))
    if expected == 'ano' or explicit_year:
        value = re.fullmatch(r'(?:ano\s*[:=]?\s*)?(\d+)\s*', q)
        if value:
            digits = value.group(1)
            if len(digits) != 4:
                return GuardDecision(answer=(f'O ano "{digits}" parece incompleto ou inválido. '
                                             'Pode informar o ano com quatro dígitos? Por exemplo, 2025.'))
            if not 2000 <= int(digits) <= 2099:
                return GuardDecision(answer='Para esta consulta, informe um ano de quatro dígitos entre 2000 e 2099.')

    code = re.search(r'\bOUV[-\s]?(\d{1,3})\b', original, re.I)
    if code and (expected == 'protocolo' or re.fullmatch(r'OUV[-\s]?\d{1,3}', original, re.I)
                 or re.search(r'\bprotocolo\b', original, re.I)):
        return GuardDecision(answer=(f'O código OUV-{code.group(1)} parece incompleto. '
                                     'Pode informar o protocolo no formato OUV-NNNN (quatro dígitos)? '
                                     'Prefiro confirmar o número a consultar outro registro.'))

    invalid_month = re.search(r'\bmes\s*(?:numero\s*)?(\d{1,2})\b', q)
    if invalid_month and not 1 <= int(invalid_month.group(1)) <= 12:
        return GuardDecision(answer=f'O mês {invalid_month.group(1)} não é válido. Pode informar um mês entre 1 e 12?')
    if expected == 'mes' and re.fullmatch(r'\d{1,2}', q) and not 1 <= int(q) <= 12:
        return GuardDecision(answer=f'O mês {q} não é válido. Pode informar um mês entre 1 e 12?')

    names = '|'.join(MONTHS)
    period = re.search(rf'\b(?:de\s+)?({names})\s+(?:a|ate)\s+({names})\b', q)
    if period and MONTHS[period.group(1)] > MONTHS[period.group(2)]:
        return GuardDecision(answer=(f'O período de {period.group(1)} a {period.group(2)} '
                                     'está invertido para uma consulta no mesmo ano. '
                                     'Pode confirmar o mês inicial e o final?'))

    if expected == 'departamento':
        # Só sugerir departamentos reais, nunca fazer substituição silenciosa.
        candidate = re.sub(r'^(?:do|da|de|o|a|departamento)\s+', '', q).strip()
        if 3 <= len(candidate) <= 35 and re.fullmatch(r'[a-z ]+', candidate):
            candidates = _known_departments(database)
            matched = { _norm(name): name for name in candidates }
            if candidate not in matched:
                close = get_close_matches(candidate, list(matched), n=1, cutoff=.77)
                if close:
                    canonical = matched[close[0]]
                    state.pending_confirmation = canonical
                    return GuardDecision(answer=f'Você quis dizer o departamento {canonical}?')

    if q == '10 mil' and expected is None and state.pending_questions:
        last = _norm(_last_question(state))
        if 'valor' not in last and 'quantia' not in last:
            return GuardDecision(answer='Você se refere a R$ 10 mil ou a 10 mil registros?')
    return None
