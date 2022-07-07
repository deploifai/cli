import click

from .create import create


@click.group()
def cloud_profile():
    """
    Manage user's cloud profiles
    """


cloud_profile.add_command(create)
