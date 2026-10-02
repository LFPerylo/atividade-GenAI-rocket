from collections.abc import Sequence
from dataclasses import dataclass

from cinerocket.database.connection import ReadOnlyDatabase

SQLITE_MAX_VARIABLES = 900


@dataclass(frozen=True)
class MovieSynopsis:
    movie_id: str
    title: str
    synopsis: str

    @property
    def document(self) -> str:
        return f"{self.title}. {self.synopsis}"


@dataclass(frozen=True)
class MovieSummary:
    movie_id: str
    title: str
    release_year: int | None


class MovieRepository:
    def __init__(self, database: ReadOnlyDatabase) -> None:
        self._database = database

    def list_synopses(self) -> list[MovieSynopsis]:
        with self._database.connect() as connection:
            rows = connection.execute(
                "SELECT sk_movie_id, titulo, sinopse FROM dim_movies "
                "WHERE sinopse IS NOT NULL AND TRIM(sinopse) <> '' ORDER BY sk_movie_id"
            ).fetchall()
        return [MovieSynopsis(movie_id=row[0], title=row[1], synopsis=row[2]) for row in rows]

    def find_by_ids(self, movie_ids: Sequence[str]) -> dict[str, MovieSummary]:
        summaries: dict[str, MovieSummary] = {}
        with self._database.connect() as connection:
            for start in range(0, len(movie_ids), SQLITE_MAX_VARIABLES):
                chunk = movie_ids[start : start + SQLITE_MAX_VARIABLES]
                placeholders = ", ".join("?" for _ in chunk)
                rows = connection.execute(
                    f"SELECT sk_movie_id, titulo, ano_lancamento FROM dim_movies "
                    f"WHERE sk_movie_id IN ({placeholders})",
                    tuple(chunk),
                )
                summaries.update(
                    (row[0], MovieSummary(movie_id=row[0], title=row[1], release_year=row[2])) for row in rows
                )
        return summaries
