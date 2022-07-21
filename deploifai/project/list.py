import click

from deploifai.api import DeploifaiAPIError
from deploifai.context import (
    pass_deploifai_context_obj,
    DeploifaiContextObj,
    is_authenticated,
)


@click.command("list")
@pass_deploifai_context_obj
@is_authenticated
def list_project(context: DeploifaiContextObj):
    """
    Command to list all projects in the current workspace
    """

    current_workspace = context.global_config["WORKSPACE"]["username"]

    click.secho("Workspace Name: {}".format(current_workspace), fg="blue")

    fragment = """
                    fragment project on Project {
                        id
                        name
                    }
                    """
    projects_data = context.api.get_projects(workspace=current_workspace, fragment=fragment)

    if len(projects_data) == 0:
        click.secho("No projects exist", fg="yellow")
        return

    # If more information is needed change fragment to add it, then change the final echo to provide that info too

    click.secho("All projects:", fg="blue")
    for projects in projects_data:
        click.echo(projects["name"])
    return
