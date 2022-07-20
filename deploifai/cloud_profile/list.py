import click
from deploifai.context import (
    pass_deploifai_context_obj,
    DeploifaiContextObj,
    is_authenticated,
)
from deploifai.api import DeploifaiAPIError


@click.command("list")
@pass_deploifai_context_obj
@is_authenticated
def list_profile(context: DeploifaiContextObj):
    """
    List all cloud profiles in the current workspace
    """

    current_workspace = context.global_config["WORKSPACE"]["username"]

    click.secho("Workspace Name: {}".format(current_workspace), fg="blue")

    cloud_profile_info = context.api.get_cloud_profiles(current_workspace)

    if len(cloud_profile_info) == 0:
        click.secho("No cloud profiles exist", fg="yellow")
        return

    click.secho("All cloud profiles:", fg="blue")
    for info in cloud_profile_info:
        click.echo(f"{info.name} - {info.provider}")
    return
