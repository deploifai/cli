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
from deploifai.utilities.user import parse_user_profiles
from time import sleep


@click.command()
@click.option(
    "--create-new",
    prompt="Create a new data storage on Deploifai?",
    type=bool,
    default=False,
)
@click.option("--workspace", help="Workspace name", type=str)
@pass_deploifai_context_obj
@is_authenticated
def init(context: DeploifaiContextObj, create_new, workspace):
    """
    Initialise the current directory as a dataset
    """
    if create_new:
        click.secho(
            "Creating a new data storage. Select the configurations for your new data storage.",
            fg="blue",
        )
    else:
        click.secho("Connecting with an existing data storage", fg="blue")
    storage_id = None
    container_name = None
    command_workspace = None
    deploifai_api = context.api

    user_data = deploifai_api.get_user()
    personal_workspace, team_workspaces = parse_user_profiles(user_data)

    workspaces_from_api = [personal_workspace] + team_workspaces

    # We need to check if the workspace was passed in. Also, we need to make sure that it is a part of the list of
    # workspaces that this user has access to. Otherwise, we need to ask the user to give a valid workspace to use for
    # this command.
    if workspace and len(workspace):
        if any(ws["username"] == workspace for ws in workspaces_from_api):
            for w in workspaces_from_api:
                if w["username"] == workspace:
                    command_workspace = w
                    break
        else:
            # the workspace user input does not match with any of the workspaces the user has access to
            click.secho(
                "{workspace} cannot be found. Please put in a workspace you have access to.".format(
                    workspace=workspace
                ),
                fg="red",
            )
            raise Abort()
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
            raise Abort()
        command_workspace = _choose_workspace["workspace"]

    if create_new:
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
        container_names = new_storage_answers["container_name_input"].split(" ")
        cloud_profile = new_storage_answers["cloud_profile"]
        create_storage_response = deploifai_api.create_data_storage(
            storage_name, container_names, cloud_profile
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
        container_name = prompt(
            {
                "type": "list",
                "name": "container",
                "message": "Choose the container to connect this folder to.",
                "choices": lambda ans: deploifai_api.get_containers(
                    create_storage_response["id"]
                ),
            }
        )["container"]

        if container_name == {}:
            raise Abort()

        storage_id = create_storage_response["id"]
    else:
        try:
            with click_spinner.spinner():
                click.echo("Getting workspace information")
                data_storages = deploifai_api.get_data_storages(
                    workspace=command_workspace
                )
            if not len(data_storages):
                click.echo("No data storages in the workspace")
                raise Abort()
            questions = [
                {
                    "type": "list",
                    "name": "storage_option",
                    "message": "Choose the dataset storage to link.",
                    "choices": [
                        {
                            "name": "{}({})".format(
                                x["name"], x["account"]["username"]
                            ),
                            "value": x["id"],
                        }
                        for x in data_storages
                    ],
                }
            ]
            answers = prompt(questions=questions)
            if answers == {}:
                raise Abort()
            storage_id = answers.get("storage_option", "")
        except DeploifaiAPIError as err:
            click.echo(err)
            raise Abort()

    try:
        os.mkdir("data")
        click.echo(
            "Creating the data directory. If your data is outside the data directory, move it into the the data "
            "directory so that it can be uploaded"
        )
    except FileExistsError as err:
        click.echo("Using the existing data directory")

    try:
        add_data_storage_config(storage_id)
    except DeploifaiDataAlreadyInitialisedError:
        click.echo(
            """
    A different storage is already initialised in the folder.
    Consider removing it from the config file.
    """
        )
        raise Abort()
