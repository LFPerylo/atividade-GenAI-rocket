from collections.abc import Sequence

import numpy as np

from cinerocket.agent.examples import ExampleRetriever, SqlExample, load_examples, render_examples
from cinerocket.application.keys import normalize_question
from cinerocket.evaluation.dataset import load_cases
from cinerocket.semantic.embedder import Vector, normalize

VOCABULARY = ("lucro", "nota", "ator", "genero")


class KeywordEmbedder:
    model_name = "keywords"

    def embed_documents(self, texts: Sequence[str]) -> Vector:
        return normalize(np.array([self._vector(text) for text in texts], dtype=np.float32))

    def embed_query(self, text: str) -> Vector:
        return self.embed_documents([text])[0]

    @staticmethod
    def _vector(text: str) -> list[float]:
        return [float(word in text.lower()) for word in VOCABULARY] + [0.01]


EXAMPLES = [
    SqlExample(question="Qual o lucro por ano?", sql="SELECT 1", notes=["Lucro exige receita e orçamento."]),
    SqlExample(question="Qual ator fez mais filmes?", sql="SELECT 2"),
    SqlExample(question="Qual a nota média por genero?", sql="SELECT 3"),
]


def test_retrieves_most_similar_examples_above_threshold() -> None:
    retriever = ExampleRetriever(EXAMPLES, KeywordEmbedder(), limit=2, min_score=0.5)

    retrieved = retriever.retrieve("Qual o lucro médio dos filmes?")

    assert [example.sql for example in retrieved] == ["SELECT 1"]
    assert "Lucro exige receita e orçamento." in render_examples(retrieved)


def test_bundled_examples_never_leak_evaluation_questions() -> None:
    examples = load_examples()
    evaluation = {normalize_question(case.question) for case in load_cases()}

    assert len(examples) >= 20
    assert not evaluation & {normalize_question(example.question) for example in examples}
