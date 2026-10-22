// Testes dinâmicos em Node.js (sem dependências externas). Não usa chave OpenAI.
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const SRC = readFileSync(path.join(__dirname, '../frontend/app.js'), 'utf8');

function fixture(healthSequence, chatResponder) {
  const nodes = new Map();
  const timers = new Map();
  let nextTimer = 1;
  let healthCalls = 0;
  const posts = [];
  class Node {
    constructor(name) {
      this.name = name;
      this.children = [];
      this.value = '';
      this.disabled = false;
      this.hidden = name === 'reconnectOverlay';
      this.handlers = new Map();
      this.classes = new Set();
      this.classList = {add: c => this.classes.add(c)};
    }
    appendChild(n) { this.children.push(n); }
    remove() { this.removed = true; }
    focus() { this.focused = true; }
    setAttribute(name, val) { this[name] = val; }
    addEventListener(name, fn) { this.handlers.set(name, fn); }
    removeEventListener(name, fn) { if (this.handlers.get(name) === fn) this.handlers.delete(name); }
  }
  for (const name of ['messages', 'chatForm', 'question', 'send', 'reconnectOverlay', 'reconnectCancel']) {
    nodes.set(name, new Node(name));
  }
  const examples = [new Node('example1'), new Node('example2')];
  const ctx = {
    console,
    crypto: {randomUUID: () => 'session-123'},
    AbortController,
    setTimeout: (fn, delay) => {const id = nextTimer++; timers.set(id, {fn, delay}); return id;},
    clearTimeout: id => {timers.delete(id);},
    document: {
      getElementById: name => nodes.get(name),
      querySelectorAll: () => examples,
      createElement: name => new Node(name)
    },
    fetch: async (url, opts) => {
      if (url === '/health') {
        const step = healthSequence[Math.min(healthCalls++, healthSequence.length - 1)];
        if (step === 'error') throw new Error('offline');
        return {ok: !!step, json: async () => ({status: step ? 'ok' : 'down', engine: 'sdk'})};
      }
      if (url === '/api/v1/chat') {
        posts.push({url, opts});
        return chatResponder ? chatResponder() : {ok: true, json: async () => ({answer: 'Conectado.', sources: [], engine: 'sdk'})};
      }
      throw new Error('Unexpected URL ' + url);
    }
  };
  vm.createContext(ctx);
  vm.runInContext(SRC + '\n globalThis.__ask=ask;', ctx);
  async function flush() { for(let i = 0; i < 35; i++) await Promise.resolve(); }
  async function runTimer(delay) {
    const entry = [...timers.entries()].find(([, val]) => val.delay === delay);
    assert.ok(entry, `Timer ${delay} ms not found`);
    timers.delete(entry[0]);
    entry[1].fn();
    await flush();
  }
  return {nodes, timers, posts, examples, ctx, flush, runTimer, get healthCalls(){return healthCalls;}};
}

async function main() {
  // Online: exatamente um POST e overlay invisível.
  {
    const x=fixture([true]);
    x.nodes.get('question').value = 'ola bom dia';
    const run=x.ctx.__ask('ola bom dia'); await x.flush(); await run;
    assert.equal(x.posts.length,1);
    assert.equal(x.nodes.get('reconnectOverlay').hidden,true);
    assert.equal(x.nodes.get('question').value,'');
    assert.equal(x.nodes.get('send').disabled,false);
  }
  // Offline inicialmente: não há POST durante reconexão; envia uma vez quando healthy.
  {
    const x=fixture(['error',false,true]);
    const run=x.ctx.__ask('OUV-0016'); await x.flush();
    assert.equal(x.nodes.get('send').disabled,true);
    assert.equal(x.nodes.get('reconnectOverlay').hidden,false);
    assert.equal(x.posts.length,0);
    assert.equal(x.nodes.get('question').value,'OUV-0016');
    await x.runTimer(3000);
    assert.equal(x.posts.length,0);
    assert.equal(x.nodes.get('reconnectOverlay').hidden,false);
    await x.runTimer(3000); await run;
    assert.equal(x.posts.length,1);
    assert.equal(x.nodes.get('reconnectOverlay').hidden,true);
    assert.equal(x.nodes.get('question').value,'');
  }
  // Cancelar espera offline: zero POST; pergunta continua editável.
  {
    const x=fixture(['error',true]);
    const run=x.ctx.__ask('teste cancelado');await x.flush();
    x.nodes.get('reconnectCancel').handlers.get('click')();
    await run;
    assert.equal(x.posts.length,0);
    assert.equal(x.nodes.get('question').value,'teste cancelado');
    assert.equal(x.nodes.get('send').disabled,false);
    assert.equal(x.nodes.get('reconnectOverlay').hidden,true);
  }
  // Health pronto, POST falha: NÃO repetir automaticamente (requisição ambígua).
  {
    const x=fixture([true], async () => {throw new Error('POST failed');});
    const run=x.ctx.__ask('situacao do protocolo');await x.flush();await run;
    assert.equal(x.posts.length,1);
    assert.equal(x.nodes.get('question').value,'situacao do protocolo');
    assert.equal(x.nodes.get('reconnectOverlay').hidden,true);
    assert.equal(x.nodes.get('send').disabled,false);
  }
  // Health retorna e container cai no POST: comportamento ainda é o de pedido incerto.
  {
    const x=fixture([true], async () => ({ok:false, status:503}));
    const run=x.ctx.__ask('falha apos health');await x.flush();await run;
    assert.equal(x.posts.length,1);
    assert.equal(x.nodes.get('question').value,'falha apos health');
  }
  console.log('PASS | 5 cenários JS: online, offline/reconexão, cancelamento, POST incerto, queda após health.');
}
main().catch(err => { console.error(err); process.exitCode = 1; });
