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
from deploifai.utilities.config import dataset_config


@click.command()
@pass_deploifai_context_obj
@is_authenticated
def init(context: DeploifaiContextObj):
    """
    Initialise the current directory as a dataset
    """
    click.secho("Connecting with an existing dataset", fg="blue")
    deploifai_api = context.api

    command_workspace = context.global_config["WORKSPACE"]["username"]

    try:
        with click_spinner.spinner():
            click.echo("Getting dataset information")
            data_storages = deploifai_api.get_data_storages(
                workspace=command_workspace
            )
        if not len(data_storages):
            click.echo("No dataset in the workspace")
            raise click.Abort()
        questions = [
            {
                "type": "list",
                "name": "storage_option",
                "message": "Choose the dataset to link.",
                "choices": [
                    {
                        "name": "{} <{}>".format(
                            x["name"], x["cloudProfile"]["provider"]
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
        storage_id = answers["storage_option"]

        context.debug_msg(storage_id)
    except DeploifaiAPIError as err:
        click.echo(err)
        raise Abort()

    try:
        dataset_config.create_config_files()
        context.dataset_config = dataset_config.read_config_file()
        context.debug_msg(context.dataset_config)
        click.echo(
            "Creating the dataset config file. If your dataset is outside the current working directory, "
            "move it into the the current working directory so that it can be uploaded."
        )
    except FileExistsError as err:
        click.echo("Using the existing dataset directory")

    try:
        dataset_config.add_data_storage_config(storage_id, context.dataset_config)
    except dataset_config.DeploifaiDataAlreadyInitialisedError:
        click.echo(
            """
    A different dataset is already initialised in the config file.
    Consider removing it from the config file, or removing the config file itself.
    """
        )
        raise Abort()
