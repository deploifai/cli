import click

from deploifai.context import (
    pass_deploifai_context_obj,
    DeploifaiContextObj,
    debug_levels,
)

from .auth import auth
from .application import application
from .project import project
from .data import data

commands = {"auth": auth, "project": project, "data": data, "application": application}


@click.group(commands=commands)
@click.version_option(package_name="deploifai-cli", message="%(prog)s %(version)s")
@pass_deploifai_context_obj
@click.option("--debug", is_flag=True, help="Show debug logs")
@click.option(
    "--debug-level",
    type=click.Choice(debug_levels),
    default="info",
    help="Set debugging level",
)
def cli(deploifai: DeploifaiContextObj, debug: bool, debug_level):
    """
    Deploifai CLI
    """
    deploifai.debug = debug
    deploifai.debug_level = debug_level
    deploifai.read_config()
    deploifai.initialise_api()


def main():
    cli(auto_envvar_prefix="DEPLOIFAI")


if __name__ == "__main__":
    main()
