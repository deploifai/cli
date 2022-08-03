import click

from deploifai.context import DeploifaiContextObj, pass_deploifai_context_obj, is_authenticated, dataset_found
from deploifai.core.data_storage import DataStorage


@click.command()
@pass_deploifai_context_obj
@is_authenticated
@dataset_found
def pull(context: DeploifaiContextObj):
    """
    Download the dataset from the cloud to the current directory
    """

    api = context.api
    dataset_id = context.dataset_config["DATASET"]["id"]

    datastorage_handler = DataStorage(api, dataset_id)
    datastorage_handler.pull()
