import click

from .create import create
from .list import list_server


@click.group()
def server():
    """
    Manage training servers on Deploifai
    """
    pass


server.add_command(create)
server.add_command(list_server)
