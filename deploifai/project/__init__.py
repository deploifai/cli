import click

from .create import create
from .browse import browse


@click.group()
def project():
    """
    Initialise, manage, and deploy an ML project
    """


project.add_command(create)
project.add_command(browse)
