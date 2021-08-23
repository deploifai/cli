import click

from ..context_obj import pass_deploifai_context_obj, DeploifaiContextObj
from . import credentials


@click.command()
@pass_deploifai_context_obj
def login(deploifai: DeploifaiContextObj):
    """
    Login as a Deploifai user
    """
    username = "98sean98"
    token = "some-token"

    deploifai.config["AUTH"]["username"] = username

    credentials.save_auth_token(username, token)

    deploifai.save_config()
