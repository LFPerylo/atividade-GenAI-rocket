---
name: CineRocket Analytics
description: Interface de análise Text-to-SQL sobre a camada Gold da CineData
colors:
  ink: "#16191D"
  ink-muted: "#5E646C"
  surface: "#FFFFFF"
  panel: "#F3F4F2"
  rule: "#E2E4E0"
  grid: "#ECEEEA"
  accent: "#0B6E63"
  accent-wash: "#E3F1EE"
  series: "#008573"
typography:
  headline:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "2rem"
    fontWeight: 700
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    letterSpacing: "-0.02em"
  body:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
  lede:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
  label:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 600
  code:
    fontFamily: "JetBrains Mono, ui-monospace, monospace"
    fontWeight: 400
rounded:
  base: "6px"
  bar: "4px"
spacing:
  section: "1.25rem"
  lede-bottom: "2rem"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.surface}"
    rounded: "{rounded.base}"
  button-example:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.base}"
  button-example-hover:
    textColor: "{colors.accent}"
  sidebar:
    backgroundColor: "{colors.panel}"
  table-header:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
  chart-bar:
    backgroundColor: "{colors.series}"
    rounded: "{rounded.bar}"
---

# Design System: CineRocket Analytics

## Overview

**Creative North Star: "O boletim de bilheteria"**

A interface trata cada resposta como uma página de relatório de bilheteria de revista do setor: o texto vem primeiro, e logo abaixo ficam a tabela-ledger com numerais tabulares, o gráfico de série única e o SQL que sustenta tudo. É uma superfície de operação (modo Operate). Familiaridade é virtude, a densidade é moderada e a marca aparece em detalhes precisos, não em decoração.

Fundo claro, porque o uso é em escritório e durante o dia. Há um único acento verde-petróleo para ações, seleção e foco, e uma única cor de série nos gráficos.

**Key Characteristics:**
- Restrained: neutros levemente esverdeados mais um acento.
- Uma família tipográfica (Archivo) para títulos, rótulos, corpo e dados; monoespaçada só para SQL.
- Numerais tabulares em tabelas, metadados e status.
- Movimento só para comunicar estado (160 ms, ease-out exponencial) e desligado com `prefers-reduced-motion`.

## Colors

- **Ink** `#16191D`: texto principal.
- **Ink muted** `#5E646C`: texto secundário, legendas, eixos.
- **Surface** `#FFFFFF` e **Panel** `#F3F4F2`: área de conteúdo e segundo plano neutro (sidebar, cabeçalho de tabela, fundo de código).
- **Rule** `#E2E4E0` e **Grid** `#ECEEEA`: bordas e grade dos gráficos, sempre recessivas.
- **Accent** `#0B6E63`: botão primário, links, aba ativa, anel de foco, cursor de texto.
- **Accent wash** `#E3F1EE`: seleção de texto.
- **Series** `#008573`: única cor de dados, validada pelo validador de paleta da skill de dataviz (faixa de luminosidade, croma mínimo e contraste ≥ 3:1 sobre branco).

## Typography

Archivo carrega toda a interface com uma escala contida: título da página 2rem/700, subtítulo 1.5rem/600, corpo 15px, lede 1.0625rem limitado a 62ch e rótulos de seção 0.8125rem/600 em ink muted. Tracking de títulos em -0.02em, com `text-wrap: balance`; parágrafos com `text-wrap: pretty`. JetBrains Mono aparece apenas em blocos SQL.

## Layout

Coluna central com no máximo 1040px, sidebar fixa à esquerda com o nome do produto, a ação "Nova conversa", as perguntas de exemplo por categoria (expansores) e o bloco "Ambiente". Cada resposta segue a ordem texto → abas (Gráfico, Dados, SQL, Premissas, só as que existem) → linha de metadados. No mobile a sidebar recolhe e o conteúdo ocupa a largura toda.

## Elevation & Depth

Plano. A hierarquia vem de camadas tonais (surface/panel) e bordas de 1px; não há sombras decorativas.

## Shapes

Raio base de 6px em botões, campos e tabelas, e de 4px nas extremidades das barras dos gráficos. As pílulas ficam restritas às sugestões de pergunta (controle pequeno).

## Components

- **Botão primário**: fundo accent, texto branco, `:active` em `scale(0.97)`.
- **Pergunta de exemplo**: botão secundário alinhado à esquerda, com quebra de linha; no hover, borda e texto em accent.
- **Tabela de resultado**: `st.dataframe` com números no formato local, contagem de linhas e download em CSV.
- **Gráfico**: Plotly com uma série, barras horizontais para rankings e categorias, linha com marcadores de 8px e anel branco de 2px para séries temporais, grade só no eixo de valor e tooltip por marca.
- **Metadados**: modelo em negrito, chamadas, tokens e tempo do SQL; "Resposta em cache" quando não houve chamada ao modelo.
- **Avatares**: ícones Material (pessoa e filme) no lugar dos avatares padrão coloridos do Streamlit.

## Do's and Don'ts

- Faça os dados aparecerem como dados: numerais tabulares e formatação local nas tabelas.
- Use uma única cor de série; destaque com rótulos, nunca com novas cores.
- Não use kickers ou eyebrows acima de títulos, nem cards como estrutura da página.
- Não use gráficos de pizza ou rosca para comparar categorias.
- Não use eixo duplo.
