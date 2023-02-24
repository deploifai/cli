from pathlib import Path

import click

from deploifai.cli.clouds.utilities.data_storage.handler import DataStorageHandlerEmptyFilesException
from deploifai.cli.context import DeploifaiContextObj, pass_deploifai_context_obj, is_authenticated, dataset_found
from deploifai.cli.core.data_storage import DataStorage


@click.command()
@click.argument("target", required=False)
@pass_deploifai_context_obj
@is_authenticated
@dataset_found
def pull(context: DeploifaiContextObj, target: str = None):
    """
    Download files from the cloud to local.
    """

    api = context.api
    dataset_id = context.dataset_config["DATASET"]["id"]

    data = context.api.get_data_storage_info(dataset_id)

    click.secho("Dataset Name: {}".format(data["name"]), fg="blue")
    click.secho("Cloud Provider: {}".format(data["cloudProviderYodaConfig"]["provider"]), fg="blue")

    datastorage_handler = DataStorage(api, dataset_id)

    # find the absolute path to the target directory
    cwd = Path.cwd()
    target_abs = cwd if target is None else cwd.joinpath(target)

    try:
        datastorage_handler.pull(target_abs)
    except DataStorageHandlerEmptyFilesException:
        click.secho("No files to pull", fg='yellow')
