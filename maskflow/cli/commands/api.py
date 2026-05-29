import typer

from maskflow.runtime.settings import get_settings
from maskflow.utils.logging import configure_logging


def register_api_command(app: typer.Typer) -> None:
    @app.command("api")
    def run_api(
        host: str = typer.Option(get_settings().api_host, "--host"),
        port: int = typer.Option(get_settings().api_port, "--port"),
        log_level: str = typer.Option(get_settings().log_level, "--log-level"),
        reload: bool = typer.Option(False, "--reload"),
    ) -> None:
        configure_logging(level=log_level)

        try:
            import uvicorn
        except ImportError as error:
            raise typer.BadParameter("Install project dependencies: uv sync") from error

        uvicorn.run(
            "maskflow.api.app:create_app",
            factory=True,
            host=host,
            port=port,
            log_level=log_level.lower(),
            reload=reload,
        )
