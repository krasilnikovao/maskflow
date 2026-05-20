from __future__ import annotations

from typing import Any

import click
from click.core import Context, Option, Parameter
from typer.core import TyperCommand, TyperGroup

from maskflow.cli.i18n import tr


def _show_help_callback(
    ctx: Context,
    _param: Parameter,
    value: bool,
) -> None:
    if not value or ctx.resilient_parsing:
        return

    click.echo(ctx.get_help(), color=ctx.color)
    ctx.exit()


def _localized_help_option(command: Any, ctx: Context) -> Option | None:
    help_options = command.get_help_option_names(ctx)

    if not help_options or not command.add_help_option:
        return None

    return click.Option(
        help_options,
        is_flag=True,
        is_eager=True,
        expose_value=False,
        help=tr("help_option"),
        callback=_show_help_callback,
    )


def _localize_help_text(text: str) -> str:
    replacements = {
        "Usage:": f"{tr('usage')}:",
        "Options": tr("options"),
        "Commands": tr("commands"),
        "Arguments": tr("arguments"),
        "Show this message and exit.": tr("help_option"),
    }

    for source, target in replacements.items():
        text = text.replace(source, target)

    return text


class LocalizedTyperCommand(TyperCommand):
    def get_help_option(self, ctx: Context) -> Option | None:
        return _localized_help_option(self, ctx)

    def get_help(self, ctx: Context) -> str:
        return _localize_help_text(super().get_help(ctx))


class LocalizedTyperGroup(TyperGroup):
    def get_help_option(self, ctx: Context) -> Option | None:
        return _localized_help_option(self, ctx)

    def get_help(self, ctx: Context) -> str:
        return _localize_help_text(super().get_help(ctx))
