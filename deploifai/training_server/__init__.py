import click
from deploifai.training_server.create import create


@click.group()
def training_server():
    """
    Manage datasets and data storages on Deploifai
    """
    pass


training_server.add_command(create)
