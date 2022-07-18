import click

from deploifai.context import pass_deploifai_context_obj, DeploifaiContextObj, is_authenticated, project_found


@click.command("list")
@pass_deploifai_context_obj
@is_authenticated
def list_server(context: DeploifaiContextObj):
    """
        Command to list out all training servers in current workspace
    """

    current_workspace = context.global_config["WORKSPACE"]["username"]

    click.echo("Workspace Name: {}".format(current_workspace))

    server_info = context.api.get_server(current_workspace)

    click.echo("Training Server List:")
    for info in server_info:
        click.echo(f"{info['name']} - {info['status']}")
