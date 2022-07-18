import click

from .create import create
from .list import list_profile


@click.group()
def cloud_profile():
    """
    Manage user's cloud profiles
    """


cloud_profile.add_command(create)
cloud_profile.add_command(list_profile)
