import click
from deploifai.context import (
    pass_deploifai_context_obj,
    DeploifaiContextObj,
    is_authenticated,
    project_found,
)
from deploifai.api import DeploifaiAPIError


@click.command("list")
@pass_deploifai_context_obj
@is_authenticated
def list_data(context: DeploifaiContextObj):
    """
    Command to list all data storages in the current project
    """

    current_workspace = context.global_config["WORKSPACE"]["username"]

    click.secho("Workspace Name: {}".format(current_workspace))

    data_storage_info = context.api.get_data_storages(current_workspace)

    click.echo("Data Storages:")
    for info in data_storage_info:
        click.echo(f"{info['name']} - {info['status']}")
    return
