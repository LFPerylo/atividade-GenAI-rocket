import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, Field

from cinerocket.domain.errors import SemanticIndexUnavailableError
from cinerocket.semantic.embedder import Vector


class IndexManifest(BaseModel):
    model_name: str
    dimension: int
    size: int
    built_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class VectorStore(Protocol):
    @property
    def manifest(self) -> IndexManifest: ...

    def search(self, query: Vector, limit: int) -> list[tuple[str, float]]: ...


class VectorIndexRepository(Protocol):
    def exists(self) -> bool: ...

    def load(self) -> VectorStore: ...

    def save(self, ids: list[str], vectors: Vector, model_name: str) -> IndexManifest: ...


class NumpyVectorStore:
    def __init__(self, ids: NDArray[np.str_], vectors: Vector, manifest: IndexManifest) -> None:
        self._ids = ids
        self._vectors = vectors
        self._manifest = manifest

    @property
    def manifest(self) -> IndexManifest:
        return self._manifest

    def search(self, query: Vector, limit: int) -> list[tuple[str, float]]:
        scores = self._vectors @ query
        size = min(limit, scores.shape[0])
        if size == 0:
            return []
        top = np.argpartition(-scores, size - 1)[:size]
        ranked = top[np.argsort(-scores[top])]
        return [(str(self._ids[index]), float(scores[index])) for index in ranked]


class NumpyIndexRepository:
    VECTORS_FILE = "vectors.npy"
    IDS_FILE = "ids.npy"
    MANIFEST_FILE = "manifest.json"

    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def exists(self) -> bool:
        return all(
            (self._directory / name).is_file()
            for name in (self.VECTORS_FILE, self.IDS_FILE, self.MANIFEST_FILE)
        )

    def load(self) -> NumpyVectorStore:
        if not self.exists():
            raise SemanticIndexUnavailableError(
                f"Índice semântico não encontrado em '{self._directory}'. Execute 'cinerocket index build'."
            )
        manifest = IndexManifest.model_validate_json((self._directory / self.MANIFEST_FILE).read_text())
        vectors = np.load(self._directory / self.VECTORS_FILE, mmap_mode="r")
        ids = np.load(self._directory / self.IDS_FILE)
        return NumpyVectorStore(ids=ids, vectors=vectors, manifest=manifest)

    def save(self, ids: list[str], vectors: Vector, model_name: str) -> IndexManifest:
        self._directory.mkdir(parents=True, exist_ok=True)
        manifest = IndexManifest(model_name=model_name, dimension=int(vectors.shape[1]), size=len(ids))
        np.save(self._directory / self.VECTORS_FILE, vectors.astype(np.float32))
        np.save(self._directory / self.IDS_FILE, np.asarray(ids))
        (self._directory / self.MANIFEST_FILE).write_text(
            json.dumps(manifest.model_dump(mode="json"), indent=2)
        )
        return manifest
