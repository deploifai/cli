import click

from deploifai.context import pass_deploifai_context_obj, DeploifaiContextObj
from deploifai.utilities import local_config
from deploifai.api import DeploifaiAPI


@click.command()
@pass_deploifai_context_obj
@click.argument("name")
def create(context: DeploifaiContextObj, name: str):
    """
    Create a new project
    """
    if not context.is_authenticated():
        click.echo("Login using deploifai login first")
        raise click.Abort()

    deploifai_api = DeploifaiAPI(context=context)

    project_id = deploifai_api.create_project(name)

    local_config.set_project_config(project_id, context.local_config)
