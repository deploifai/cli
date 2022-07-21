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
def init(context: DeploifaiContextObj):
    """
    Initialise the current directory as a dataset
    """
    click.secho("Connecting with an existing dataset", fg="blue")
    deploifai_api = context.api

    # assume that the user should be in a project directory, that contains local configuration file
    if "id" in context.local_config["PROJECT"]:
        project_id = context.local_config["PROJECT"]["id"]

        # query for workspace name from api
        fragment = """
                        fragment project on Project {
                            account{
                                username
                            }
                        }
                        """
        context.debug_msg(project_id)
        project_data = context.api.get_project(
            project_id=project_id, fragment=fragment
        )
        command_workspace = project_data["account"]["username"]
    else:
        click.secho("Could not find a project in the current directory", fg='yellow')
        return

    try:
        with click_spinner.spinner():
            click.echo("Getting workspace information")
            data_storages = deploifai_api.get_data_storages(
                workspace=command_workspace
            )
        if not len(data_storages):
            click.echo("No dataset in the workspace")
            raise Abort()
        questions = [
            {
                "type": "list",
                "name": "storage_option",
                "message": "Choose the dataset to link.",
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
        os.mkdir("dataset")
        click.echo(
            "Creating the dataset directory. If your dataset is outside the dataset directory, move it into the the dataset "
            "directory so that it can be uploaded"
        )
    except FileExistsError as err:
        click.echo("Using the existing dataset directory")

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
