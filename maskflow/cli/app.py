import typer

from maskflow.cli.commands import register_commands
from maskflow.cli.help import LocalizedTyperGroup
from maskflow.cli.i18n import tr

app = typer.Typer(
    cls=LocalizedTyperGroup,
    help=tr("app_help"),
    no_args_is_help=True,
    add_completion=False,
    context_settings={
        "help_option_names": ["--help", "-help", "-h", "/?"],
    },
)

register_commands(app)


if __name__ == "__main__":
    app()
