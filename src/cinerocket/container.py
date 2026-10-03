from dataclasses import dataclass
from datetime import date
from functools import partial

from cinerocket.agent.builder import build_agent
from cinerocket.agent.deps import AgentDeps
from cinerocket.agent.prompts import PROMPT_VERSION
from cinerocket.application.service import AnalyticsService, ServicePolicy
from cinerocket.config import Settings
from cinerocket.database.catalog import SchemaCatalog
from cinerocket.database.connection import ReadOnlyDatabase
from cinerocket.database.executor import QueryExecutor
from cinerocket.database.movies import MovieRepository
from cinerocket.guardrails.input import QuestionGuard
from cinerocket.guardrails.sql import SqlGuard
from cinerocket.llm.factory import ModelChain, build_model_chain
from cinerocket.semantic.embedder import FastEmbedEmbedder
from cinerocket.semantic.search import SemanticSearch
from cinerocket.semantic.store import NumpyIndexRepository
from cinerocket.storage.cache import SQLiteResponseCache
from cinerocket.storage.sessions import SQLiteSessionStore


@dataclass(frozen=True)
class Container:
    settings: Settings
    database: ReadOnlyDatabase
    catalog: SchemaCatalog
    executor: QueryExecutor
    movies: MovieRepository
    embedder: FastEmbedEmbedder
    index: NumpyIndexRepository
    semantic: SemanticSearch
    model_chain: ModelChain
    service: AnalyticsService


def build_container(settings: Settings, model_chain: ModelChain | None = None) -> Container:
    database = ReadOnlyDatabase(settings.database_path, settings.query_timeout_seconds)
    catalog = SchemaCatalog(database, settings.excluded_tables)
    executor = QueryExecutor(database, SqlGuard(lambda: catalog.table_names), settings.max_rows)
    movies = MovieRepository(database)
    embedder = FastEmbedEmbedder(
        settings.embedding_model, settings.embedding_cache_dir, settings.embedding_batch_size
    )
    index = NumpyIndexRepository(settings.index_dir)
    semantic = SemanticSearch(embedder, index, movies)
    chain = model_chain or build_model_chain(settings)
    agent = build_agent(
        chain.model,
        retries=settings.agent_retries,
        history_max_turns=settings.history_max_turns,
    )
    service = AnalyticsService(
        agent=agent,
        deps_factory=partial(
            new_agent_deps,
            catalog=catalog,
            executor=executor,
            semantic=semantic,
            preview_rows=settings.preview_rows,
            semantic_limit=settings.semantic_search_limit,
        ),
        sessions=SQLiteSessionStore(settings.app_db_path),
        cache=SQLiteResponseCache(settings.app_db_path, settings.cache_ttl_seconds),
        question_guard=QuestionGuard(settings.max_question_length),
        policy=ServicePolicy(
            request_limit=settings.agent_request_limit,
            history_max_turns=settings.history_max_turns,
        ),
        cache_scope=lambda: (catalog.fingerprint, chain.fingerprint, PROMPT_VERSION),
    )
    return Container(
        settings=settings,
        database=database,
        catalog=catalog,
        executor=executor,
        movies=movies,
        embedder=embedder,
        index=index,
        semantic=semantic,
        model_chain=chain,
        service=service,
    )


def new_agent_deps(
    *,
    catalog: SchemaCatalog,
    executor: QueryExecutor,
    semantic: SemanticSearch,
    preview_rows: int,
    semantic_limit: int,
) -> AgentDeps:
    return AgentDeps(
        catalog=catalog,
        executor=executor,
        semantic=semantic,
        today=date.today(),
        preview_rows=preview_rows,
        semantic_limit=semantic_limit,
    )
