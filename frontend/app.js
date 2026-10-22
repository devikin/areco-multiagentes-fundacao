// Areco v0.2.35 — reconexão segura antes de enviar ao chat.
// Uma sessão e no máximo uma mensagem pendente por aba; não persistir dados em storage.
const messages = document.getElementById('messages');
const form = document.getElementById('chatForm');
const input = document.getElementById('question');
const send = document.getElementById('send');
const examples = [...document.querySelectorAll('[data-q]')];
const reconnectOverlay = document.getElementById('reconnectOverlay');
const reconnectCancel = document.getElementById('reconnectCancel');
const sessionId = crypto.randomUUID();
const REQUEST_TIMEOUT_MS = 120000;
const HEALTH_TIMEOUT_MS = 3500;
const RECONNECT_INTERVAL_MS = 3000;

function renderMessage(text, role, meta = '') {
  const article = document.createElement('article');
  article.className = 'message ' + role;
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = text; // Nunca renderizar HTML recebido da LLM.
  article.appendChild(bubble);
  if (meta) {
    const label = document.createElement('div');
    label.className = 'meta';
    label.textContent = meta;
    article.appendChild(label);
  }
  messages.appendChild(article);
  messages.scrollTop = messages.scrollHeight;
  return article;
}

function setBusy(busy) {
  send.disabled = busy;
  input.disabled = busy;
  examples.forEach(button => { button.disabled = busy; });
  form.setAttribute('aria-busy', String(busy));
}

// GET /health não aciona o Agents SDK e não consome tokens OpenAI.
async function serverAvailable() {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), HEALTH_TIMEOUT_MS);
  try {
    const response = await fetch('/health', {
      method: 'GET', cache: 'no-store', signal: controller.signal
    });
    if (!response.ok) return false;
    const status = await response.json();
    return status.status === 'ok' && status.engine === 'sdk';
  } catch (_) {
    return false;
  } finally {
    clearTimeout(timeoutId);
  }
}

function waitForServer() {
  reconnectOverlay.hidden = false;
  reconnectCancel.focus();
  return new Promise((resolve, reject) => {
    let active = true;
    let retryTimer;
    function cleanup() {
      active = false;
      clearTimeout(retryTimer);
      reconnectCancel.removeEventListener('click', cancel);
      reconnectOverlay.hidden = true;
    }
    function cancel() {
      if (!active) return;
      cleanup();
      reject(new Error('RECONNECT_CANCELLED'));
    }
    async function probe() {
      if (!active) return;
      const healthy = await serverAvailable();
      if (!active) return; // Um check iniciado não deve enviar após Cancelar.
      if (healthy) {
        cleanup();
        resolve();
      } else {
        retryTimer = setTimeout(probe, RECONNECT_INTERVAL_MS);
      }
    }
    reconnectCancel.addEventListener('click', cancel);
    retryTimer = setTimeout(probe, RECONNECT_INTERVAL_MS);
  });
}

async function sendToChat(text) {
  // Chamada POST ocorre uma única vez. Se falhar após iniciar, não há retry.
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch('/api/v1/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: text, session_id: sessionId}),
      signal: controller.signal
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (typeof data.answer !== 'string' || !data.answer.trim()) {
      throw new Error('Resposta inválida do servidor');
    }
    return data;
  } finally {
    clearTimeout(timeoutId);
  }
}

async function ask(question) {
  if (send.disabled) return;
  const text = question.trim();
  if (text.length < 2 || text.length > 1500) return;

  // Preserva o rascunho até que uma resposta válida seja confirmada.
  input.value = text;
  const outgoing = renderMessage(text, 'user');
  setBusy(true);
  let postStarted = false;
  let pending = null;
  try {
    // No cenário offline comprovado, o POST ainda não foi iniciado.
    if (!(await serverAvailable())) await waitForServer();

    // Se o container cair ENTRE /health e o POST, NÃO reenviar automaticamente:
    // já não é possível garantir que o servidor não processou a requisição.
    postStarted = true;
    pending = renderMessage('...', 'bot');
    const data = await sendToChat(text);
    const sources = Array.isArray(data.sources)
      ? data.sources.map(item => item.source).filter(Boolean).join(', ') : '';
    renderMessage(data.answer, 'bot',
      `Motor: ${data.engine || 'sdk'} · Agente: ${data.agent || 'orquestrador'} · Fonte: ${sources || 'não aplicável'} · Classificação: ${data.classification_method || 'não aplicável'} · Resposta: ${data.generation_method || 'não aplicável'} · ${data.latency_ms ?? '?'} ms`);
    input.value = '';
  } catch (error) {
    if (error && error.message === 'RECONNECT_CANCELLED' && !postStarted) {
      // A requisição não foi enviada; remover bolha duplicável, manter o texto.
      outgoing.remove();
    } else {
      outgoing.classList.add('unconfirmed');
      renderMessage('Não foi possível confirmar a resposta do servidor. Sua pergunta permanece no campo. A solicitação pode ter sido processada; um novo envio manual pode consumir tokens novamente.', 'bot');
    }
  } finally {
    if (pending) pending.remove();
    setBusy(false);
    input.focus();
  }
}

form.addEventListener('submit', event => {
  event.preventDefault();
  const question = input.value.trim();
  if (question.length >= 2) ask(question);
});
examples.forEach(button => button.addEventListener('click', () => ask(button.dataset.q || '')));
