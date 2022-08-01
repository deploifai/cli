import click

from .create import create
from .browse import browse
from .list import list_project
from .init import init
from .info import info


@click.group()
def project():
    """
    Initialise, manage, and deploy an ML project
    """


project.add_command(create)
project.add_command(browse)
project.add_command(list_project)
project.add_command(init)
project.add_command(info)
