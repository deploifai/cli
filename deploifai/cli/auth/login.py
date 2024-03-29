import click
import requests
from deploifai.cli.utilities import environment
from deploifai.cli.utilities import credentials
from deploifai.cli.context import pass_deploifai_context_obj, DeploifaiContextObj


@click.command()
@pass_deploifai_context_obj
@click.option(
    "-u",
    "--username",
    prompt=True,
    help="Username on Deploifai (Optionally can be set via DEPLOIFAI_LOGIN_USERNAME environment variable)",
)
@click.option(
    "-t",
    "--token",
    prompt="Personal access token",
    help="Generated personal access token on Deploifai (Optionally can be set via DEPLOIFAI_LOGIN_TOKEN environment variable)",
)
def login(deploifai: DeploifaiContextObj, username: str, token: str):
    """
    Login using personal access token
    """
    try:
        url = f"{environment.backend_url}/auth/login/cli"
        deploifai.debug_msg(f"Login url: {url}")
        response = requests.post(
            url,
            json={"username": username},
            headers={"authorization": token},
        )
    except requests.exceptions.RequestException as e:
        deploifai.debug_msg(e, level="error")
        click.echo("Error sending network request")
        return

    if response.status_code != 200:
        click.secho("Invalid login", fg="red")
        return

    click.secho("Login success", fg="green")

    deploifai.global_config["AUTH"]["username"] = username
    deploifai.global_config["WORKSPACE"]["username"] = username

    try:
        credentials.save_auth_token(username, token)
        deploifai.debug_msg("Saved auth token in keyring")
    except Exception as e:
        deploifai.debug_msg(e, level="error")
        click.echo("Error saving auth token")
        return

    deploifai.save_config()
