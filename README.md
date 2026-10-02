# CineRocket Analytics

Agente de IA que responde, em linguagem natural, perguntas sobre o catálogo de filmes da **CineData Analytics**, consultando em tempo real a camada Gold do Data Lakehouse (Text-to-SQL). Feito para quem não sabe SQL: a pergunta vira uma consulta testada pelo próprio agente, executada somente em leitura, e a resposta volta em português com a tabela de dados, o SQL executado, as premissas adotadas e um gráfico.

Atividade GenAI do Rocket Lab 26.2 (Visagio).

## Funcionalidades

- **Text-to-SQL com autocorreção**: o agente explora o schema, confirma valores reais, testa o SQL e corrige a partir do erro do banco antes de responder.
- **Respostas rastreáveis**: os números exibidos vêm da reexecução do SQL final no banco, nunca de texto gerado pelo modelo. O SQL final precisa ter sido testado pelo agente na mesma análise.
- **Agente híbrido**: busca semântica nas 95 mil sinopses (embeddings locais multilíngues) combinada com SQL, para perguntas como "filmes sobre viagem no tempo com melhor nota IMDb".
- **Guardrails**: conexão SQLite read-only, `PRAGMA query_only`, validação por AST (sqlglot) que aceita apenas uma consulta `SELECT`/`WITH`, lista de tabelas permitidas, bloqueio de funções perigosas, limite de linhas, timeout de consulta e recusa de perguntas fora do escopo.
- **Fallback entre modelos**: cadeia de modelos gratuitos do OpenRouter com Gemini como última opção. Erros de provedor (429, 5xx, timeout) passam automaticamente para o próximo modelo, sem retentativas que queimem a cota.
- **Memória de conversa** por sessão, com janela de turnos configurável. Perguntas de acompanhamento ("e no ano anterior?") funcionam.
- **Cache de respostas**: perguntas repetidas (normalizadas) não consomem chamadas ao modelo.
- **Avaliação**: conjunto com as 14 perguntas do enunciado e SQL de referência, comparando os resultados por conteúdo.
- **Três interfaces**: API FastAPI, interface web em Streamlit (chat, gráficos, tabela, SQL e download em CSV) e CLI.

## Arquitetura

```
 Streamlit (ui) ──HTTP──▶ FastAPI (api) ─┐
                                         ├──▶ AnalyticsService ──▶ Agente PydanticAI ──▶ LLM (OpenRouter → Gemini)
 CLI (cinerocket) ───────────────────────┘        │      │              │
                                                  │      │              ├── describe_table / distinct_values
                                       cache + sessões   │              ├── run_sql ──▶ SqlGuard ──▶ SQLite read-only
                                       (SQLite app.db)   │              └── search_synopses ──▶ índice vetorial
                                                         └── reexecuta o SQL final e monta a resposta
```

Camadas em `src/cinerocket`, com dependências sempre de fora para dentro:

| Pacote | Responsabilidade |
| --- | --- |
| `domain` | Modelos (`ChatResponse`, `QueryResult`, `AgentAnswer`, `ChartSpec`) e erros de domínio |
| `database` | Conexão read-only, catálogo do schema, executor de consultas, repositório de filmes |
| `guardrails` | Validação de SQL (AST) e da pergunta |
| `llm` | Fábrica da cadeia de modelos com fallback e consulta de cota do OpenRouter |
| `semantic` | Embeddings (FastEmbed), armazenamento vetorial e indexação das sinopses |
| `agent` | Prompt, dependências, ferramentas, validação da saída e janela de histórico |
| `application` | `AnalyticsService` (guarda → cache → agente → reexecução → sessão), portas e regras auxiliares |
| `storage` | Implementações SQLite de sessões e cache |
| `api`, `cli`, `ui` | Interfaces |
| `evaluation` | Dataset de referência, comparação de resultados e runner |
| `container.py` | Composition root: monta e injeta as dependências |

Componentes externos (LLM, sessão, cache, índice vetorial) ficam atrás de `Protocol`s, então trocar SQLite por Redis/Postgres ou NumPy por um banco vetorial não exige mudar o serviço nem o agente.

## Stack

Python 3.12 · [PydanticAI](https://ai.pydantic.dev) · OpenRouter (modelos `:free`) e Google Gemini · SQLite · sqlglot · FastEmbed (`paraphrase-multilingual-MiniLM-L12-v2`) · NumPy · FastAPI · Streamlit · Plotly · Typer · Rich · uv · Ruff · mypy (strict) · pytest · Docker · GitHub Actions

## Pré-requisitos

- [uv](https://docs.astral.sh/uv/getting-started/installation/), que baixa o Python 3.12 se ele não estiver instalado
- Arquivo do banco `cinerocket.db` (camada Gold, disponível na pasta da atividade)
- Pelo menos uma chave de LLM:
  - OpenRouter, gratuita: crie em <https://openrouter.ai/keys>
  - Gemini, gratuita: crie em <https://aistudio.google.com/apikey>
- Opcional: Docker, para rodar tudo em contêineres

## Passo a passo

### 1. Instalar dependências

```bash
git clone https://github.com/LFPerylo/atividade-GenAI-rocket.git
```

```bash
cd atividade-GenAI-rocket && make install
```

Sem `make`, use `uv sync`.

### 2. Colocar o banco de dados

O banco tem cerca de 550 MB e não é versionado. Copie o arquivo da atividade para `data/cinerocket.db`:

```bash
cp "/caminho/para/cinerocket.db" data/cinerocket.db
```

### 3. Configurar as chaves

```bash
cp .env.example .env
```

Preencha `OPENROUTER_API_KEY` e/ou `GOOGLE_API_KEY` no `.env`. Todas as variáveis estão listadas mais abaixo, em [Configuração](#configuração).

### 4. Gerar o índice semântico (opcional, recomendado)

Habilita a busca por enredo nas sinopses. Na primeira execução baixa o modelo de embeddings (cerca de 220 MB) e processa 95.645 sinopses localmente, sem chamar LLM. Leva de 10 a 25 minutos, dependendo da CPU.

```bash
make index
```

Sem o índice, o agente funciona normalmente e a ferramenta de busca semântica fica oculta.

### 5. Usar

**Interface web**: suba a API e, em outro terminal, a UI. Depois abra <http://localhost:8501>.

```bash
make api
```

```bash
make ui
```

**Terminal**: pergunta única ou chat com memória.

```bash
uv run cinerocket ask 'Quais são os 10 filmes com maior receita em R$?'
```

```bash
uv run cinerocket chat
```

**API**: a documentação interativa fica em <http://localhost:8000/docs>.

```bash
curl -s localhost:8000/api/v1/chat -H 'Content-Type: application/json' -d '{"question": "Quais são os 5 filmes mais populares?"}'
```

### Com Docker

Com o banco em `data/` e o `.env` preenchido:

```bash
docker compose up --build -d api ui
```

Para gerar o índice semântico dentro do contêiner:

```bash
docker compose --profile jobs run --rm indexer
```

A API sobe em <http://localhost:8000> e a UI em <http://localhost:8501>. A pasta `data/` é montada como volume e guarda banco, índice, modelo de embeddings, sessões e cache.

## Comandos

| Comando | O que faz |
| --- | --- |
| `cinerocket ask "<pergunta>" [--session ID] [--json]` | Pergunta única; `--session` mantém o contexto |
| `cinerocket chat` | Conversa interativa com memória |
| `cinerocket serve [--host] [--port] [--reload]` | Sobe a API |
| `cinerocket ui [--host] [--port]` | Sobe a interface Streamlit |
| `cinerocket index build [--parallel N]` | Gera o índice semântico das sinopses |
| `cinerocket eval run [--case ID ...] [--limit N] [--delay S]` | Roda a avaliação; o relatório vai para `data/eval/` |
| `cinerocket quota` | Mostra as requisições gratuitas restantes no OpenRouter |
| `make check` | Lint, formatação, tipos e testes |

## API

| Método | Rota | Descrição |
| --- | --- | --- |
| `POST` | `/api/v1/chat` | `{"question": "...", "session_id": "opcional"}` → resposta, SQL, linhas, gráfico, premissas, modelo e uso |
| `GET` | `/api/v1/sessions/{id}` | Histórico da sessão |
| `DELETE` | `/api/v1/sessions/{id}` | Encerra a sessão |
| `GET` | `/api/v1/schema` | Tabelas, colunas, chaves e contagens da camada Gold |
| `GET` | `/api/v1/quota` | Cota diária do OpenRouter |
| `GET` | `/health` | Estado do banco, do índice semântico e dos modelos configurados |

Os erros seguem `{"error": "<Tipo>", "detail": "<mensagem>"}`, com o status HTTP correspondente: 422 para pergunta inválida, 404 para sessão inexistente, 503 para LLM indisponível ou configuração ausente e 502 para falha do agente.

## Exemplos de perguntas

Todas as categorias do enunciado estão na barra lateral da UI e no conjunto de avaliação:

- **Bilheteria e finanças**: top 10 filmes por receita em R$; lucro médio por gênero; maiores margens de lucro.
- **Popularidade e engajamento**: 5 filmes mais populares; divergência entre notas TMDB e IMDb; nota média IMDb por ano.
- **Elenco e equipe**: ator com mais participações nos últimos 5 anos; diretores com maior nota média (mínimo de 5 filmes); dupla ator-diretor mais frequente.
- **Gêneros e produtoras**: filmes por gênero; produtora com maior lucro; gênero com maior margem média.
- **Avaliações dos usuários**: filmes mais avaliados; maior divergência entre usuários e IMDb.
- **Busca por enredo**: "Quais filmes sobre viagem no tempo têm a melhor nota IMDb?"

## Decisões técnicas

- **Schema completo no prompt em vez de schema linking**: as 10 tabelas cabem com folga no contexto. Isso evita uma chamada extra por pergunta, o que importa com 50 requisições por dia, e as ferramentas `describe_table`/`distinct_values` cobrem a verificação de valores.
- **Glossário de negócio no prompt**: regras que o schema não revela. Exemplos: receita = faturamento = bilheteria; `lucro_brl` vale 0 sem receita e é igual à receita sem orçamento; margem agregada por grupo, para não ser distorcida por receitas ínfimas; filmes futuros no catálogo; nomes de gênero em inglês.
- **Dados vêm do banco, não do modelo**: o `output_validator` rejeita SQL final não testado e o serviço reexecuta a consulta para montar a tabela e o gráfico.
- **Fallback no cliente**, com `max_retries=0` e timeout por requisição: um 429 de um modelo gratuito troca de modelo em vez de repetir a chamada e consumir a cota diária.
- **Cache só no primeiro turno**: perguntas de acompanhamento dependem do histórico e sempre vão ao agente.
- **Embeddings locais**: a busca semântica não consome cota de LLM nem exige outra API.

## Avaliação

`src/cinerocket/evaluation/dataset.yaml` traz as 14 perguntas do enunciado com SQL de referência. A comparação procura no resultado do agente as colunas-chave da referência pelo conteúdo, não pelo nome, e confere os valores numéricos com tolerância. Também aceita o grau de sobreposição esperado em perguntas que admitem mais de uma interpretação legítima, como cortes de número mínimo de votos.

```bash
uv run cinerocket eval run --limit 5 --delay 5
```

Cada pergunta usa de 2 a 5 requisições ao modelo; planeje a execução pela cota diária.

## Configuração

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `OPENROUTER_API_KEY` | — | Chave do OpenRouter |
| `OPENROUTER_MODELS` | 4 modelos `:free` | Lista JSON, em ordem de preferência |
| `GOOGLE_API_KEY` | — | Chave do Gemini (último fallback) |
| `GEMINI_MODEL` | `gemini-flash-latest` | Modelo Gemini |
| `DATABASE_PATH` | `data/cinerocket.db` | Banco da camada Gold |
| `APP_DB_PATH` | `data/app.db` | Sessões e cache |
| `INDEX_DIR` | `data/index` | Índice semântico |
| `EMBEDDING_MODEL` | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Modelo de embeddings |
| `MAX_ROWS` | `200` | Máximo de linhas retornadas por consulta |
| `QUERY_TIMEOUT_SECONDS` | `45` | Timeout de cada consulta SQL |
| `LLM_TIMEOUT_SECONDS` | `60` | Timeout de cada requisição ao modelo |
| `AGENT_REQUEST_LIMIT` | `8` | Máximo de chamadas ao modelo por pergunta |
| `AGENT_RETRIES` | `3` | Tentativas de autocorreção por ferramenta ou saída |
| `HISTORY_MAX_TURNS` | `6` | Turnos de conversa enviados ao modelo |
| `CACHE_TTL_SECONDS` | `86400` | Validade do cache; `0` desliga |
| `API_URL` | `http://localhost:8000` | Endereço da API usado pela UI |
| `LOG_LEVEL` | `INFO` | Nível de log |

## Desenvolvimento

```bash
make check
```

Roda Ruff (lint e formatação), mypy em modo strict e pytest. Os testes não chamam LLM: usam um modelo simulado do PydanticAI sobre um banco SQLite de teste. O CI no GitHub Actions executa as mesmas etapas e o build da imagem Docker. Para ativar os hooks locais de pre-commit:

```bash
make hooks
```

## Solução de problemas

- **`ModuleNotFoundError: No module named 'cinerocket'` no macOS**: o Python ignora arquivos `.pth` com a flag `hidden`, que às vezes é aplicada ao `.venv`. O `make install` já corrige; manualmente:

  ```bash
  chflags -R nohidden .venv
  ```

- **Erro 429 do OpenRouter**: o pool do modelo gratuito está cheio e o fallback já tenta o próximo modelo. Se todos falharem, verifique a cota com `cinerocket quota`; ela zera às 21h (horário de Brasília).
- **"Banco de dados não encontrado"**: confira se o arquivo está em `data/cinerocket.db` ou ajuste `DATABASE_PATH`.
- **Busca semântica "sem índice"**: rode `make index`.
