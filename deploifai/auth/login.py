import click

from ..context_obj import pass_deploifai_context_obj, DeploifaiContextObj


@click.command()
@pass_deploifai_context_obj
def login(deploifai: DeploifaiContextObj):
    """
    Login as a Deploifai user
    """
    click.echo("open deploifai login page")
    auth = deploifai.config["AUTH"]
    # auth["authorization"] = "some_token"

    deploifai.save_config()
