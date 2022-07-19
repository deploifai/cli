import click
from deploifai.context import (
    pass_deploifai_context_obj,
    DeploifaiContextObj,
    is_authenticated,
    project_found,
)
from deploifai.api import DeploifaiAPIError


@click.command("list")
@click.option("--project", "-p", help="Project Name")
@pass_deploifai_context_obj
@is_authenticated
def list_data(context: DeploifaiContextObj, project: str):
    """
    Command to list all datasets in the current project
    """

    current_workspace = context.global_config["WORKSPACE"]["username"]

    click.secho("Workspace Name: {}".format(current_workspace))

    if project:
        variables = {"account": {"is": {"username": {"equals": current_workspace}}},
                     "projects": {"every": {"name": {"equals": project}}}}

    elif "id" in context.local_config["PROJECT"]:
        project_id = context.local_config["PROJECT"]["id"]
        variables = {"account": {"is": {"username": {"equals": current_workspace}}},
                     "projects": {"every": {"id": {"equals": project_id}}}}

    else:
        variables = {"account": {"is": {"username": {"equals": current_workspace}}}}

    data_storage_info = context.api.get_data_storages(variables)

    click.echo("Data Storages:")
    for info in data_storage_info:
        click.echo(f"{info['name']} - {info['status']}")
    return
