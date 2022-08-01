import click
from PyInquirer import prompt

from deploifai.api import DeploifaiAPIError
from deploifai.context import pass_deploifai_context_obj, DeploifaiContextObj, is_authenticated, project_found
from deploifai.utilities.server_state import change_state


@click.command()
@pass_deploifai_context_obj
@is_authenticated
@project_found
def start(context: DeploifaiContextObj):
    """
        Start a training server
    """

    change_state("start")
