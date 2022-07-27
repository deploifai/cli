import click

from deploifai.context import DeploifaiContextObj, pass_deploifai_context_obj, is_authenticated, dataset_found
from deploifai.utilities.config.dataset_config import read_config_file
from deploifai.core.data_storage import DataStorage


@click.command()
@pass_deploifai_context_obj
@is_authenticated
@dataset_found
def push(context: DeploifaiContextObj):
    """
    Push the dataset to the cloud.
    """

    api = context.api
    dataset_id = context.dataset_config["DATASET"]["id"]

    datastorage_handler = DataStorage(api, dataset_id)
    datastorage_handler.push()
