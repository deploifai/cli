import click
from .auth.login import login
from .auth.logout import logout


@click.group()
@click.version_option(message="%(prog)s %(version)s")
def cli():
    pass


cli.add_command(login)
cli.add_command(logout)


if __name__ == "__main__":
    cli()
