# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Banca avaliadora do Rocket Lab (Visagio), que usa o produto como um usuário de negócio da CineData Analytics usaria: faz perguntas em linguagem natural sobre o catálogo de filmes e confere se as respostas são corretas, rastreáveis e bem fundamentadas. Usam em desktop, no escritório, durante o dia.

## Product Purpose

CineRocket Analytics permite que quem não sabe SQL consulte em tempo real a camada Gold da CineData (SQLite dimensional com filmes, desempenho financeiro, notas, elenco, gêneros, produtoras e avaliações). Sucesso: a pergunta vira uma resposta correta em português, acompanhada dos dados, do SQL executado e das premissas adotadas.

## Positioning

Agente Text-to-SQL que testa e autocorrige a própria consulta antes de responder, executa somente leitura com guardrails, combina SQL com busca semântica nas sinopses e devolve dados vindos do banco, nunca números gerados pelo modelo.

## Operating Context

Avaliação da atividade GenAI do Rocket Lab 26.2. As perguntas de referência estão no PDF da atividade, em cinco categorias: bilheteria e finanças, popularidade e engajamento, elenco e equipe, gêneros e produtoras, avaliações dos usuários. Modelos gratuitos do OpenRouter limitam a 50 requisições por dia, então cache e economia de chamadas importam.

## Capabilities and Constraints

- Interface em Streamlit consumindo a API FastAPI do projeto; também há CLI.
- Respostas trazem texto, tabela de resultado, SQL, premissas e gráfico sugerido.
- Memória de conversa por sessão, cache de respostas, fallback entre modelos (OpenRouter e Gemini).
- Somente leitura sobre o banco; perguntas fora do catálogo são recusadas.

## Brand Commitments

Nome do produto: CineRocket Analytics. Sem logo, paleta ou tipografia obrigatórias.

## Evidence on Hand

Dados reais do arquivo `data/cinerocket.db` (95.645 filmes). Não existem depoimentos, clientes ou métricas de uso; não inventar.

## Product Principles

- Toda afirmação numérica é rastreável até o SQL e a tabela exibidos.
- Transparência sobre premissas e interpretações da pergunta.
- Clareza para quem não é técnico, sem esconder o detalhe técnico de quem quer conferir.
- Economia de requisições ao modelo como parte da experiência.
