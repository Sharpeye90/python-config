"""CLI entry point for the interactive config viewer."""

import sys

import click

import python_config.document

from . import app


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("config_path", type=click.Path(exists=True, dir_okay=False, readable=True))
@click.option(
    "--page-size",
    default=20,
    show_default=True,
    type=click.IntRange(1, 500),
    help="Rows per page for lists, dicts, and root variables.",
)
@click.option("--no-color", is_flag=True, help="Disable Rich styling.")
def main(config_path, page_size, no_color):
    """Browse a python-config file interactively."""

    try:
        doc = python_config.document.load(config_path)
    except Exception as exc:
        raise click.ClickException(str(exc))

    try:
        app.run_viewer(
            doc,
            config_path,
            page_size=page_size,
            no_color=no_color,
        )
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
