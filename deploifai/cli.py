import click

from .context_obj import pass_deploifai_context_obj, DeploifaiContextObj, debug_levels

from .auth.login import login
from .auth.logout import logout


@click.group()
@click.version_option(package_name="deploifai-cli", message="%(prog)s %(version)s")
@pass_deploifai_context_obj
@click.option("--debug", is_flag=True, help="Show debug logs")
@click.option(
    "--debug-level",
    type=click.Choice(debug_levels),
    default="info",
    help="Set debugging level",
)
def cli_group(deploifai: DeploifaiContextObj, debug: bool, debug_level):
    deploifai.debug = debug
    deploifai.debug_level = debug_level
    deploifai.read_config()


cli_group.add_command(login)
cli_group.add_command(logout)


def cli():
    cli_group(auto_envvar_prefix="DEPLOIFAI")


if __name__ == "__main__":
    cli()
