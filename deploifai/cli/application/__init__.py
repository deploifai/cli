import click

from .init import init


@click.group()
def application():
    """
    Initialise, and manage an ML application deployment
    """


application.add_command(init)
