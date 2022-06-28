import click

from deploifai.context import pass_deploifai_context_obj, DeploifaiContextObj
from deploifai.utilities import credentials


@click.command()
@pass_deploifai_context_obj
def logout(deploifai: DeploifaiContextObj):
    """
    Logout to remove access
    """
    auth = deploifai.global_config["AUTH"]
    username = auth.get("username")

    if username is None:
        click.secho("Not logged in")
        return

    try:
        credentials.delete_auth_token(username)
        deploifai.debug_msg("Deleted auth token in keyring")

    except Exception as e:
        deploifai.debug_msg(e, level="error")
        click.secho("Logout error")
        return

    auth = deploifai.global_config["AUTH"]
    auth.pop("username")

    deploifai.save_config()

    click.secho("Logout success", fg="green")
