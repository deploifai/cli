import click

from .get_setup import get_setup


@click.group()
def mlflow():
    """
    Set-up and manage the ML FLow Integration
    """


mlflow.add_command(get_setup)