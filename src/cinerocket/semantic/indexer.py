import logging
from collections.abc import Callable

import numpy as np

from cinerocket.database.movies import MovieRepository
from cinerocket.semantic.embedder import Embedder
from cinerocket.semantic.store import IndexManifest, VectorIndexRepository

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, int], None]


class SynopsisIndexer:
    def __init__(
        self,
        movies: MovieRepository,
        embedder: Embedder,
        repository: VectorIndexRepository,
        chunk_size: int = 2048,
    ) -> None:
        self._movies = movies
        self._embedder = embedder
        self._repository = repository
        self._chunk_size = chunk_size

    def build(self, on_progress: ProgressCallback | None = None) -> IndexManifest:
        synopses = self._movies.list_synopses()
        total = len(synopses)
        logger.info("Indexando %d sinopses com %s", total, self._embedder.model_name)
        chunks = []
        for start in range(0, total, self._chunk_size):
            batch = synopses[start : start + self._chunk_size]
            chunks.append(self._embedder.embed_documents([movie.document for movie in batch]))
            if on_progress is not None:
                on_progress(min(start + self._chunk_size, total), total)
        vectors = np.vstack(chunks) if chunks else np.empty((0, 0), dtype=np.float32)
        return self._repository.save(
            [movie.movie_id for movie in synopses], vectors, self._embedder.model_name
        )
