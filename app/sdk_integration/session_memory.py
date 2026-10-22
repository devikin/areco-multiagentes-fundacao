"""Registro volátil por sessão: SDK gerencia o conteúdo da conversa.

TTL/limite de sessões e lock são responsabilidades técnicas do servidor;
este arquivo não escreve respostas nem concatena parâmetros.
"""
from __future__ import annotations

import asyncio
from collections import OrderedDict
from dataclasses import dataclass, field
from threading import Lock
from time import monotonic
from typing import Any


@dataclass
class SessionState:
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    updated: float = field(default_factory=monotonic)
    sdk_session: Any | None = None
    pending_agent: Any | None = None  # Especialista que pediu esclarecimento.
    pending_question: str | None = None  # Texto original, apenas para validar plano da ferramenta.


class SessionMemory:
    def __init__(self, *, ttl_seconds: int = 1800, max_sessions: int = 200,
                 max_exchanges: int = 30):
        self.ttl_seconds = ttl_seconds
        self.max_sessions = max_sessions
        self.max_exchanges = max_exchanges
        self._sessions: OrderedDict[str, SessionState] = OrderedDict()
        self._guard = Lock()

    def get(self, session_id: str) -> SessionState:
        now = monotonic()
        with self._guard:
            for key, state in list(self._sessions.items()):
                if now - state.updated > self.ttl_seconds:
                    del self._sessions[key]
            state = self._sessions.get(session_id)
            if state is None:
                if len(self._sessions) >= self.max_sessions:
                    self._sessions.popitem(last=False)
                state = SessionState()
                self._sessions[session_id] = state
            state.updated = now
            self._sessions.move_to_end(session_id)
            return state


def last_30_exchanges(history: list[dict], new_input: list[dict]) -> list[dict]:
    """Limita a 30 entradas do usuário; preserva os itens dos handoffs e tools."""
    positions = [idx for idx, item in enumerate(history)
                 if item.get('role') == 'user']
    if len(positions) > 30:
        history = history[positions[-30]:]
    return history + new_input
