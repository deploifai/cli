import click

from deploifai.context import DeploifaiContextObj, pass_deploifai_context_obj, is_authenticated
from deploifai.utilities.config.local_config import read_config_file
from deploifai.core.data_storage import DataStorage


@click.command()
@pass_deploifai_context_obj
@is_authenticated
def push(context: DeploifaiContextObj):
    """
    Push the dataset to the cloud.
    """

    api = context.api
    # try:
    #     configs = read_config_file()
    # except FileNotFoundError:
    #     return

    datastorage_handler = DataStorage(api, 'id')
    datastorage_handler.push()
