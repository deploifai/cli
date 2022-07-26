import click

from deploifai.context import (
    is_authenticated,
    pass_deploifai_context_obj,
    DeploifaiContextObj,
)

@click.command()
@is_authenticated
@pass_deploifai_context_obj
def status(context: DeploifaiContextObj):
    click.secho("You are logged in", fg="green")

    workspace = context.global_config["WORKSPACE"]["username"]
    click.secho(f"You are currently in the workspace {workspace}", fg="blue")