import click

from deploifai.api import DeploifaiAPIError
from deploifai.context import pass_deploifai_context_obj, DeploifaiContextObj, is_authenticated, project_found


@click.command("list")
@click.option("--project", "-p", help="Project Name")
@pass_deploifai_context_obj
@is_authenticated
def list_server(context: DeploifaiContextObj, project: str):
    """
        Command to list out all training servers in current workspace
    """

    current_workspace = context.global_config["WORKSPACE"]["username"]

    click.echo("Workspace Name: {}".format(current_workspace))

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
        variables = {"project": {"is": {"name": {"equals": project}}}}

    elif "id" in context.local_config["PROJECT"]:
        project_id = context.local_config["PROJECT"]["id"]
        variables = {"project": {"is": {"id": {"equals": project_id}}}}

    else:
        variables = None

    server_info = context.api.get_training_server(current_workspace, variables)

    if len(server_info) == 0:
        click.secho("No Training Servers Exist", fg="yellow")
        return

    click.echo("Training Server List:")
    for info in server_info:
        click.echo(f"{info['name']} - {info['status']}")
    return
