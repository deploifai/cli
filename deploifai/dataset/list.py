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
        # checking if project exists
        fragment = """
                    fragment project on Project {
                        id 
                    }
                    """
        where_project = {"name": {"equals": project}}
        try:
            projects_data = context.api.get_projects(workspace=current_workspace,
                                                     fragment=fragment, where_project=where_project)
        except DeploifaiAPIError:
            click.secho(
                f"Project \"{project}\" cannot be found in workspace \"{current_workspace}\"",
                fg="red",
            )
            return
        if len(projects_data) == 0:
            click.secho(
                f"Project \"{project}\" cannot be found in workspace \"{current_workspace}\"",
                fg="red",
            )
            return
        variables = {"projects": {"every": {"id": {"equals": project}}}}

    elif "id" in context.local_config["PROJECT"]:
        project_id = context.local_config["PROJECT"]["id"]
        variables = {"projects": {"every": {"id": {"equals": project_id}}}}

    else:
        variables = None

    data_storage_info = context.api.get_data_storages(current_workspace, variables)

    if len(data_storage_info) == 0:
        click.secho("No Datasets Exist", fg="yellow")
        return

    click.echo("Data Storages:")
    for info in data_storage_info:
        click.echo(f"{info['name']} - {info['status']}")
    return
