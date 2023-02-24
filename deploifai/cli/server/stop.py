import click

from deploifai.cli.context import pass_deploifai_context_obj, DeploifaiContextObj, is_authenticated, project_found
from deploifai.cli.utilities.server_state import change_state


@click.command()
@pass_deploifai_context_obj
@is_authenticated
@project_found
def stop(context: DeploifaiContextObj):
    """
        Stop a training server
    """

    change_state("stop")
