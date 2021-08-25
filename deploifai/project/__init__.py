import click

from .init import init


@click.group()
def project():
    """
    Initialise, manage, and deploy an ML project
    """


project.add_command(init)
