from typer import Typer

from maskflow.cli.commands.api import register_api_command
from maskflow.cli.commands.batch import register_batch_commands
from maskflow.cli.commands.mask import register_mask_commands
from maskflow.cli.commands.models import register_model_commands
from maskflow.cli.commands.web import register_web_command


def register_commands(app: Typer) -> None:
    register_mask_commands(app)
    register_batch_commands(app)
    register_model_commands(app)
    register_api_command(app)
    register_web_command(app)
