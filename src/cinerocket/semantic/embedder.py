from collections.abc import Sequence
from functools import cached_property
from pathlib import Path
from typing import Protocol

import numpy as np
from fastembed import TextEmbedding
from numpy.typing import NDArray

Vector = NDArray[np.float32]


def normalize(vectors: Vector) -> Vector:
    norms = np.linalg.norm(vectors, axis=-1, keepdims=True)
    return (vectors / np.clip(norms, 1e-12, None)).astype(np.float32)


class Embedder(Protocol):
    @property
    def model_name(self) -> str: ...

    def embed_documents(self, texts: Sequence[str]) -> Vector: ...

    def embed_query(self, text: str) -> Vector: ...


class FastEmbedEmbedder:
    def __init__(
        self, model_name: str, cache_dir: Path, batch_size: int = 256, parallel: int | None = None
    ) -> None:
        self._model_name = model_name
        self._cache_dir = cache_dir
        self._batch_size = batch_size
        self._parallel = parallel

    @property
    def model_name(self) -> str:
        return self._model_name

    @cached_property
    def _model(self) -> TextEmbedding:
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        return TextEmbedding(model_name=self._model_name, cache_dir=str(self._cache_dir))

    def embed_documents(self, texts: Sequence[str]) -> Vector:
        embeddings = self._model.embed(list(texts), batch_size=self._batch_size, parallel=self._parallel)
        return normalize(np.asarray(list(embeddings), dtype=np.float32))

    def embed_query(self, text: str) -> Vector:
        embedding = next(iter(self._model.query_embed(text)))
        return normalize(np.asarray(embedding, dtype=np.float32))
