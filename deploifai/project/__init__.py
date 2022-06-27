import click

from .create import create


@click.group()
def project():
    """
    Initialise, manage, and deploy an ML project
    """


project.add_command(create)
