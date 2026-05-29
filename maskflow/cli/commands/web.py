import typer

from maskflow.runtime.settings import get_settings
from maskflow.utils.logging import configure_logging


def register_web_command(app: typer.Typer) -> None:
    @app.command("web")
    def run_web(
        host: str = typer.Option(get_settings().api_host, "--host"),
        port: int = typer.Option(get_settings().api_port, "--port"),
        log_level: str = typer.Option(get_settings().log_level, "--log-level"),
        reload: bool = typer.Option(False, "--reload"),
    ) -> None:
        configure_logging(level=log_level)

        try:
            import uvicorn

            from maskflow.api.app import create_app
        except ImportError as error:
            raise typer.BadParameter("Install project dependencies: uv sync") from error

        uvicorn.run(
            create_app(include_web=True),
            host=host,
            port=port,
            log_level=log_level.lower(),
            reload=reload,
        )
