import click
from deploifai.context import (
    pass_deploifai_context_obj,
    DeploifaiContextObj,
    is_authenticated,
)
from deploifai.utilities.user import parse_user_profiles


@click.command('list')
@pass_deploifai_context_obj
@is_authenticated
def list_workspace(context: DeploifaiContextObj):
    """
    Lists out all available workspaces
    """
    deploifai_api = context.api

    user_data = deploifai_api.get_user()
    personal_workspace, team_workspaces = parse_user_profiles(user_data)

    workspaces_from_api = [personal_workspace] + team_workspaces

    current_workspace = context.global_config["WORKSPACE"]["username"]

    click.secho("All accessible workspaces:", fg="blue")

    for workspace in workspaces_from_api:
        workspace_type = "TEAM" if workspace["isTeam"] else "PERSONAL"
        context.debug_msg(workspace)
        is_current_workspace = "*" if workspace["username"] == current_workspace else " "

        click.echo(f"{is_current_workspace} {workspace['username']} - {workspace_type}")
    return
