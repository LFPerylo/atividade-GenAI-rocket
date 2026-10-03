from collections.abc import Iterable

WORDS = {
    "ano": "ano",
    "lancamento": "de lançamento",
    "titulo": "título",
    "genero": "gênero",
    "produtora": "produtora",
    "pessoa": "pessoa",
    "ator": "ator",
    "diretor": "diretor",
    "receita": "receita",
    "faturamento": "faturamento",
    "bilheteria": "bilheteria",
    "orcamento": "orçamento",
    "lucro": "lucro",
    "margem": "margem",
    "medio": "médio",
    "media": "média",
    "total": "total",
    "nota": "nota",
    "imdb": "IMDb",
    "tmdb": "TMDB",
    "usuarios": "dos usuários",
    "qtd": "quantidade de",
    "quantidade": "quantidade",
    "filmes": "filmes",
    "avaliacoes": "avaliações",
    "votos": "votos",
    "popularidade": "popularidade",
    "duracao": "duração",
    "minutos": "em minutos",
    "participacoes": "participações",
    "divergencia": "divergência",
    "juntos": "juntos",
}
COLUMNS = {
    "qtd_imdb": "Votos no IMDb",
    "qtd_tmdb": "Votos no TMDB",
    "nome_pessoa": "Pessoa",
    "nome_produtora": "Produtora",
    "status_filme": "Situação",
}
SUFFIXES = {"brl": "R$", "usd": "US$", "pct": "%", "percent": "%", "percentual": "%", "min": "min"}
DROPPED = {"nome", "de", "do", "da", "em"}
SCALES = ((1e9, "bilhões"), (1e6, "milhões"), (1e3, "mil"))


def humanize(column: str) -> str:
    if column.lower() in COLUMNS:
        return COLUMNS[column.lower()]
    tokens = [token for token in column.lower().split("_") if token]
    unit = next((SUFFIXES[token] for token in reversed(tokens) if token in SUFFIXES), None)
    words = [WORDS.get(token, token) for token in tokens if token not in SUFFIXES and token not in DROPPED]
    label = " ".join(words) or column
    label = label[0].upper() + label[1:]
    return f"{label} ({unit})" if unit else label


def value_scale(values: Iterable[float]) -> tuple[float, str | None]:
    peak = max((abs(value) for value in values), default=0.0)
    return next(((factor, name) for factor, name in SCALES if peak >= factor * 10), (1.0, None))


def scaled_title(label: str, unit: str | None) -> str:
    return f"{label}, em {unit}" if unit else label
