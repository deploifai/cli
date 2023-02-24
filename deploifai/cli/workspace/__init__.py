import click

from .list import list_workspace
from .set import set_workspace


@click.group()
def workspace():
    """
    Manage, and browse available workspaces
    """
    pass


workspace.add_command(list_workspace)
workspace.add_command(set_workspace)
