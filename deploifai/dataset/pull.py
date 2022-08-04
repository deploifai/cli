import click

from deploifai.clouds.utilities.data_storage.handler import DataStorageHandlerEmptyFilesException
from deploifai.context import DeploifaiContextObj, pass_deploifai_context_obj, is_authenticated, dataset_found
from deploifai.core.data_storage import DataStorage


@click.command()
@click.option("--target", "-t", help="specify which file, or folder you would like to download", type=str)
@pass_deploifai_context_obj
@is_authenticated
@dataset_found
def pull(context: DeploifaiContextObj, target: str = None):
    """
    Download the dataset from the cloud to the current directory
    """

    api = context.api
    dataset_id = context.dataset_config["DATASET"]["id"]

    datastorage_handler = DataStorage(api, dataset_id)
    try:
        datastorage_handler.pull(target)
    except DataStorageHandlerEmptyFilesException as e:
        click.secho(e, fg='yellow')
