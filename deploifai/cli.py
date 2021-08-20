import click

from .context_obj import pass_deploifai_context_obj

from .auth.login import login
from .auth.logout import logout


@click.group()
@click.version_option(message="%(prog)s %(version)s")
@pass_deploifai_context_obj
def cli(deploifai):
    pass


cli.add_command(login)
cli.add_command(logout)


if __name__ == "__main__":
    cli()
