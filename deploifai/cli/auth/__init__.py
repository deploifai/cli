import click
from .login import login
from .logout import logout
from .status import status


@click.group()
def auth():
    """
    Manage Deploifai's authentication state.
    """
    pass


auth.add_command(login)
auth.add_command(logout)
auth.add_command(status)
