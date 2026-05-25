import typer

from maskflow.runtime.settings import get_settings


def register_web_command(app: typer.Typer) -> None:
    @app.command("web")
    def run_web(
        host: str = typer.Option(get_settings().api_host, "--host"),
        port: int = typer.Option(get_settings().api_port, "--port"),
        reload: bool = typer.Option(False, "--reload"),
    ) -> None:
        try:
            import uvicorn

            from maskflow.api.app import create_app
        except ImportError as error:
            raise typer.BadParameter("Install project dependencies: uv sync") from error

        uvicorn.run(
            create_app(include_web=True),
            host=host,
            port=port,
            reload=reload,
        )
