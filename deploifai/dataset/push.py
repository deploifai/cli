from pathlib import Path

import click

from deploifai.clouds.utilities.data_storage.handler import DataStorageHandlerEmptyFilesException, \
    DataStorageHandlerTargetNotFoundException
from deploifai.context import DeploifaiContextObj, pass_deploifai_context_obj, is_authenticated, dataset_found
from deploifai.core.data_storage import DataStorage


@click.command()
@click.option("--target", "-t", help="Target file or directory relative to dataset root", type=str)
@pass_deploifai_context_obj
@is_authenticated
@dataset_found
def push(context: DeploifaiContextObj, target: str = None):
    """
    Uploads files from local to the cloud.
    """

    api = context.api
    dataset_id = context.dataset_config["DATASET"]["id"]

    datastorage_handler = DataStorage(api, dataset_id)

    # find the absolute path to the target directory
    cwd = Path.cwd()
    target_abs = cwd if target is None else cwd.joinpath(target)

    try:
        datastorage_handler.push(target_abs)
    except DataStorageHandlerEmptyFilesException:
        click.secho("No files to pull", fg='yellow')
