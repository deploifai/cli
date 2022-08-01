import click

from deploifai.api import DeploifaiAPIError
from deploifai.context import pass_deploifai_context_obj, DeploifaiContextObj, is_authenticated, project_found


@click.command("list")
@click.option("--project", "-p", help="Project Name")
@pass_deploifai_context_obj
@is_authenticated
def list_server(context: DeploifaiContextObj, project: str):
    """
    List all training servers in current workspace
    """

    current_workspace = context.global_config["WORKSPACE"]["username"]

    click.secho("Workspace Name: {}".format(current_workspace), fg="blue")

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
        click.secho("Project Name: {}".format(project), fg="blue")
        project_id = projects_data[0]["id"]
        where_training = {"project": {"is": {"id": {"equals": project_id}}}}

    elif context.local_config and "id" in context.local_config["PROJECT"]:
        project_id = context.local_config["PROJECT"]["id"]
        # query for workspace name from api
        fragment = """
                        fragment project on Project {
                            name
                        }
                        """
        context.debug_msg(project_id)
        project_data = context.api.get_project(
            project_id=project_id, fragment=fragment
        )
        project = project_data["name"]
        click.secho("Project Name: {}".format(project), fg="blue")
        where_training = {"project": {"is": {"id": {"equals": project_id}}}}

    else:
        where_training = None

    server_info = context.api.get_training_servers(current_workspace, where_training)

    if len(server_info) == 0:
        click.secho("No training servers exist", fg="yellow")
        return

    click.secho("All training servers:", fg="blue")
    for info in server_info:
        click.echo(f"{info['name']} <{info['status']}> - {info['state']}")
    return
