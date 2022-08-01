import click

from .create import create
from .list import list_server
from .start import start
from .stop import stop


@click.group()
def server():
    """
    Manage training servers on Deploifai
    """
    pass


server.add_command(create)
server.add_command(list_server)
server.add_command(start)
server.add_command(stop)
