# Registro de validação e publicação — Areco v0.2.35

**Data:** 22/10/2026

**Escopo:** evidência de testes, GitHub e preparação da entrega; sem alterações funcionais.

## Evidência de execução confirmada pelo candidato

- PowerShell no Windows 10/11, pasta `areco-multiagentes-fundacao`.
- `python -m pytest -q` executado com o ambiente virtual do projeto: **137 passed in 6.74s**.
- Os problemas de coleta anteriores eram testes legados e mocks não isolados; foram corrigidos na suíte de testes, sem reintroduzir funções removidas no serviço.
- Reconexão da v0.2.35 aprovada manualmente pelo candidato após parar/reiniciar o container, com captura em `docs/assets/reconexao_backend_offline_v0.2.35.png`. Procedimento em `docs/EVIDENCIA_RECONECTAR_BACKEND_v0.2.35.md`.
- Handoffs e consultas reais à OpenAI foram testados em baterias anteriores. Relatórios específicos de avaliação permanecem em `docs/evidence/`.

## Verificação independente do repositório remoto

- Repositório: `https://github.com/devikin/areco-multiagentes-fundacao`.
- Visibilidade retornada pelo GitHub: **private**.
- Branch padrão: `main`.
- Commit inicial publicado e observado: `88e42fa234a9e5b9997b368f05bee1ac6c1a0204` (antes desta atualização documental).
- Confirmada leitura remota do `README.md`, `app/main.py`, `app/sdk_integration/workflow.py`, `frontend/index.html`, `pytest.ini`, `Dockerfile`, `compose.yaml`, `requirements.txt`, `docs/DELIVERY_CHECKLIST.md` e relatório oficial JSON.
- `.env` ausente no repositório consultado; `.env.example` possui `OPENAI_API_KEY=` sem valor. `.gitignore` exclui `.env`.
- Docker Compose publica apenas `127.0.0.1:8000` e utiliza volume local para o SQLite.

## Limitações e pendências não ocultadas

- Não foi feita nova execução do pytest ou do Docker em máquina limpa pelo assistente; a suíte de 137 testes foi executada pelo candidato em seu Windows.
- O print da interface prova o estado visual de reconexão, mas não a contagem exata dos POSTs. O comportamento de POST único é previsto na implementação e coberto por simulações; observação de logs reais ainda pode ser realizada.
- O protótipo não oferece autenticação, permissões por usuário, estado persistente de conversa ou idempotência de ponta a ponta; deve permanecer local.
- `requirements.txt` usa faixas de versão, não um lockfile reproduzível. Um build Docker novo após instalação das dependências exige verificação no ambiente do avaliador.
- A publicação em repositório **privado** não concede acesso à Areco automaticamente: enviar convite de colaboração aos avaliadores autorizados ou entregar ZIP em canal aprovado.
- Confirmar que o compartilhamento das bases sintéticas fornecidas no desafio é permitido. Não tornar o repositório público sem essa confirmação.

## Demonstração sugerida

1. Criar `.env` a partir de `.env.example` somente se o arquivo não existir, e adicionar chave válida localmente.
2. Executar `docker compose up --build -d` e `docker compose ps`; aguardar `healthy`.
3. Abrir `http://127.0.0.1:8000/` e consultar casos dos três domínios com fontes e trace.
4. Demonstrar reconexão com `docker compose stop app` / `docker compose start app`, mantendo aba aberta.
5. Apresentar resultados e limites com `docs/EVALUATION_RESULTS_v0.2.13.md`, `docs/EVIDENCIA_RECONECTAR_BACKEND_v0.2.35.md` e este registro.

**Importante:** testes com chat real usam créditos da API OpenAI; `pytest` e as verificações estáticas não devem consumi-los.
