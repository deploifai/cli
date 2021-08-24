import click
import requests

from ..context_obj import pass_deploifai_context_obj, DeploifaiContextObj
from . import credentials


@click.command()
@pass_deploifai_context_obj
@click.option("-u", "--username", prompt=True, help="Username on Deploifai")
@click.option(
    "-t",
    "--token",
    prompt="Personal access token",
    help="Generated personal access token on Deploifai",
)
def login(deploifai: DeploifaiContextObj, username: str, token: str):
    """
    Login to access Deploifai using a personal access token
    """
    try:
        response = requests.post(
            "http://localhost:4000/auth/login/cli",
            json={"username": username},
            headers={"authorization": "deploifai-" + token},
        )
    except requests.exceptions.RequestException as e:
        deploifai.debug_msg(e, level="error")
        click.echo("Error sending network request")
        return

    if response.status_code != 200:
        click.secho("Invalid login", fg="red")
        return

    click.secho("Login success", fg="green")

    deploifai.config["AUTH"]["username"] = username

    try:
        credentials.save_auth_token(username, token)
        deploifai.debug_msg("Saved auth token in keyring")
    except Exception as e:
        deploifai.debug_msg(e, level="error")
        click.echo("Error saving auth token")
        return

    deploifai.save_config()
