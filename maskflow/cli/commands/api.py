import typer

from maskflow.runtime.settings import get_settings


def register_api_command(app: typer.Typer) -> None:
    @app.command("api")
    def run_api(
        host: str = typer.Option(get_settings().api_host, "--host"),
        port: int = typer.Option(get_settings().api_port, "--port"),
        reload: bool = typer.Option(False, "--reload"),
    ) -> None:
        try:
            import uvicorn
        except ImportError as error:
            raise typer.BadParameter("Install project dependencies: uv sync") from error

        uvicorn.run(
            "maskflow.api.app:create_app",
            factory=True,
            host=host,
            port=port,
            reload=reload,
        )
