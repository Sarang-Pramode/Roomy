from __future__ import annotations

import json
import os
import socket
import webbrowser
from pathlib import Path

import typer
import uvicorn

from roomy.storage.sqlite_store import SqliteStore

app = typer.Typer(no_args_is_help=True, help="Roomy — LangChain agent context observability CLI")
sessions_app = typer.Typer(no_args_is_help=True)
app.add_typer(sessions_app, name="sessions")


def _db(db: str | None) -> str:
    return db or os.environ.get("ROOMY_DB_PATH", "./roomy_traces.db")


def _port_accepting_connections(host: str, port: int, *, timeout_s: float = 1.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            return True
    except OSError:
        return False


@sessions_app.command("list")
def sessions_list(db: str | None = typer.Option(None, "--db", help="SQLite database path")) -> None:
    path = _db(db)
    if not Path(path).exists():
        typer.echo(f"No database at {path}", err=True)
        raise typer.Exit(1)
    store = SqliteStore(path)
    rows = store.query_all("SELECT * FROM sessions ORDER BY started_at DESC LIMIT 50")
    for r in rows:
        typer.echo(
            f"{r['session_id']}\t{r['agent_name']}\t{r['status']}\t{r['started_at']}\t{r['ended_at'] or '-'}"
        )


@sessions_app.command("show")
def sessions_show(
    session_id: str = typer.Argument(...),
    db: str | None = typer.Option(None, "--db"),
) -> None:
    store = SqliteStore(_db(db))
    steps = store.query_all(
        "SELECT step_id, step_index, step_type, latency_ms, status FROM steps WHERE session_id = ? ORDER BY step_index",
        (session_id,),
    )
    if not steps:
        typer.echo("No steps for session", err=True)
        raise typer.Exit(1)
    for s in steps:
        typer.echo(
            f"{s['step_index']:3d}  {s['step_type']:10s}  {s['latency_ms'] or '-':>8}ms  {s['status']}  {s['step_id']}"
        )


@app.command("step-dump")
def step_dump(
    step_id: str = typer.Argument(...),
    db: str | None = typer.Option(None, "--db"),
) -> None:
    store = SqliteStore(_db(db))
    llm = store.query_one("SELECT * FROM llm_calls WHERE step_id = ?", (step_id,))
    if not llm:
        typer.echo("No LLM call for step", err=True)
        raise typer.Exit(1)
    req = store.loads(llm["request_payload_json"])
    res = store.loads(llm["response_payload_json"])
    typer.echo(json.dumps({"request": req, "response": res}, indent=2, default=str))


@app.command("tokens")
def tokens_totals(
    session_id: str = typer.Argument(...),
    db: str | None = typer.Option(None, "--db"),
) -> None:
    store = SqliteStore(_db(db))
    row = store.query_one(
        """
        SELECT
          SUM(COALESCE(lc.input_tokens_reported, lc.input_tokens_estimated, 0)) AS inp,
          SUM(COALESCE(lc.output_tokens_reported, lc.output_tokens_estimated, 0)) AS outp,
          SUM(COALESCE(lc.cost_estimate_usd, 0)) AS cost
        FROM llm_calls lc
        JOIN steps s ON s.step_id = lc.step_id
        WHERE s.session_id = ?
        """,
        (session_id,),
    )
    if not row:
        typer.echo("No data", err=True)
        raise typer.Exit(1)
    typer.echo(
        f"input_tokens:  {row['inp'] or 0}\n"
        f"output_tokens: {row['outp'] or 0}\n"
        f"cost_est_usd:  {row['cost'] or 0}"
    )


@app.command("dashboard")
def dashboard(
    host: str = typer.Option("127.0.0.1", "--host", help="Vite dev server host (apps/web npm run dev)"),
    port: int = typer.Option(5173, "--port", help="Vite dev server port"),
    path: str = typer.Option("/", "--path", help="Path on the dev server (default /)"),
    skip_check: bool = typer.Option(
        False,
        "--skip-check",
        help="Open the browser even if nothing is listening (default: verify port first)",
    ),
) -> None:
    """Open the Roomy web UI in your browser (start `npm run dev` in apps/web first)."""
    suffix = path if path.startswith("/") else f"/{path}"
    url = f"http://{host}:{port}{suffix}"
    if not skip_check and not _port_accepting_connections(host, port):
        typer.echo(f"Nothing is accepting connections on {host}:{port} (ERR_CONNECTION_REFUSED).", err=True)
        typer.echo(
            "Start the web UI from the Roomy repo:\n"
            "  cd apps/web && npm install && npm run dev\n"
            "In another terminal, start the API (use the same trace DB as your agent):\n"
            "  roomy serve --db path/to/traces.db --host 127.0.0.1 --port 8765\n"
            "Then run: roomy dashboard\n"
            "Or open with: roomy dashboard --skip-check",
            err=True,
        )
        raise typer.Exit(1)
    typer.echo(f"Opening {url}")
    if not webbrowser.open(url):
        typer.echo("Could not launch a browser; open the URL manually.", err=True)
        raise typer.Exit(1)


@app.command("serve")
def serve(
    db: str | None = typer.Option(None, "--db"),
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8765, "--port"),
) -> None:
    from roomy.api.app import create_app

    path = _db(db)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if not Path(path).exists():
        Path(path).touch()
    api = create_app(path)
    uvicorn.run(api, host=host, port=port, log_level="info")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
