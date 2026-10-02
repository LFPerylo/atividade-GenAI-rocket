import asyncio
import subprocess
import sys
from pathlib import Path
from typing import Annotated

import typer
import uvicorn
from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TimeElapsedColumn

from cinerocket.cli.render import render_response
from cinerocket.config import Settings, get_settings
from cinerocket.container import Container, build_container
from cinerocket.database.connection import ReadOnlyDatabase
from cinerocket.database.movies import MovieRepository
from cinerocket.domain.errors import CineRocketError
from cinerocket.llm.quota import fetch_openrouter_quota
from cinerocket.observability import configure_logging
from cinerocket.semantic.embedder import FastEmbedEmbedder
from cinerocket.semantic.indexer import SynopsisIndexer
from cinerocket.semantic.store import NumpyIndexRepository

app = typer.Typer(
    no_args_is_help=True, help="CineRocket Analytics: perguntas em linguagem natural sobre filmes."
)
index_app = typer.Typer(no_args_is_help=True, help="Índice semântico das sinopses.")
app.add_typer(index_app, name="index")

console = Console()
EXIT_COMMANDS = {"sair", "exit", "quit", ":q"}


def load_settings() -> Settings:
    settings = get_settings()
    configure_logging(settings.log_level)
    return settings


def load_container() -> Container:
    try:
        return build_container(load_settings())
    except CineRocketError as error:
        console.print(f"[red]{error}[/red]")
        raise typer.Exit(code=1) from error


@app.command()
def ask(
    question: Annotated[str, typer.Argument(help="Pergunta em linguagem natural.")],
    session: Annotated[str | None, typer.Option(help="ID de sessão para manter o contexto.")] = None,
    as_json: Annotated[bool, typer.Option("--json", help="Imprime a resposta completa em JSON.")] = False,
) -> None:
    """Faz uma pergunta única ao agente."""
    container = load_container()
    try:
        with console.status("Analisando os dados..."):
            response = asyncio.run(container.service.ask(question, session))
    except CineRocketError as error:
        console.print(f"[red]{error}[/red]")
        raise typer.Exit(code=1) from error
    if as_json:
        console.print_json(response.model_dump_json())
    else:
        render_response(console, response)


@app.command()
def chat() -> None:
    """Abre uma conversa interativa com memória no terminal."""
    container = load_container()
    asyncio.run(_chat_loop(container))


async def _chat_loop(container: Container) -> None:
    session_id: str | None = None
    console.print("[bold magenta]CineRocket Analyst[/bold magenta] — digite sua pergunta ou 'sair'.\n")
    while True:
        question = (await asyncio.to_thread(console.input, "[bold cyan]Você:[/bold cyan] ")).strip()
        if not question:
            continue
        if question.lower() in EXIT_COMMANDS:
            break
        try:
            with console.status("Analisando os dados..."):
                response = await container.service.ask(question, session_id)
        except CineRocketError as error:
            console.print(f"[red]{error}[/red]\n")
            continue
        session_id = response.session_id
        render_response(console, response)


@app.command()
def quota() -> None:
    """Mostra a cota diária de requisições gratuitas do OpenRouter."""
    settings = load_settings()
    if settings.openrouter_api_key is None:
        console.print("[red]OPENROUTER_API_KEY não configurada.[/red]")
        raise typer.Exit(code=1)
    data = asyncio.run(fetch_openrouter_quota(settings.openrouter_api_key.get_secret_value()))
    daily = data.free_model_daily_requests
    if daily is None:
        console.print_json(data.model_dump_json())
        return
    console.print(
        f"Requisições gratuitas hoje: [bold]{daily.used}[/bold] de {daily.limit} (restam {daily.remaining})"
    )


@app.command()
def serve(
    host: Annotated[str, typer.Option()] = "127.0.0.1",
    port: Annotated[int, typer.Option()] = 8000,
    reload: Annotated[bool, typer.Option()] = False,
) -> None:
    """Sobe a API FastAPI."""
    uvicorn.run("cinerocket.api.app:create_app", factory=True, host=host, port=port, reload=reload)


@app.command()
def ui(port: Annotated[int, typer.Option()] = 8501) -> None:
    """Sobe a interface Streamlit (requer a API em execução)."""
    script = Path(__file__).resolve().parent.parent / "ui" / "app.py"
    command = [sys.executable, "-m", "streamlit", "run", str(script), "--server.port", str(port)]
    raise typer.Exit(code=subprocess.call(command))


@index_app.command("build")
def build_index(
    parallel: Annotated[
        int | None, typer.Option(help="Processos de embedding (0 = todos os núcleos).")
    ] = None,
) -> None:
    """Gera os embeddings das sinopses para a busca semântica."""
    settings = load_settings()
    database = ReadOnlyDatabase(settings.database_path, settings.query_timeout_seconds)
    embedder = FastEmbedEmbedder(
        settings.embedding_model, settings.embedding_cache_dir, settings.embedding_batch_size, parallel
    )
    repository = NumpyIndexRepository(settings.index_dir)
    indexer = SynopsisIndexer(MovieRepository(database), embedder, repository)
    columns = (*Progress.get_default_columns()[:-1], BarColumn(), MofNCompleteColumn(), TimeElapsedColumn())
    with Progress(*columns, console=console) as progress:
        task = progress.add_task("Indexando sinopses", total=None)
        manifest = indexer.build(lambda done, total: progress.update(task, completed=done, total=total))
    console.print(
        f"[green]Índice criado:[/green] {manifest.size} filmes, dimensão {manifest.dimension}, "
        f"modelo {manifest.model_name}"
    )
