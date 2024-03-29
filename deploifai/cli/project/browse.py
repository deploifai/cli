import click
import webbrowser
import requests

from deploifai.cli.api import DeploifaiAPIError
from deploifai.cli.context import (
    pass_deploifai_context_obj,
    DeploifaiContextObj,
    project_found,
)
from deploifai.cli.utilities.frontend_routing import get_project_route


@click.command()
@pass_deploifai_context_obj
@project_found
@click.option("--workspace", '-w', help="Workspace name", type=str)
@click.option("--project", '-p', help="Project name", type=str)
def browse(context: DeploifaiContextObj, project: str, workspace="unassigned"):
    """
    Command to open a project in the Web Browser
    """

    if workspace:
        if project:
            # query for list of projects to obtain project id
            fragment = """
                            fragment project on Project {
                                id 
                            }
                            """
            where_project = {"name": {"equals": project}}
            try:
                projects_data = context.api.get_projects(workspace=workspace,
                                                         fragment=fragment, where_project=where_project)
            except DeploifaiAPIError:
                click.secho(
                    f"Project \"{project}\" cannot be found in workspace \"{workspace}\"",
                    fg="red",
                )
                return
            if len(projects_data) == 0:
                click.secho(
                    f"Project \"{project}\" cannot be found in workspace \"{workspace}\"",
                    fg="red",
                )
                return
            else:
                project_id = projects_data[0]["id"]

        else:
            click.secho("Missing project name", fg="yellow")
            click.secho("use --project option to pass the name of the project", fg="yellow")
            return

    elif project:
        click.secho("Missing workspace name", fg="yellow")
        click.secho("Use --workspace option to pass the name of the workspace", fg="yellow")
        return

    else:
        # assume that the user should be in a project directory, that contains local configuration file

        if "id" not in context.local_config["PROJECT"]:
            click.secho("Missing workspace name and project name", fg='yellow')
            click.secho("Use --workspace option to pass the name of the workspace, and --project option to pass the "
                        "name of the project", fg="yellow")
            return

        else:
            project_id = context.local_config["PROJECT"]["id"]

            # query for workspace name from api
            fragment = """
                            fragment project on Project {
                                name
                                account{
                                    username
                                }
                            }
                            """
            context.debug_msg(project_id)
            project_data = context.api.get_project(
                project_id=project_id, fragment=fragment
            )
            project = project_data["name"]
            workspace = project_data["account"]["username"]

    # defining the url
    url = get_project_route(workspace, project)
    context.debug_msg(f"Opening url: {url}")
    # checking if the url leads to a valid webpage
    response = requests.head(url)
    if response.status_code == 200:
        # opening the url in default browser
        webbrowser.open(url, new=2)
    else:
        click.secho("Invalid workspace or project name", fg='red')
