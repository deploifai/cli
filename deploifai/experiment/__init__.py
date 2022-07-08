import click

from .create import create


@click.group()
def experiment():
    """
    Manage experiments on an ML project
    """


experiment.add_command(create)
