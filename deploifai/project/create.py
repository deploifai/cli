import click

from deploifai.context import (
    pass_deploifai_context_obj,
    DeploifaiContextObj,
    is_authenticated,
)
from deploifai.utilities import local_config
from deploifai.api import DeploifaiAPIError
from deploifai.utilities.user import parse_user_profiles
from PyInquirer import prompt


@click.command()
@click.argument("name")
@click.option("--workspace", help="Workspace name", type=str)
@pass_deploifai_context_obj
@is_authenticated
def create(context: DeploifaiContextObj, name: str, workspace):
    """
    Create a new project
    """
    deploifai_api = context.api

    user_data = deploifai_api.get_user()
    personal_workspace, team_workspaces = parse_user_profiles(user_data)

    workspaces_from_api = [personal_workspace] + team_workspaces

    # checking validity of workspace, and prompting workspaces choices if not specified
    if workspace and len(workspace):
        if any(ws["username"] == workspace for ws in workspaces_from_api):
            for w in workspaces_from_api:
                if w["username"] == workspace:
                    command_workspace = w
                    break
        else:
            # the workspace user input does not match with any of the workspaces the user has access to
            click.secho(
                f"{workspace} cannot be found. Please put in a workspace you have access to.",
                fg="red",
            )
            raise click.Abort()
    else:
        _choose_workspace = prompt(
            {
                "type": "list",
                "name": "workspace",
                "message": "Choose a workspace",
                "choices": [
                    {"name": ws["username"], "value": ws} for ws in workspaces_from_api
                ],
            }
        )
        if _choose_workspace == {}:
            raise click.Abort()
        command_workspace = _choose_workspace["workspace"]

    # ensure project name is unique to the chosen workspace
    try:
        fragment = """
                fragment project on Project {
                    id name 
                }
                """
        projects = deploifai_api.get_projects(command_workspace, fragment)
    except DeploifaiAPIError as err:
        click.echo("An error occurred when fetching projects. Please try again.")
        return

    err_msg = "Project name taken. Choose a unique project name:"

    project_names = [project["name"] for project in projects]

    name_taken_err_msg = f"Project name taken. Existing names in chosen workspace: {' '.join(project_names)}\nChoose a unique project name:"
    err_msg = name_taken_err_msg

    is_valid_name = not (name in project_names)

    while not is_valid_name:
        prompt_name = prompt(
            {
                "type": "input",
                "name": "project_name",
                "message": err_msg,
            }
        )

        new_project_name = prompt_name["project_name"]

        if len(new_project_name) == 0:
            err_msg = "Project name cannot be empty.\nChoose a non-empty project name:"
        elif not new_project_name.isalnum():
            err_msg = f"Project name should only contain alphanumeric characters.\nChoose a valid project name:"
        elif new_project_name in project_names:
            err_msg = name_taken_err_msg
        else:
            name = new_project_name
            is_valid_name = True

    try:
        cloud_profiles = deploifai_api.get_cloud_profiles(workspace=command_workspace)
    except DeploifaiAPIError as err:
        click.echo("Could not fetch cloud profiles. Please try again.")
        return

    # TODO: prompt user if no existing cloud profiles exist
    choose_cloud_profile = prompt(
        {
            "type": "list",
            "name": "cloud_profile",
            "message": "Choose a cloud profile for project",
            "choices": [
                {
                    "name": "{name}({workspace}) - {provider}".format(
                        name=cloud_profile.name,
                        workspace=cloud_profile.workspace,
                        provider=cloud_profile.provider,
                    ),
                    "value": cloud_profile,
                }
                for cloud_profile in cloud_profiles
            ],
        }
    )

    cloud_profile = choose_cloud_profile["cloud_profile"]

    try:
        project_id = deploifai_api.create_project(name, cloud_profile)["id"]
    except DeploifaiAPIError as err:
        click.echo("Could not create project. Please try again.")
        return

    click.secho(f"Successfully created new project named {name}.", fg="green")

    local_config.set_project_config(project_id, context.local_config)
