import click
import os

from deploifai.context import (
    pass_deploifai_context_obj,
    DeploifaiContextObj,
    is_authenticated,
)
from deploifai.utilities.config import local_config
from deploifai.api import DeploifaiAPIError
from PyInquirer import prompt
import os


@click.command()
@click.argument("name")
@pass_deploifai_context_obj
@is_authenticated
def create(context: DeploifaiContextObj, name: str):
    """
    Create a new project
    """
    deploifai_api = context.api

    command_workspace = context.global_config["WORKSPACE"]["username"]

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

    # check to see if the .deploifai directory already exists

    if os.path.isdir(".deploifai"):
        click.echo("Project directory already exists, create project in a different directory")
        raise click.Abort()

    # extract and use the cloud profile information
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

    # create project in the backend
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

    # storing the project information in the local.cfg file
    local_config.create_config_files()
    context.local_config = local_config.read_config_file()
    # set id in local config file
    local_config.set_project_config(project_id, context.local_config)
