import click

from deploifai.context import DeploifaiContextObj, pass_deploifai_context_obj
from deploifai.utilities.local_config import read_config_file
from deploifai.core.data_storage import DataStorage


@click.command()
@pass_deploifai_context_obj
def push(context: DeploifaiContextObj):
    api = context.api
    try:
        configs = read_config_file()
    except FileNotFoundError:
        return

    datastorage_handler = DataStorage(context=context, config=configs, api=api)
    datastorage_handler.push()
