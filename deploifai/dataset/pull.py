from pathlib import Path

import click

from deploifai.clouds.utilities.data_storage.handler import DataStorageHandlerEmptyFilesException, \
    DataStorageHandlerTargetNotFoundException
from deploifai.context import DeploifaiContextObj, pass_deploifai_context_obj, is_authenticated, dataset_found
from deploifai.core.data_storage import DataStorage


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
    if len(data) == 0:
        click.secho("No dataset information extracted", fg="yellow")
        click.secho("Please run deploifai dataset init again")
        raise click.Abort()

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
