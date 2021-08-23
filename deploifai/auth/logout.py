import click

from ..context_obj import pass_deploifai_context_obj, DeploifaiContextObj
from . import credentials


@click.command()
@pass_deploifai_context_obj
def logout(deploifai: DeploifaiContextObj):
    """
    Logout as a Deploifai user
    """
    click.echo("should logout!")

    username = deploifai.config["AUTH"]["username"]
    token = credentials.get_auth_token(username)
    click.echo(f"token: {token}")

    credentials.delete_auth_token(username)
