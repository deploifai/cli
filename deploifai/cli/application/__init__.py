import click

from .init import init
from .create import create

@click.group()
def application():
    """
    Initialise, and manage an ML application deployment
    """


application.add_command(init)
application.add_command(create)
