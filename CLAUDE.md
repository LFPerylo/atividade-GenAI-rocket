# CLAUDE.md

Guia para agentes de código trabalhando neste repositório. Visão de produto em `PRODUCT.md`, sistema visual em `DESIGN.md`, passo a passo de uso no `README.md`.

## O projeto

CineRocket Analytics: agente Text-to-SQL (PydanticAI) que responde perguntas em português sobre a camada Gold da CineData (`data/cinerocket.db`, SQLite, 10 tabelas). Entregas: API FastAPI, UI Streamlit e CLI `cinerocket`. Atividade GenAI do Rocket Lab 26.2.

## Comandos

```bash
make install        # uv sync + correção da flag hidden do .venv no macOS
make check          # ruff check, ruff format --check, mypy strict, pytest
make api            # API em http://localhost:8000 (reload observa só src/cinerocket)
make ui             # Streamlit em http://localhost:8501 (precisa da API)
make index          # índice semântico das sinopses (10 a 25 min, sem LLM)
uv run cinerocket ask '<pergunta>'
uv run cinerocket eval run --case <id> --delay 3
uv run cinerocket cache clear
```

## Arquitetura

Dependências sempre de fora para dentro: `api`/`cli`/`ui` → `application` → `agent` → `database`/`guardrails`/`llm`/`semantic`/`storage` → `domain`. O composition root é `src/cinerocket/container.py`; novas dependências entram por ali, nunca por import global.

- `agent/prompts.py`: instruções e glossário de negócio. Regras que o schema não revela ficam aqui.
- `agent/examples.yaml`: exemplos few-shot (pergunta, premissas, SQL), recuperados por similaridade em `agent/examples.py` e injetados nas instruções.
- `agent/validation.py`: validação da saída. O SQL final precisa ter passado por `run_sql`; resposta vazia, ausência de SQL e `out_of_scope` depois de consultar o banco viram `ModelRetry`.
- `application/service.py`: guarda → cache → agente → reexecução do SQL final → sessão. Os números exibidos vêm sempre do banco, nunca do texto do modelo.
- `llm/factory.py` + `llm/deadline.py`: cadeia `FallbackModel` de modelos gratuitos (OpenRouter `:free`, Gemini por último), com prazo total por chamada.
- `evaluation/dataset.yaml`: as 14 perguntas do enunciado com SQL de referência.

## Convenções

- **Sem comentários no código.** Docstrings só onde são contrato funcional: funções de tool do agente (o PydanticAI as envia ao modelo) e comandos Typer (viram o `--help`).
- Python 3.12, Ruff com linha de 110, mypy `strict`. Rode `make check` antes de commitar.
- Textos para o usuário, mensagens de erro, prompts e commits em **português**; identificadores em inglês.
- Commits no formato `tipo: descrição` (`feat`, `fix`, `docs`, `ci`, `chore`, `test`, `refactor`), em português e **sem linha `Co-Authored-By`**.
- Erros de domínio herdam de `CineRocketError` (`domain/errors.py`) e são mapeados para HTTP em `api/errors.py`.
- Componentes externos ficam atrás de `Protocol` (`application/ports.py`, `semantic/store.py`, `semantic/embedder.py`).
- Banco de análise somente leitura: nunca escreva em `data/cinerocket.db` nem afrouxe `guardrails/sql.py`. Estado da aplicação vai em `data/app.db`.
- Não trate nem altere os dados da camada Gold; ruídos conhecidos são contornados com regras no glossário (ex.: a pessoa "English").

## Testes

- Testes nunca chamam LLM nem dependem do banco real: usam `FunctionModel` do PydanticAI e o SQLite de fixture em `tests/conftest.py`. O few-shot fica desligado nos testes (`few_shot_limit=0`) para não baixar o modelo de embeddings.
- Escreva só testes que protejam comportamento real: guardrails, validação da saída, fluxo do serviço, API, comparação da avaliação.
- **Nunca** use perguntas de `evaluation/dataset.yaml` como exemplos few-shot; `tests/test_examples.py` falha se houver vazamento.
- Novo exemplo few-shot: valide o SQL no banco real antes de commitar.

## Cota e custo

- OpenRouter gratuito: 50 requisições por dia (zera às 21h de Brasília); cada pergunta usa de 2 a 5. Confira com `cinerocket quota` antes de rodar avaliações e use `--case` e `--delay`.
- O hash do cache inclui schema, cadeia de modelos, `PROMPT_VERSION` e a versão dos exemplos: mudar o prompt ou `examples.yaml` invalida o cache sozinho.
- O catálogo `:free` muda com frequência. Para trocar a ordem dos modelos, meça latência e tool calling primeiro; modelos que entregam o corpo devagar são cortados pelo `DeadlineModel` (`LLM_TIMEOUT_SECONDS`).

## Armadilhas conhecidas

- macOS: a flag `hidden` no `.venv` faz o Python ignorar o `.pth` do pacote (`No module named 'cinerocket'`). Corrija com `chflags -R nohidden .venv`.
- Streamlit não recarrega módulos já importados: depois de mudar `ui/components.py` ou `ui/charts.py`, reinicie `make ui`.
- `uvicorn --reload` observando a raiz do projeto reinicia a API a cada gravação em `data/app.db`; mantenha `reload_dirs` restrito ao pacote.
- Use aspas simples no shell para perguntas com `R$`.
- `lucro_brl` vale 0 sem receita e é igual à receita sem orçamento; margens de grupos são agregadas (`SUM(lucro)/SUM(receita)`).
- Arquivos que não vão para o Git: `data/` (banco de ~550 MB, índice, modelos, sessões), `.env`, `docs/` (contém chave), `.claude/` e `.impeccable/`.
