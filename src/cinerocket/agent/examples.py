import hashlib
import logging
from collections.abc import Sequence
from functools import cached_property
from pathlib import Path

import numpy as np
import yaml
from pydantic import BaseModel, Field, TypeAdapter

from cinerocket.semantic.embedder import Embedder, Vector

logger = logging.getLogger(__name__)

DEFAULT_EXAMPLES = Path(__file__).with_name("examples.yaml")
WARM_UP_QUESTION = "Quais filmes tiveram a maior receita?"


class SqlExample(BaseModel):
    question: str
    sql: str
    notes: list[str] = Field(default_factory=list)
    semantic: bool = False

    @property
    def document(self) -> str:
        return " ".join((self.question, *self.notes))


EXAMPLES = TypeAdapter(list[SqlExample])


def load_examples(path: Path = DEFAULT_EXAMPLES) -> list[SqlExample]:
    return EXAMPLES.validate_python(yaml.safe_load(path.read_text(encoding="utf-8")))


def render_examples(examples: Sequence[SqlExample]) -> str:
    blocks = [
        "## Exemplos de referência",
        "Casos já resolvidos de perguntas parecidas com a atual. Siga os critérios e o padrão de SQL, "
        "adaptando-os à pergunta; nunca copie números deles, sempre execute a sua própria consulta.",
    ]
    for example in examples:
        notes = "\n".join(f"- {note}" for note in example.notes)
        blocks.append(f"### {example.question}\n{notes}\n```sql\n{example.sql.strip()}\n```")
    return "\n\n".join(blocks)


class ExampleRetriever:
    def __init__(
        self, examples: Sequence[SqlExample], embedder: Embedder, limit: int, min_score: float
    ) -> None:
        self._examples = list(examples)
        self._embedder = embedder
        self._limit = limit
        self._min_score = min_score

    @cached_property
    def version(self) -> str:
        payload = EXAMPLES.dump_json(self._examples)
        return hashlib.sha256(payload).hexdigest()[:12]

    @cached_property
    def _vectors(self) -> Vector:
        return self._embedder.embed_documents([example.document for example in self._examples])

    def warm_up(self) -> None:
        logger.info("Carregando o modelo de embeddings dos exemplos de referência.")
        self.retrieve(WARM_UP_QUESTION)

    def retrieve(self, question: str) -> list[SqlExample]:
        if not self._examples or self._limit == 0:
            return []
        try:
            scores = self._vectors @ self._embedder.embed_query(question)
        except Exception:
            logger.warning("Exemplos de referência indisponíveis; seguindo sem few-shot.", exc_info=True)
            return []
        ranked = np.argsort(-scores)[: self._limit]
        return [self._examples[index] for index in ranked if scores[index] >= self._min_score]
