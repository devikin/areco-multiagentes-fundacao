"""Recuperação de seguimento restrita a fatos verificáveis na Ouvidoria.

Se o modelo não chamar uma ferramenta, NÃO exibimos sua resposta livre.
Revalidamos o último protocolo realmente consultado nesta sessão apenas
quando a pergunta trata de confirmação de pagamento/reembolso.
"""
from __future__ import annotations

import re
import unicodedata

from app.sdk_integration.tools import ExecutionContext, buscar_protocolo


def _plain(text: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', text.casefold())
                   if not unicodedata.combining(c))


def confirmar_limite_reembolso_ouvidoria(
    context: ExecutionContext, question: str, verified_protocol: str | None
) -> str | None:
    """Não deduz pagamento a partir do status de uma manifestação.

    Retorna None se não existe um protocolo validado, uma pergunta de
    pagamento/reembolso ou quando a ferramenta não consegue fundamentar.
    """
    if not verified_protocol or not re.fullmatch(r'OUV-\d{4}', verified_protocol):
        return None
    q = _plain(question)
    if not re.search(r'\b(reembols\w*|pag\w*|pagamento|deposit\w*|receb\w*|liquid\w*|quit\w*|caiu)\b', q):
        return None
    # Não reutilize o protocolo anterior se a pessoa apontou outro código.
    mentioned = re.findall(r'OUV-\d{4}', question.upper())
    if mentioned and any(p != verified_protocol for p in mentioned):
        return None
    result = buscar_protocolo(context, verified_protocol)
    status_match = re.search(r'(?:^|; )status=([^;\n]+)', result)
    if not status_match or 'não encontrado' in result.lower():
        return None
    status = status_match.group(1).strip()
    return (f'O protocolo {verified_protocol} consta como {status} na Ouvidoria. '
            'Esse status informa o andamento da manifestação, mas não comprova que o reembolso foi pago. '
            'Não é possível confirmar a liquidação financeira apenas com esse registro. '
            'Para verificar a liquidação do reembolso, consulte o setor Financeiro ou o sistema de pagamentos.')
