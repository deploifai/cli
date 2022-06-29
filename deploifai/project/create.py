import click

from deploifai.context import pass_deploifai_context_obj, DeploifaiContextObj
from deploifai.utilities import local_config


@click.command()
@pass_deploifai_context_obj
@click.argument("name")
def create(context: DeploifaiContextObj, name: str):
    """
    Create a new project
    """
    project_id = 'project_id'

    local_config.set_project_config(name, context.local_config)

    click.echo("Created a new project")
