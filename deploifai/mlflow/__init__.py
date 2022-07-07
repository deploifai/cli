import click

from .get_setup import get_setup


@click.group()
def mlflow():
    """
    Initialise, manage, and deploy an ML project
    """


mlflow.add_command(get_setup)