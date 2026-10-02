from functools import cached_property

from cinerocket.database.movies import MovieRepository
from cinerocket.domain.errors import SemanticIndexUnavailableError
from cinerocket.domain.models import MovieMatch
from cinerocket.semantic.embedder import Embedder
from cinerocket.semantic.store import VectorIndexRepository, VectorStore


class SemanticSearch:
    def __init__(
        self, embedder: Embedder, repository: VectorIndexRepository, movies: MovieRepository
    ) -> None:
        self._embedder = embedder
        self._repository = repository
        self._movies = movies

    def is_available(self) -> bool:
        return self._repository.exists()

    @cached_property
    def _store(self) -> VectorStore:
        store = self._repository.load()
        if store.manifest.model_name != self._embedder.model_name:
            raise SemanticIndexUnavailableError(
                f"Índice gerado com '{store.manifest.model_name}', mas o modelo configurado é "
                f"'{self._embedder.model_name}'. Reconstrua com 'cinerocket index build'."
            )
        return store

    def search(self, query: str, limit: int) -> list[MovieMatch]:
        hits = self._store.search(self._embedder.embed_query(query), limit)
        summaries = self._movies.find_by_ids([movie_id for movie_id, _ in hits])
        return [
            MovieMatch(
                movie_id=movie_id,
                title=summaries[movie_id].title,
                release_year=summaries[movie_id].release_year,
                score=round(score, 4),
            )
            for movie_id, score in hits
            if movie_id in summaries
        ]
