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
import os


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

    project_names = [project["name"] for project in projects]
    user_pwd_dir_names = os.listdir()

    is_valid_name = True

    err_msg = ""

    if name in user_pwd_dir_names:
        is_valid_name = False
        err_msg = f"There are existing files/directories in your computer also named {name}"
    elif name in project_names:
        is_valid_name = False
        err_msg = f"Project name taken. Existing names in chosen workspace: {' '.join(project_names)}."
    elif not name.isalnum():
        is_valid_name = False
        err_msg = "Project name should only contain alphanumeric characters."

    if not is_valid_name:
        click.secho(err_msg, fg="red")
        raise click.Abort()

    try:
        cloud_profiles = deploifai_api.get_cloud_profiles(workspace=command_workspace)
    except DeploifaiAPIError:
        click.echo("Could not fetch cloud profiles. Please try again.")
        return

    if not cloud_profiles:
        click.secho("No cloud profiles found. To create a cloud profile: deploifai cloud-profile create", fg="yellow")
        raise click.Abort()

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

    # create proejct in the backend
    try:
        project_fragment = """
                fragment project on Project {
                    id
                }
        """
        project_id = deploifai_api.create_project(name, cloud_profile, project_fragment)["id"]
    except DeploifaiAPIError as err:
        click.secho(err, fg="red")
        raise click.Abort()

    click.secho(f"Successfully created new project named {name}.", fg="green")

    # create a project directory locally, along with .deploifai directory within this project
    try:
        os.mkdir(name)
    except OSError:
        click.secho("An error occured when creating the project locally", fg="red")
        raise click.Abort()

    click.secho(f"A new directory named {name} has been created locally.", fg="green")

    project_path = os.path.join(os.getcwd(), name)
    local_config.create_config_files(project_path)

    context.local_config = local_config.read_config_file()
    # set id in local config file
    local_config.set_project_config(project_id, context.local_config)
