import click

from .create import create
from .list import list_server


@click.group()
def training_server():
    """
    Manage datasets and data storages on Deploifai
    """
    pass


training_server.add_command(create)
training_server.add_command(list_server)
