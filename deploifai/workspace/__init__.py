import click

from .list import list
from .set import set

@click.group()
def workspace():
    """
    Manage, and browse available workspaces
    """
    pass

workspace.add_command(list)
workspace.add_command(set)