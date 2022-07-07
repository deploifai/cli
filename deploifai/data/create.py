import os
import click
import click_spinner
from PyInquirer import prompt
from click import Abort

from deploifai.api import DeploifaiAPIError
from deploifai.context import (
    pass_deploifai_context_obj,
    DeploifaiContextObj,
    is_authenticated,
)
from deploifai.utilities.local_config import (
    add_data_storage_config,
    DeploifaiDataAlreadyInitialisedError,
)
from time import sleep


@click.command()
@pass_deploifai_context_obj
@is_authenticated
def create(context: DeploifaiContextObj):
    """
    Creating a new data storage
    """

    deploifai_api = context.api
    # assume that the user should be in a project directory, that contains local configuration file
    if "id" in context.local_config["PROJECT"]:
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
        project_name = project_data["name"]
        command_workspace = project_data["account"]["username"]
        click.secho("Workspace:{}\n".format(command_workspace), fg='green')
        click.secho("Project:{}<{}>\n".format(project_name,project_id), fg='green')

    else:
        click.secho("Could not find a project in the current directory", fg='yellow')
        return

    try:
        cloud_profiles = deploifai_api.get_cloud_profiles(
            workspace=command_workspace
        )
    except DeploifaiAPIError as err:
        click.echo("Could not fetch cloud profiles. Please try again.")
        return
    new_storage_questions = [
        {
            "type": "input",
            "name": "storage_name_input",
            "message": "Name the data storage",
        },
        {
            "type": "input",
            "name": "container_name_input",
            "message": "Input container partition names (space separated: ex: first second-name third)",
        },
        {
            "type": "list",
            "name": "cloud_profile",
            "message": "Choose a cloud profile for data storage",
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
            "when": lambda ans: ans.get("storage_option") != "New",
        },
    ]
    new_storage_answers = prompt(questions=new_storage_questions)
    if new_storage_answers == {}:
        raise Abort()
    storage_name = new_storage_answers["storage_name_input"]
    cloud_profile = new_storage_answers["cloud_profile"]

    click.secho("Cloud Profile:{}".format(cloud_profile), fg='green')
    click.secho("Dataset Name:{}".format(storage_name), fg='green')

    click.secho("Creating a new data storage.", fg="blue")

    create_storage_response = deploifai_api.create_data_storage(
        storage_name, cloud_profile
    )

    with click_spinner.spinner():
        click.echo("Deploying data storage")
        while True:
            data_storage_info = deploifai_api.get_data_storage_info(
                create_storage_response["id"]
            )
            if data_storage_info["status"] == "DEPLOY_SUCCESS":
                click.echo("Deployment success!")
                break
            elif data_storage_info["status"] == "DEPLOY_ERROR":
                click.echo("There was an error in deployment.")
                break
            sleep(10)
