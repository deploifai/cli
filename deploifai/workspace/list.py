import click
from deploifai.context import (
    pass_deploifai_context_obj,
    DeploifaiContextObj,
    is_authenticated,
)
from deploifai.utilities.user import parse_user_profiles


@click.command()
@pass_deploifai_context_obj
@is_authenticated
def list(context: DeploifaiContextObj):
    """
    Lists out all available workspaces
    """
    deploifai_api = context.api

    user_data = deploifai_api.get_user()
    personal_workspace, team_workspaces = parse_user_profiles(user_data)

    workspaces_from_api = [personal_workspace] + team_workspaces

    current_workspace = context.global_config["AUTH"]["username"]

    click.secho("All accessible workspaces:", fg="blue")

    for workspace in workspaces_from_api:
        workspace_type = "TEAM" if workspace["isTeam"] else "PERSONAL"
        is_current_workspace = " (Current Workspace)" if workspace["username"] == current_workspace else ""

        click.echo(f"{workspace['username']} - {workspace_type}{is_current_workspace}")